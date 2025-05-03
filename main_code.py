import os
import cv2
import pygame
import time
import numpy as np
import google.generativeai as genai
import requests
import io

from PIL import Image
from threading import Event
from gpiozero import DistanceSensor
from picamera2 import Picamera2
from ultralytics import YOLO
import RPi.GPIO as GPIO
GPIO.cleanup()  # Reset any previously locked GPIO states
GPIO.setmode(GPIO.BCM)  # Set GPIO mode before setup
# -----------------------------------------------------------------------------
# Configuration

# Gemini API
GENAI_API_KEY = "(replace with your actual key)"
# ElevenLabs API configuration (replace with your actual key)
ELEVENLABS_API_KEY = "(replace with your actual key)"  
ELEVENLABS_VOICE_ID = "(replace with your actual key)" 
# -----------------------------------------------------------------------------

# Gemini API configuration (replace with your actual key)
genai.configure(api_key=GENAI_API_KEY)
# Paths for sounds and image saving
IMAGE_SAVE_PATH = "captured_image.jpg"
TRIGGER_SOUND = "/home/pi/Desktop/pbl/beep.wav"  # Ensure this file exists

# -----------------------------------------------------------------------------
# Initialize GPIO
# -----------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)

# -----------------------------------------------------------------------------
# Hardware Initialization
# -----------------------------------------------------------------------------
# Ultrasonic sensor (using gpiozero)
sensor = DistanceSensor(echo=27, trigger=17, max_distance=2)

# PiCamera2 initialization
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

# -----------------------------------------------------------------------------
# Model and Audio Initialization
# -----------------------------------------------------------------------------
custom_model = YOLO("Yolo_best.pt")
default_model = YOLO("yolov8n.pt")
pygame.mixer.init()

alert_event = Event()

# -----------------------------------------------------------------------------
# Distance & Object Parameters
# -----------------------------------------------------------------------------
FOCAL_LENGTH = 700  # For distance estimation (pixels)
MAX_DISTANCE = 200  # cm

KNOWN_WIDTHS_CUSTOM = {
    "AIR COMPRESSOR": 50, "BAMBULAB 3D PRINTER": 45, "BLACK MARKER": 2,
    "BLUE ROBOTARM": 30, "BOOK": 15, "BnR TOOLKIT": 35, "Chair": 50,
    "DOBOT MAGICIAN": 40, "DUSTBIN": 45, "ELEGOO Mercury XS Cure Station": 50,
    "ELEGOO Mercury XS Wash Station": 50, "ELGO INFINITY 3D PRINTER GREEN": 50,
    "ENDERMAX 3D PRINTER": 50, "ENDER 3D PRINTER": 50, "FIRE EXTINGUISHER": 25,
    "FLASHFORGE 3D PRINTER": 55, "HP MONITOR": 50, "JANATICS Modular Manufacturing System": 60,
    "LAPTOP": 30, "MARKER": 2, "MOBILE PHONE": 7, "NOTICE BOARD": 150,
    "PROJECTOR REMOTE": 10, "SMART MONITOR": 55, "STUDENT TABLE": 120,
    "TURTLEBOT MINI": 40, "WATCH": 5, "X PLUS QIDI 3D PRINTER": 55
}


