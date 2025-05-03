from gpiozero import DistanceSensor
from signal import pause

sensor = DistanceSensor(echo=27, trigger=17, max_distance=5)

try:
    print("Sensor is running... Press Ctrl+C to stop.")
    pause()  # Keeps the script running
except KeyboardInterrupt:
    print("Stopping sensor...")
finally:
    sensor.close()  # Ensures the GPIO pin is released
