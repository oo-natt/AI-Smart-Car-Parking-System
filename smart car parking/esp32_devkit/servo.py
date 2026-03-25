# ============================================================
#  servo.py — Micro Servo Barrier Gate Driver
# ============================================================
#  Controls a micro servo (SG90 / MG90S) via PWM using
#  duty_ns() for precise pulse timing.
#
#  SG90 pulse timing at 50 Hz (20ms period):
#    0°   → 500,000 ns pulse
#    90°  → 1,500,000 ns pulse
#    180° → 2,500,000 ns pulse
# ============================================================

from machine import Pin, PWM
import time
import config


class ServoGate:
    """Barrier gate controlled by a micro servo."""

    _MIN_PULSE_NS = 500000    # 0.5ms → 0 degrees
    _MAX_PULSE_NS = 2500000   # 2.5ms → 180 degrees
    _FREQ = 50                # 50 Hz standard servo frequency

    def __init__(self, pin_num):
        self.pin_num = pin_num
        self._pwm = None
        self.is_open = False

    def _start_pwm(self):
        """Start PWM if not already running."""
        if self._pwm is None:
            self._pwm = PWM(Pin(self.pin_num), freq=self._FREQ)

    def _stop_pwm(self):
        """Stop PWM completely and force pin LOW."""
        if self._pwm is not None:
            self._pwm.deinit()
            self._pwm = None
        # Force pin LOW so it doesn't float and cause twitching
        Pin(self.pin_num, Pin.OUT).value(0)

    def _angle_to_ns(self, angle):
        """Convert angle (0-180) to pulse width in nanoseconds."""
        angle = max(0, min(180, angle))
        return int(self._MIN_PULSE_NS + (angle / 180) * (self._MAX_PULSE_NS - self._MIN_PULSE_NS))

    def _move_to(self, angle):
        """Move servo to the specified angle, then stop PWM."""
        self._start_pwm()
        pulse_ns = self._angle_to_ns(angle)
        self._pwm.duty_ns(pulse_ns)
        time.sleep_ms(1000)  # Wait for servo to reach position
        self._stop_pwm()     # Kill PWM to prevent jitter

    def open_gate(self):
        """Open the barrier gate."""
        if not self.is_open:
            print("[SERVO] Opening gate...")
            self._move_to(config.SERVO_OPEN_ANGLE)
            self.is_open = True
            print("[SERVO] Gate OPEN")

    def close_gate(self):
        """Close the barrier gate."""
        if self.is_open:
            print("[SERVO] Closing gate...")
            self._move_to(config.SERVO_CLOSE_ANGLE)
            self.is_open = False
            print("[SERVO] Gate CLOSED")

    def test_sweep(self):
        """Test: sweep from 0 to 180 and back."""
        print("[SERVO] Test sweep starting...")
        self._start_pwm()
        for angle in range(0, 181, 5):
            self._pwm.duty_ns(self._angle_to_ns(angle))
            time.sleep(0.05)
        for angle in range(180, -1, -5):
            self._pwm.duty_ns(self._angle_to_ns(angle))
            time.sleep(0.05)
        self._stop_pwm()
        print("[SERVO] Test sweep complete")


# Pre-configured gate instance
gate = ServoGate(config.PIN_SERVO)
