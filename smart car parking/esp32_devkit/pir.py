# ============================================================
#  pir.py — SR602 PIR Motion Sensor Driver
# ============================================================
#  The SR602 outputs HIGH (3.3V) when motion is detected and
#  LOW (0V) when idle. This module wraps two sensors (entry and
#  exit) with software debounce to prevent rapid re-triggering.
# ============================================================

from machine import Pin
import time
import config


class PIRSensor:
    """Driver for a single SR602 PIR motion sensor."""

    def __init__(self, pin_num, name="PIR"):
        self.pin = Pin(pin_num, Pin.IN)
        self.name = name
        self._last_trigger_ms = 0
        self._prev_value = 0   # Track previous state for edge detection

    def is_triggered(self):
        """
        Returns True ONCE when motion is first detected (rising edge).
        Will not trigger again until the sensor goes LOW first AND
        the debounce window has passed.
        """
        current = self.pin.value()
        triggered = False

        # Only trigger on rising edge (0 → 1)
        if current == 1 and self._prev_value == 0:
            now = time.ticks_ms()
            elapsed = time.ticks_diff(now, self._last_trigger_ms)
            if elapsed >= config.PIR_DEBOUNCE_MS:
                self._last_trigger_ms = now
                triggered = True

        self._prev_value = current
        return triggered

    def raw_value(self):
        """Returns the raw digital reading (0 or 1) — for debugging."""
        return self.pin.value()


# Pre-configured sensor instances
entry_sensor = PIRSensor(config.PIN_PIR_ENTRY, name="ENTRY")
exit_sensor  = PIRSensor(config.PIN_PIR_EXIT,  name="EXIT")
