# ============================================================
#  main.py — Entry Point
# ============================================================
#  This file runs automatically after boot.py.
#  It initializes the parking system and starts the main loop.
# ============================================================

import parking


def main():
    """Initialize and run the Smart Parking System."""
    system = parking.ParkingSystem()
    system.run()


# Start the system
main()
