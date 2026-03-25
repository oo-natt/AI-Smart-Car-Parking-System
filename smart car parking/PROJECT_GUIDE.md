# AI Smart Car Parking System — Complete Project Guide

A university course project for **Embedded Systems & IoT**. Uses an ESP32-CAM to capture vehicle number plates, an ESP32 DevKit as the main microcontroller, two SR602 PIR sensors for entry/exit detection, and a micro servo as a barrier gate.

---

## Table of Contents

1. [Bill of Materials](#bill-of-materials)
2. [System Architecture](#system-architecture)
3. [Wiring Guide](#wiring-guide)
4. [Software Setup](#software-setup)
5. [Flashing the ESP32-CAM](#flashing-the-esp32-cam)
6. [Flashing the ESP32 DevKit](#flashing-the-esp32-devkit)
7. [Configuration](#configuration)
8. [Testing Guide](#testing-guide)
9. [System Flow](#system-flow)
10. [Troubleshooting](#troubleshooting)
11. [Optional Improvements](#optional-improvements)

---

## Bill of Materials

| # | Component | Qty | Notes |
|---|-----------|-----|-------|
| 1 | ESP32 DevKit V1 (30-pin or 38-pin) | 1 | Main microcontroller, runs MicroPython |
| 2 | ESP32-CAM (AI-Thinker) | 1 | Camera module for plate capture |
| 3 | SR602 PIR Motion Sensor | 2 | One for entry, one for exit |
| 4 | SG90 Micro Servo | 1 | Barrier gate actuator |
| 5 | USB-to-TTL Serial Adapter (FTDI) | 1 | For flashing the ESP32-CAM |
| 6 | Breadboard (full or half size) | 1–2 | For prototyping |
| 7 | Jumper Wires (M-M, M-F) | ~20 | Various connections |
| 8 | Micro USB Cables | 2 | One per board |
| 9 | 5V Power Supply (optional) | 1 | If USB power is insufficient for servo |

---

## System Architecture

```
 ┌─────────────────────────────────────────────────────────────┐
 │                      WiFi Network                          │
 │                                                             │
 │   ┌──────────────┐         HTTP         ┌───────────────┐  │
 │   │  ESP32-CAM   │◄───────────────────►│ ESP32 DevKit  │  │
 │   │  (Arduino)   │   GET /capture       │ (MicroPython) │  │
 │   │              │   returns JPEG       │               │  │
 │   └──────────────┘                      │  ┌─────────┐  │  │
 │                                         │  │ PIR IN  │──┼──┼── SR602 (Entry)
 │   ┌──────────────┐                      │  │ PIR OUT │──┼──┼── SR602 (Exit)
 │   │  Cloud API   │◄──HTTP POST image──►│  │ SERVO   │──┼──┼── SG90 Barrier
 │   │  (Gemini)    │   returns plate text │  └─────────┘  │  │
 │   └──────────────┘                      └───────────────┘  │
 └─────────────────────────────────────────────────────────────┘
```

**Flow**: PIR detects car → DevKit requests image from ESP32-CAM → Image sent to Gemini API → Plate logged → Servo opens gate → Car passes → Servo closes gate.

---

## Wiring Guide

### ESP32 DevKit Connections

| Component | Component Pin | ESP32 DevKit Pin | Wire Color (suggested) |
|-----------|--------------|------------------|----------------------|
| SR602 (Entry) | VCC | 3.3V | Red |
| SR602 (Entry) | GND | GND | Black |
| SR602 (Entry) | OUT | GPIO 27 | Yellow |
| SR602 (Exit) | VCC | 3.3V | Red |
| SR602 (Exit) | GND | GND | Black |
| SR602 (Exit) | OUT | GPIO 26 | Orange |
| SG90 Servo | VCC (Red) | 5V (VIN) | Red |
| SG90 Servo | GND (Brown) | GND | Brown/Black |
| SG90 Servo | Signal (Orange) | GPIO 13 | Orange |

> **Important**: The servo should be powered from the **5V / VIN** pin (or external 5V supply), NOT 3.3V. The SR602 sensors can use 3.3V.

### ESP32-CAM Connections (for flashing via FTDI)

| FTDI Adapter | ESP32-CAM |
|-------------|-----------|
| 5V | 5V |
| GND | GND |
| TX | U0R (GPIO 3) |
| RX | U0T (GPIO 1) |
| — | GPIO 0 → GND (**during flash only**) |

> After flashing, **remove** the GPIO 0 → GND bridge and press the RST button on the ESP32-CAM.

### SR602 PIR Sensor Pin Identification

```
    ┌──────────┐
    │  SR602   │
    │  ┌───┐  │
    │  │   │  │
    │  │PIR│  │
    │  │   │  │
    │  └───┘  │
    │          │
    └─┤ ┤ ┤───┘
      1  2  3

  1 = OUT (Signal)
  2 = GND
  3 = VCC (3.3V–9V)
```

> **Note**: Pin numbering may vary by manufacturer — check your specific module's markings.

### SG90 Servo Wire Colors

| Wire Color | Function |
|-----------|----------|
| Red | VCC (5V) |
| Brown/Black | GND |
| Orange/Yellow | PWM Signal |

---

## Software Setup

### For the ESP32-CAM (Arduino IDE)

1. **Install Arduino IDE** (2.x recommended): https://www.arduino.cc/en/software
2. **Add ESP32 board support**:
   - Go to **File → Preferences**
   - In "Additional Board Manager URLs", add:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to **Tools → Board → Boards Manager**
   - Search "esp32" and install **"ESP32 by Espressif Systems"**
3. **Select board**: Tools → Board → **AI Thinker ESP32-CAM**
4. **Select port**: Tools → Port → *(your FTDI COM port)*

### For the ESP32 DevKit (MicroPython + Thonny)

1. **Download MicroPython firmware** for ESP32:
   - Go to https://micropython.org/download/ESP32_GENERIC/
   - Download the latest `.bin` file
2. **Install Thonny IDE**: https://thonny.org
3. **Flash MicroPython**: 
   - In Thonny, go to **Tools → Options → Interpreter**
   - Select **MicroPython (ESP32)**
   - Click **Install or update MicroPython** (select the `.bin` file)
4. Once flashed, you should see the `>>>` REPL prompt in Thonny

---

## Flashing the ESP32-CAM

1. Connect the **FTDI adapter** to the ESP32-CAM as shown in the [wiring guide](#esp32-cam-connections-for-flashing-via-ftdi)
2. **Bridge GPIO 0 to GND** (put board into flash mode)
3. Open `esp32cam_firmware/esp32cam_firmware.ino` in Arduino IDE
4. **Edit WiFi credentials** at the top of the file:
   ```cpp
   const char* ssid     = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
5. Select board **AI Thinker ESP32-CAM**, select your COM port
6. Click **Upload** (→ button)
7. If upload doesn't start, press the **RST** button on the ESP32-CAM
8. After upload completes:
   - **Remove** the GPIO 0 → GND bridge
   - Press **RST** to reboot the ESP32-CAM
9. Open **Serial Monitor** (115200 baud) → you should see the assigned IP address
10. Test: open `http://<cam_ip>/capture` in your browser → you should see a JPEG photo

---

## Flashing the ESP32 DevKit

1. Connect your ESP32 DevKit via USB
2. Open **Thonny IDE** → make sure it says "MicroPython (ESP32)" at the bottom
3. Upload all files from `esp32_devkit/` to the ESP32:
   - In Thonny, go to **View → Files** to see the file browser
   - Navigate to `esp32_devkit/` on your computer (left panel)
   - Select each file → **Right-click → Upload to /**
   - Upload these files: `config.py`, `boot.py`, `pir.py`, `servo.py`, `camera_client.py`, `anpr.py`, `logger.py`, `parking.py`, `main.py`
4. **Edit `config.py`** directly on the ESP32 (double-click it in Thonny's device panel):
   - Set your WiFi credentials
   - Set the ESP32-CAM's IP address
   - Set your Gemini API key (if using real ANPR)
5. Press **Ctrl+D** or click the Stop/Restart button to reboot → the system starts automatically

---

## Configuration

All settings are in `esp32_devkit/config.py`. Edit this file on the ESP32 via Thonny:

| Setting | Default | Description |
|---------|---------|-------------|
| `WIFI_SSID` | `"YOUR_WIFI_SSID"` | Your WiFi network name |
| `WIFI_PASSWORD` | `"YOUR_WIFI_PASSWORD"` | Your WiFi password |
| `CAM_HOST` | `"192.168.1.100"` | ESP32-CAM IP address |
| `PIN_PIR_ENTRY` | `27` | Entry PIR sensor GPIO |
| `PIN_PIR_EXIT` | `26` | Exit PIR sensor GPIO |
| `PIN_SERVO` | `13` | Servo signal GPIO |
| `SERVO_OPEN_ANGLE` | `90` | Gate open angle (degrees) |
| `SERVO_CLOSE_ANGLE` | `0` | Gate closed angle (degrees) |
| `GATE_OPEN_DURATION` | `5` | Seconds gate stays open |
| `MAX_CAPACITY` | `10` | Max cars allowed |
| `ANPR_MODE` | `"simulated"` | `"simulated"` or `"gemini"` |
| `GEMINI_API_KEY` | `"YOUR_GEMINI_API_KEY"` | Google Gemini API key |

---

## Testing Guide

Test each component individually by pasting these scripts into the **Thonny REPL** (the `>>>` prompt). Press **Stop** between tests.

### Test 1: WiFi Connection
```python
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print("Connected:", wlan.isconnected())
print("IP:", wlan.ifconfig()[0])
```

### Test 2: Entry PIR Sensor
```python
from machine import Pin
import time
pir = Pin(27, Pin.IN)
print("Wave your hand near the ENTRY PIR sensor...")
for i in range(100):
    if pir.value():
        print("MOTION DETECTED!")
    time.sleep(0.3)
```

### Test 3: Exit PIR Sensor
```python
from machine import Pin
import time
pir = Pin(26, Pin.IN)
print("Wave your hand near the EXIT PIR sensor...")
for i in range(100):
    if pir.value():
        print("MOTION DETECTED!")
    time.sleep(0.3)
```

### Test 4: Servo Gate
```python
from machine import Pin, PWM
import time
servo = PWM(Pin(13), freq=50)
print("Opening gate (90 degrees)...")
servo.duty(77)
time.sleep(2)
print("Closing gate (0 degrees)...")
servo.duty(26)
time.sleep(1)
servo.deinit()
print("Done!")
```

### Test 5: ESP32-CAM Connection
```python
import urequests
resp = urequests.get("http://192.168.1.100/status")  # ← Use your CAM IP
print(resp.json())
resp.close()
```

### Test 6: Image Capture
```python
import camera_client
img = camera_client.capture_image()
if img:
    print("Success! Image size:", len(img), "bytes")
else:
    print("Failed to capture image")
```

### Test 7: ANPR (Simulated)
```python
import anpr
plate = anpr.recognize_plate(b"fake_image_data")
print("Plate:", plate)
```

### Test 8: Full System
```python
import parking
system = parking.ParkingSystem()
system.run()
# Wave hand at entry PIR → watch the full flow
# Press Ctrl+C to stop
```

---

## System Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    ENTRY FLOW                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Car arrives → PIR (Entry) triggers                          │
│       │                                                      │
│       ▼                                                      │
│  Check capacity → FULL? → Deny entry (log "FULL")            │
│       │                                                      │
│       ▼ (not full)                                           │
│  Request image from ESP32-CAM (HTTP GET /capture)            │
│       │                                                      │
│       ▼                                                      │
│  Send JPEG to Gemini API → Extract plate text                │
│       │                                                      │
│       ▼                                                      │
│  Log: timestamp + plate + "ENTRY" → CSV file + serial        │
│       │                                                      │
│       ▼                                                      │
│  Open servo gate (90°) → Wait 5 seconds → Close gate (0°)   │
│       │                                                      │
│       ▼                                                      │
│  Increment vehicle count                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    EXIT FLOW                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Car exits → PIR (Exit) triggers                             │
│       │                                                      │
│       ▼                                                      │
│  Capture + ANPR (same as entry)                              │
│       │                                                      │
│       ▼                                                      │
│  Log: timestamp + plate + "EXIT" → CSV file + serial         │
│       │                                                      │
│       ▼                                                      │
│  Open gate → Wait → Close gate                               │
│       │                                                      │
│       ▼                                                      │
│  Decrement vehicle count                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### WiFi Issues

| Problem | Solution |
|---------|----------|
| ESP32-CAM doesn't connect | Check SSID/password in the Arduino sketch. Ensure 2.4 GHz network (ESP32 doesn't support 5 GHz) |
| ESP32 DevKit doesn't connect | Check `config.py` credentials. Run `boot.py` manually in REPL |
| Devices can't see each other | Both must be on the same WiFi network / subnet |

### Camera Issues

| Problem | Solution |
|---------|----------|
| `/capture` returns error | Reset the ESP32-CAM. Check if PSRAM is available |
| Blurry/dark images | Adjust camera settings in `initCamera()`. Ensure adequate lighting |
| Connection timeout | Check ESP32-CAM IP address in `config.py`. Try pinging the IP |

### Sensor Issues

| Problem | Solution |
|---------|----------|
| PIR always reads HIGH | Check wiring. SR602 needs a 5–30 second warm-up after power-on |
| PIR never triggers | Verify OUT pin is connected to the correct GPIO. Check 3.3V power |
| Double triggers | Increase `PIR_DEBOUNCE_MS` in `config.py` (default: 3000ms) |

### Servo Issues

| Problem | Solution |
|---------|----------|
| Servo jitters/buzzes | Normal if PWM stays active — the code stops PWM after each move |
| Servo doesn't move | Check 5V power supply. USB power may be insufficient |
| Wrong angle | Adjust `SERVO_OPEN_ANGLE` and `SERVO_CLOSE_ANGLE` in `config.py` |

### ANPR Issues

| Problem | Solution |
|---------|----------|
| Always returns "UNKNOWN" | Check API key. Ensure camera captures readable plate images |
| API timeout | Check internet connectivity. Gemini API needs HTTPS access |
| Simulated mode only | Set `ANPR_MODE = "gemini"` and provide a valid `GEMINI_API_KEY` |

---

## Optional Improvements

- **OLED Display** — Show plate number and vehicle count on a small screen (SSD1306 via I2C)
- **Buzzer** — Beep on entry/exit or when parking is full
- **Web Dashboard** — Serve a simple HTTP page from the ESP32 DevKit showing live status and log
- **MQTT Integration** — Publish events to an MQTT broker for IoT platform integration
- **LED Indicators** — Green LED for "spaces available", Red for "full"
- **NTP Time Sync** — Sync the RTC with an NTP server for accurate timestamps
- **Parking Duration** — Match entry/exit plates to calculate time spent
- **Database Backend** — Send logs to Firebase, Google Sheets, or a custom server
