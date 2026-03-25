# ============================================================
#  camera_client.py — HTTP Client for ESP32-CAM
# ============================================================
#  Fetches JPEG images from the ESP32-CAM over WiFi using
#  simple HTTP GET requests. The ESP32-CAM must be running
#  the Arduino firmware with /capture and /status endpoints.
# ============================================================

import urequests
import usocket
import config


def _cam_url(path):
    """Build full URL for an ESP32-CAM endpoint."""
    return "http://{}:{}{}".format(config.CAM_HOST, config.CAM_PORT, path)


def check_status():
    """
    Check if the ESP32-CAM is online and ready.
    Returns True if reachable, False otherwise.
    """
    try:
        url = _cam_url("/status")
        resp = urequests.get(url)
        data = resp.json()
        resp.close()
        ready = data.get("status") == "ready"
        if ready:
            print("[CAM] ESP32-CAM is ready (IP: {})".format(data.get("ip", "?")))
        return ready
    except Exception as e:
        print("[CAM] Status check failed:", e)
        return False


def capture_image():
    """
    Capture a JPEG image from the ESP32-CAM.
    Returns raw bytes on success, None on failure.

    Uses a raw socket with timeout instead of urequests
    to handle large binary responses more reliably.
    """
    try:
        print("[CAM] Requesting capture from {}:{}".format(config.CAM_HOST, config.CAM_PORT))

        # Open socket with timeout
        addr = usocket.getaddrinfo(config.CAM_HOST, config.CAM_PORT)[0][-1]
        sock = usocket.socket()
        sock.settimeout(10)
        sock.connect(addr)

        # Send HTTP GET request
        sock.send(b"GET /capture HTTP/1.0\r\nHost: {}\r\n\r\n".format(config.CAM_HOST))

        # Read response
        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            except Exception:
                break

        sock.close()

        if not response:
            print("[CAM] Empty response")
            return None

        # Split headers from body (separated by \r\n\r\n)
        header_end = response.find(b"\r\n\r\n")
        if header_end < 0:
            print("[CAM] Invalid HTTP response")
            return None

        # Check for 200 OK
        header = response[:header_end].decode()
        if "200" not in header.split("\r\n")[0]:
            print("[CAM] Capture failed:", header.split("\r\n")[0])
            return None

        image_bytes = response[header_end + 4:]
        print("[CAM] Captured image: {} bytes".format(len(image_bytes)))
        return image_bytes

    except Exception as e:
        print("[CAM] Capture error:", e)
        return None
