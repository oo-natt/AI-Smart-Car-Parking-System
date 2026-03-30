/*
 * ============================================================
 *  AI Smart Car Parking System — ESP32-CAM Firmware
 * ============================================================
 *  Board  : AI-Thinker ESP32-CAM
 *  Purpose: Connects to WiFi and serves a JPEG capture endpoint
 *           so the ESP32 DevKit can fetch images over HTTP.
 *
 *  Endpoints:
 *    GET /capture  → returns a JPEG image (Content-Type: image/jpeg)
 *    GET /status   → returns {"status":"ready"} for health checks
 *
 *  Flashing:
 *    1. Connect FTDI: U0R→TX, U0T→RX, GND→GND, 5V→5V
 *    2. Bridge GPIO0 to GND (flash mode)
 *    3. Arduino IDE → Board: "AI Thinker ESP32-CAM"
 *    4. Upload, then remove GPIO0-GND bridge and reset
 * ============================================================
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ─── WiFi credentials ────────────────────────────────────────
const char* ssid     = "xxx";      // ← Change this
const char* password = "xxx";   // ← Change this

// ─── AI-Thinker ESP32-CAM pin mapping ────────────────────────
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ─── Flash LED (built-in on GPIO 4) ─────────────────────────
#define FLASH_LED_PIN      4

// ─── Web server on port 80 ──────────────────────────────────
WebServer server(80);

// ─── Forward declarations ───────────────────────────────────
void handleCapture();
void handleStatus();
void handleNotFound();
bool initCamera();
void connectWiFi();

// =============================================================
//  SETUP
// =============================================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n[SMART PARKING] ESP32-CAM starting...");

  // Flash LED setup
  pinMode(FLASH_LED_PIN, OUTPUT);
  digitalWrite(FLASH_LED_PIN, LOW);

  // Initialize camera
  if (!initCamera()) {
    Serial.println("[ERROR] Camera init failed! Restarting in 5s...");
    delay(5000);
    ESP.restart();
  }
  Serial.println("[OK] Camera initialized");

  // Connect to WiFi
  connectWiFi();

  // Register HTTP routes
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/status",  HTTP_GET, handleStatus);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("[OK] HTTP server started");
  Serial.printf("[OK] Ready at http://%s/capture\n", WiFi.localIP().toString().c_str());
}

// =============================================================
//  LOOP
// =============================================================
void loop() {
  server.handleClient();

  // Reconnect WiFi if disconnected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WARN] WiFi lost, reconnecting...");
    connectWiFi();
  }
}

// =============================================================
//  CAMERA INITIALIZATION
// =============================================================
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Use higher resolution if PSRAM is available
  if (psramFound()) {
    config.frame_size   = FRAMESIZE_VGA;   // 640x480 — good for plate reading
    config.jpeg_quality = 10;              // Lower = better quality (0-63)
    config.fb_count     = 2;
    Serial.println("[INFO] PSRAM found → VGA mode");
  } else {
    config.frame_size   = FRAMESIZE_QVGA;  // 320x240 fallback
    config.jpeg_quality = 12;
    config.fb_count     = 1;
    Serial.println("[INFO] No PSRAM → QVGA mode");
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[ERROR] Camera init error 0x%x\n", err);
    return false;
  }

  // Tune sensor for license plate reading
  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, 1);     // Slightly brighter
    s->set_contrast(s, 1);       // Slightly more contrast
    s->set_saturation(s, 0);     // Neutral saturation
    s->set_whitebal(s, 1);       // Auto white balance ON
    s->set_awb_gain(s, 1);       // AWB gain ON
    s->set_exposure_ctrl(s, 1);  // Auto exposure ON
    s->set_aec2(s, 1);           // AEC DSP ON
    s->set_gain_ctrl(s, 1);      // Auto gain ON
  }

  return true;
}

// =============================================================
//  WiFi CONNECTION
// =============================================================
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.printf("[WIFI] Connecting to %s", ssid);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[WIFI] Connection failed! Will retry in loop...");
  }
}

// =============================================================
//  HTTP HANDLERS
// =============================================================

// GET /capture — Return a JPEG image
void handleCapture() {
  Serial.println("[HTTP] /capture requested");

  // Brief flash for low-light assistance
  digitalWrite(FLASH_LED_PIN, HIGH);
  delay(100);

  camera_fb_t * fb = esp_camera_fb_get();

  digitalWrite(FLASH_LED_PIN, LOW);

  if (!fb) {
    Serial.println("[ERROR] Camera capture failed");
    server.send(500, "application/json", "{\"error\":\"capture failed\"}");
    return;
  }

  // Send JPEG response
  server.sendHeader("Content-Disposition", "inline; filename=plate.jpg");
  server.sendHeader("Access-Control-Allow-Origin", "*");

  size_t fb_len = fb->len;  // Save length before returning buffer
  server.send_P(200, "image/jpeg", (const char*)fb->buf, fb_len);

  esp_camera_fb_return(fb);
  Serial.printf("[OK] Sent JPEG (%u bytes)\n", fb_len);
}

// GET /status — Health check
void handleStatus() {
  String json = "{";
  json += "\"status\":\"ready\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"uptime\":" + String(millis() / 1000);
  json += "}";

  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

// 404 handler
void handleNotFound() {
  String msg = "Not Found\n\nAvailable endpoints:\n";
  msg += "  GET /capture  — Capture JPEG image\n";
  msg += "  GET /status   — Health check\n";
  server.send(404, "text/plain", msg);
}