KNOWN_WIDTHS_BASE = {
   "person": 40, "backpack": 30, "handbag": 25, "wallet": 10,
   "book": 15, "notebook": 18, "pen": 1.5, "pencil": 1, "eraser": 4,
   "ruler": 30, "scissors": 12, "calculator": 8, "cell phone": 7,
   "tablet": 20, "laptop": 30, "computer monitor": 50, "mouse": 6,
   "keyboard": 45, "projector": 35, "headphones": 15, "speaker": 10,
   "microphone": 8, "desk": 120, "chair": 45, "whiteboard": 150,
   "blackboard": 180, "table": 120, "cupboard": 90, "bookshelf": 100,
   "bottle": 7, "mug": 8, "plate": 25, "spoon": 4, "fork": 4, "knife": 3,
   "lamp": 20, "fan": 50, "clock": 35, "pillow": 40, "blanket": 150, "bed": 160,
   "whiteboard marker": 2, "chalk": 1, "school bag": 35, "globe": 30, "trophy": 25,
   "fire extinguisher": 20, "trash bin": 40, "window": 150, "door": 90,
   "board eraser": 8, "remote control": 15, "shoe": 10
}

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------
def speak(text):
    """Convert text to speech using ElevenLabs."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "accept": "audio/mpeg"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        audio_data = response.content
        sound = pygame.mixer.Sound(io.BytesIO(audio_data))
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.Clock().tick(10)
    except requests.exceptions.RequestException as e:
        print(f"Error during ElevenLabs API request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def play_trigger_sound():
    """Play a short trigger sound."""
    try:
        pygame.mixer.music.load(TRIGGER_SOUND)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing trigger sound: {e}")

def adjust_frame(frame):
    """Rotate frame to correct orientation."""
    if frame is None:
        return None
    return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
# -----------------------------------------------------------------------------
# Scenario 1: YOLO Detection with Ultrasonic Check
# -----------------------------------------------------------------------------
def scenario_1_detection():
    ultrasonic_distance = sensor.distance * 100  # in cm
    print(f"Ultrasonic Distance: {ultrasonic_distance:.2f} cm")
    if not (15 <= ultrasonic_distance <= 400):
        speak("Ultrasonic sensor reading is out of range.")
        return

    play_trigger_sound()
    time.sleep(0.5)
    frame = picam2.capture_array()
    if frame is None:
        speak("Failed to capture a frame.")
        return

    frame = adjust_frame(frame)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    
    detected_objects = {}

    # Custom model detection
    custom_results = custom_model(frame, verbose=False, conf=0.5)
    for result in custom_results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())
            label = custom_model.names[cls]
            object_width = x2 - x1
            known_width = KNOWN_WIDTHS_CUSTOM.get(label)
            if known_width and object_width:
                distance_est = (known_width * FOCAL_LENGTH) / object_width
                if distance_est <= MAX_DISTANCE:
                    detected_objects[label] = (x1, y1, x2, y2, conf, distance_est, "custom")

    # Default model detection
    default_results = default_model(frame, verbose=False, conf=0.5)
    for result in default_results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())
            label = default_model.names[cls]
            if label in ["tv", "refrigerator", "bag"]:
                continue
            if label not in detected_objects:
                object_width = x2 - x1
                known_width = KNOWN_WIDTHS_BASE.get(label)
                if known_width and object_width:
                    distance_est = (known_width * FOCAL_LENGTH) / object_width
                    if distance_est <= MAX_DISTANCE:
                        detected_objects[label] = (x1, y1, x2, y2, conf, distance_est, "base")

    # Process detected objects and compute the average distance
    detection_messages = []
    for label, (x1, y1, x2, y2, conf, distance_est, source) in detected_objects.items():
        avg_distance = (distance_est + sensor.distance * 100) / 2  # Average of YOLO and ultrasonic
        if avg_distance < 100:
            spoken_distance = f"{avg_distance:.0f} centimeter"
        else:
            spoken_distance = f"{avg_distance/100:.2f} meter"
        message = f"{label} detected at distance of {spoken_distance}"
        detection_messages.append(message)
        print(f"{label} | YOLO Distance: {distance_est:.0f} cm | Ultrasonic: {sensor.distance * 100:.2f} cm | Average: {spoken_distance} | Confidence: {conf:.2f}")
        color = (0, 255, 0) if "custom" in detected_objects[label] else (255, 0, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label}, {spoken_distance}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    if detected_objects:
        final_message = " , ".join([f"{k} detected at distance of {v[5]:.0f} cm" for k, v in detected_objects.items()])
        speak("Detected objects: " + final_message)
    else:
        speak("No objects detected.")

    cv2.imwrite("detection_output.jpg", frame)
    print("Detection output saved to detection_output.jpg")

# -----------------------------------------------------------------------------
# Scenario 2: Capture Image and Describe via Gemini API
# -----------------------------------------------------------------------------
def capture_image():
    frame = picam2.capture_array()
    if frame is None:
        speak("Failed to capture image.")
        return None
    frame = adjust_frame(frame)
    cv2.imwrite(IMAGE_SAVE_PATH, frame)
    speak("Image captured and saved.")
    return IMAGE_SAVE_PATH

def describe_image():
    if not os.path.exists(IMAGE_SAVE_PATH):
        speak("No image available to describe. Please capture an image first.")
        return
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        with Image.open(IMAGE_SAVE_PATH) as img:
            response = model.generate_content([
                "Act as a visual guide for a visually impaired person. Briefly describe the surroundings, including the estimated number of people, their positions and directions, nearby objects, potential obstacles, and available paths. Mention whether the environment appears safe or unsafe to move in. Also, describe the appearance of the nearest person in simple terms. Keep the description concise and informative.", img
            ])
        if response and hasattr(response, 'text'):
            description = response.text.strip()
            print("Description:", description)
            # Clean description by removing asterisks
            cleaned_description = description.replace('*', '')
            speak("Description: " + cleaned_description)
        else:
            speak("Failed to generate a description from Gemini.")
    except Exception as e:
        speak("Error describing image: " + str(e))

def scenario_2_describe():
    play_trigger_sound()
    time.sleep(0.5)
    if capture_image():
        describe_image()

# -----------------------------------------------------------------------------
# Button Configuration for Scenario Selection
# -----------------------------------------------------------------------------
BUTTON1_PIN = 12  # For Scenario 1 (YOLO detection)
BUTTON2_PIN = 20  # For Scenario 2 (Image capture & description)

GPIO.setup(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button1_callback(channel):
    print("Button 1 pressed: Starting YOLO detection scenario.")
    scenario_1_detection()

def button2_callback(channel):
    print("Button 2 pressed: Starting image capture and description scenario.")
    scenario_2_describe()

GPIO.add_event_detect(BUTTON1_PIN, GPIO.FALLING, callback=button1_callback, bouncetime=300)
GPIO.add_event_detect(BUTTON2_PIN, GPIO.FALLING, callback=button2_callback, bouncetime=300)

# -----------------------------------------------------------------------------
# Main Loop: Keep script running and listening for button events
# -----------------------------------------------------------------------------
print("System ready. Press button one for YOLO detection or button two for image capture and description.")
speak("System ready. Press button one for YOLO detection or button two for image capture and description.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    GPIO.cleanup()
    picam2.stop()
