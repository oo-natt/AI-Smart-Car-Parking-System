# ============================================================
#  logger.py — Parking Event Logger
# ============================================================
#  Logs vehicle entry/exit events with timestamps. Events are
#  printed to serial AND saved to a CSV file on the ESP32 flash.
# ============================================================

import time
import config


def _timestamp():
    """
    Returns a human-readable timestamp string.
    Format: YYYY-MM-DD HH:MM:SS (from RTC or uptime if no NTP).
    """
    try:
        t = time.localtime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            t[0], t[1], t[2], t[3], t[4], t[5]
        )
    except Exception:
        # Fallback: seconds since boot
        return "T+{}s".format(time.time())


def log_event(plate, direction, extra=""):
    """
    Log a parking event.

    Args:
        plate:     License plate text (e.g., "ABC 1234")
        direction: "ENTRY" or "EXIT"
        extra:     Optional extra info
    """
    ts = _timestamp()
    line = "{},{},{},{}".format(ts, direction, plate, extra)

    # Print to serial console
    print("[LOG] {} | {} | {} {}".format(ts, direction, plate, extra))

    # Append to CSV file
    try:
        with open(config.LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print("[LOG] File write error:", e)


def get_log():
    """
    Read and return all logged entries as a list of strings.
    Returns an empty list if the log file doesn't exist.
    """
    try:
        with open(config.LOG_FILE, "r") as f:
            return f.readlines()
    except OSError:
        return []


def clear_log():
    """Clear the log file."""
    try:
        with open(config.LOG_FILE, "w") as f:
            f.write("timestamp,direction,plate,extra\n")
        print("[LOG] Log file cleared")
    except Exception as e:
        print("[LOG] Clear error:", e)


def print_log():
    """Print all log entries to serial."""
    entries = get_log()
    if not entries:
        print("[LOG] No entries yet")
        return
    print("[LOG] === Parking Log ({} entries) ===".format(len(entries)))
    for entry in entries:
        print("  ", entry.strip())
    print("[LOG] === End ===")


# Initialize log file with header if it doesn't exist
try:
    with open(config.LOG_FILE, "r") as f:
        pass  # File exists
except OSError:
    clear_log()  # Create with header
