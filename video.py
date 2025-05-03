from picamera2 import Picamera2
import time

# Initialize the Picamera2 instance
picam2 = Picamera2()

# Create and configure the video configuration without any transformation
video_config = picam2.create_video_configuration()
picam2.configure(video_config)

# Start the camera preview (optional)
picam2.start()

output_file = "output_video.h264"
# Open the file in write-binary mode and pass the handle to start_recording
with open(output_file, "wb") as f:
    picam2.start_recording(f)
    time.sleep(10)
    picam2.stop_recording()

picam2.stop()
print(f"Video recorded and saved to {output_file}")
