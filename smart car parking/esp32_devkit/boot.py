# ============================================================
#  boot.py — Runs automatically on ESP32 power-up
# ============================================================
#  Connects to WiFi with retry logic. If connection fails after
#  max retries, the system continues in offline mode.
# ============================================================

import network
import time
import config


def connect_wifi():
    """Connect to WiFi using credentials from config.py."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("[WIFI] Already connected:", wlan.ifconfig()[0])
        return True

    print("[WIFI] Connecting to", config.WIFI_SSID, "...")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    max_attempts = 20
    attempt = 0
    while not wlan.isconnected() and attempt < max_attempts:
        time.sleep(0.5)
        attempt += 1
        print(".", end="")

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("\n[WIFI] Connected! IP:", ip)
        return True
    else:
        print("\n[WIFI] Connection FAILED after", max_attempts, "attempts")
        return False


# Auto-connect on boot
connected = connect_wifi()
if not connected:
    print("[WARN] Running in OFFLINE mode — camera/ANPR will not work")
