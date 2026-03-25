# ============================================================
#  parking.py — Core Parking System Logic (FIXED)
# ============================================================
import time
import config
import pir
import servo
import camera_client
import anpr
import logger
import gc

class ParkingSystem:
    """Main parking system controller."""

    def __init__(self):
        self.vehicle_count = 0
        self.is_running = False
        print("\n" + "=" * 50)
        print("  AI SMART CAR PARKING SYSTEM")
        print("=" * 50)

    def startup_check(self):
        """Run startup diagnostics."""
        print("\n[INIT] Running startup checks...")
        
        # Force gate closed on startup via the hardware driver
        print("  [OK] Resetting barrier to CLOSED position...")
        servo.gate.close_gate()

        # Check ESP32-CAM
        if camera_client.check_status():
            print("  [OK] ESP32-CAM is reachable")
        else:
            print("  [!!] ESP32-CAM is NOT reachable. Check IP: {}".format(config.CAM_HOST))
            return False

        print("[INIT] All checks PASSED ✓")
        return True

    def _handle_entry(self):
        """Handle a vehicle entry event."""
        print("\n" + "-" * 40)
        print("[EVENT] Vehicle detected at ENTRY")

        if self.vehicle_count >= config.MAX_CAPACITY:
            print("[FULL] Parking is FULL! Entry denied.")
            # We must reset the sensor even if we don't open the gate
            # but we wait for them to leave the sensor area first
            while pir.entry_sensor.raw_value() == 1:
                time.sleep_ms(500)
            pir.entry_sensor.reset()
            return

        # 1. Capture & Recognize
        image = camera_client.capture_image()
        plate = anpr.recognize_plate(image)
        
        # Clean up image memory immediately
        del image
        gc.collect()

        # 2. Log & Actuate
        logger.log_event(plate, "ENTRY", "count:{}/{}".format(self.vehicle_count + 1, config.MAX_CAPACITY))
        servo.gate.open_gate()

        # 3. Wait & Close
        print("[GATE] Waiting {}s for vehicle to pass...".format(config.GATE_OPEN_DURATION))
        time.sleep(config.GATE_OPEN_DURATION)
        servo.gate.close_gate()

        # 4. FIX: THE RESET SEQUENCE
        # Wait for the physical sensor to stop seeing the car before unlocking
        print("[PIR] Waiting for entry sensor to clear...")
        while pir.entry_sensor.raw_value() == 1:
            time.sleep_ms(200)
        
        pir.entry_sensor.reset()
        self.vehicle_count += 1
        print("[STATUS] Entry Complete. Parked: {}/{}".format(self.vehicle_count, config.MAX_CAPACITY))

    def _handle_exit(self):
        """Handle a vehicle exit event."""
        print("\n" + "-" * 40)
        print("[EVENT] Vehicle detected at EXIT")

        # 1. Capture & Recognize
        image = camera_client.capture_image()
        plate = anpr.recognize_plate(image)
        
        del image
        gc.collect()

        # 2. Log & Actuate
        new_count = max(0, self.vehicle_count - 1)
        logger.log_event(plate, "EXIT", "count:{}/{}".format(new_count, config.MAX_CAPACITY))
        servo.gate.open_gate()

        # 3. Wait & Close
        time.sleep(config.GATE_OPEN_DURATION)
        servo.gate.close_gate()

        # 4. FIX: THE RESET SEQUENCE
        print("[PIR] Waiting for exit sensor to clear...")
        while pir.exit_sensor.raw_value() == 1:
            time.sleep_ms(200)
            
        pir.exit_sensor.reset()
        self.vehicle_count = new_count
        print("[STATUS] Exit Complete. Parked: {}/{}".format(self.vehicle_count, config.MAX_CAPACITY))

    def run(self):
        """Main loop — poll sensors and handle events."""
        if not self.startup_check():
            print("[WARN] Startup failed. Check connections and restart.")
        
        self.is_running = True
        print("\n[RUN] System ACTIVE. Monitoring sensors...")

        while self.is_running:
            try:
                # Polling logic
                if pir.entry_sensor.is_triggered():
                    self._handle_entry()

                if pir.exit_sensor.is_triggered():
                    self._handle_exit()

                time.sleep_ms(config.SENSOR_POLL_MS)

            except KeyboardInterrupt:
                self.is_running = False
            except Exception as e:
                print("[ERROR] Loop error:", e)
                time.sleep(2)

        servo.gate.close_gate()
        print("[STOP] System offline.")