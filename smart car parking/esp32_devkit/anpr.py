# ============================================================
#  anpr.py — Automatic Number Plate Recognition
# ============================================================
#  Sends a captured JPEG image to a cloud API for license plate
#  recognition. Supports two modes:
#
#    "simulated" — Returns a fake plate (for testing without API)
#    "gemini"    — Uses Google Gemini API (free tier)
#
#  To switch modes, change config.ANPR_MODE in config.py.
# ============================================================

import config

try:
    import urequests
    import ubinascii
    import ujson
except ImportError:
    import requests as urequests
    import binascii as ubinascii
    import json as ujson

# Simulated plates for testing
_SIM_PLATES = [
    "ABC 1234", "XYZ 5678", "KL 01 AB 9999",
    "MH 12 DE 1433", "TN 07 BQ 4567", "DL 3C AW 0001",
]
_sim_index = 0


def recognize_plate(jpeg_bytes):
    """
    Recognize the license plate in the given JPEG image.

    Args:
        jpeg_bytes: Raw JPEG image bytes from ESP32-CAM.

    Returns:
        A string with the recognized plate number,
        or "UNKNOWN" if recognition fails.
    """
    if config.ANPR_MODE == "simulated":
        return _simulated_recognize()
    elif config.ANPR_MODE == "gemini":
        return _gemini_recognize(jpeg_bytes)
    else:
        print("[ANPR] Unknown mode:", config.ANPR_MODE)
        return "UNKNOWN"


def _simulated_recognize():
    """Return a fake plate number for testing."""
    global _sim_index
    plate = _SIM_PLATES[_sim_index % len(_SIM_PLATES)]
    _sim_index += 1
    print("[ANPR] Simulated plate:", plate)
    return plate


def _gemini_recognize(jpeg_bytes):
    """
    Use Google Gemini API to read the license plate from an image.

    The image is base64-encoded and sent as an inline image part
    along with a text prompt asking Gemini to extract the plate.
    """
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("[ANPR] Gemini API key not configured! Using simulated mode.")
        return _simulated_recognize()

    try:
        # Base64-encode the JPEG image in chunks to save memory
        import gc
        gc.collect()
        b64_image = ubinascii.b2a_base64(jpeg_bytes).decode().strip()

        # Build the Gemini API request
        url = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}".format(
            config.GEMINI_MODEL, config.GEMINI_API_KEY
        )

        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            "Look at this image of a vehicle. "
                            "Read the license plate / number plate text. "
                            "Return ONLY the plate text in uppercase, nothing else. "
                            "If you cannot read a plate, return exactly: UNKNOWN"
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_image
                        }
                    }
                ]
            }]
        }

        headers = {"Content-Type": "application/json"}
        body = ujson.dumps(payload)

        print("[ANPR] Sending image to Gemini API...")
        resp = urequests.post(url, data=body, headers=headers, timeout=15)

        if resp.status_code != 200:
            print("[ANPR] Gemini API error, HTTP", resp.status_code)
            resp.close()
            return "UNKNOWN"

        result = resp.json()
        resp.close()

        # Extract the text response
        try:
            plate_text = result["candidates"][0]["content"]["parts"][0]["text"]
            plate_text = plate_text.strip().upper()
            print("[ANPR] Recognized plate:", plate_text)
            return plate_text if plate_text else "UNKNOWN"
        except (KeyError, IndexError):
            print("[ANPR] Could not parse Gemini response")
            return "UNKNOWN"

    except Exception as e:
        print("[ANPR] Gemini API error:", e)
        return "UNKNOWN"
