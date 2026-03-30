# ============================================================
#  AI Smart Car Parking System — Configuration
# ============================================================
#  Edit this file to match YOUR setup before uploading to ESP32.
# ============================================================

# ─── WiFi ────────────────────────────────────────────────────
WIFI_SSID     = "XXX"       # ← Change this
WIFI_PASSWORD = "xxx"   # ← Change this

# ─── ESP32-CAM address ───────────────────────────────────────
# The IP address your ESP32-CAM gets on the network.
# Check the Serial Monitor of the ESP32-CAM after it boots.
CAM_HOST = "xxx"   # ← Change to your ESP32-CAM IP
CAM_PORT = 80

# ─── GPIO Pin Assignments (ESP32 DevKit) ─────────────────────
PIN_PIR_ENTRY = 27    # SR602 entry sensor OUT pin
PIN_PIR_EXIT  = 26    # SR602 exit sensor OUT pin
PIN_SERVO     = 13    # Micro servo signal pin

# ─── Servo angles ────────────────────────────────────────────
SERVO_OPEN_ANGLE  = 90    # Barrier open position (degrees)
SERVO_CLOSE_ANGLE = 0     # Barrier closed position (degrees)

# ─── Timing (seconds) ────────────────────────────────────────
GATE_OPEN_DURATION  = 5     # How long the gate stays open
PIR_DEBOUNCE_MS     = 3000  # Minimum ms between PIR triggers
SENSOR_POLL_MS      = 100   # How often to poll sensors (ms)

# ─── Parking capacity ────────────────────────────────────────
MAX_CAPACITY = 10   # Maximum number of cars allowed

# ─── Cloud ANPR API ──────────────────────────────────────────
# Set ANPR_MODE to "simulated" for testing without an API,
# or "gemini" to use Google Gemini API for plate recognition.
ANPR_MODE = "simulated"   # Options: "simulated", "gemini"

# Google Gemini API settings (only used if ANPR_MODE = "gemini")
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"   # ← Get from https://aistudio.google.com/
GEMINI_MODEL   = "gemini-2.0-flash"

# ─── Logging ─────────────────────────────────────────────────
LOG_FILE = "/parking_log.csv"   # Log file path on ESP32 flash
