# 🧠 Blind Assistance System – YOLO + Gemini Integration

A Raspberry Pi-based wearable assistive system that performs real-time object detection and visual scene understanding for visually impaired users.

---

## 📁 Project Structure

```
pbl/
├── main_code.py              # Main Python script
├── beep.wav                  # Trigger sound
├── Yolo_best.pt              # Custom YOLO model for lab objects
├── yolov8n.pt                # Pre-trained YOLOv8 model (COCO)
├── captured_image.jpg        # Image captured for Gemini analysis
├── detection_output.jpg      # Output frame with detection boxes
├── README.md                 # Project documentation
```

---

## 🚀 How to Run

```bash
cd /home/pi/Desktop/pbl/
sudo pkill -9 python
python main_code.py
```

Ensure a stable internet connection is active before running the program.

---

## 🔐 API Setup Instructions

### Gemini API (Google)

* Get it from: [https://aistudio.google.com/](https://aistudio.google.com/)
* Add in `main_code.py` (around line 19):

```python
GENAI_API_KEY = "your_api_key_here"
genai.configure(api_key=GENAI_API_KEY)
```

### ElevenLabs API

* Create an account at: [https://www.elevenlabs.io/](https://www.elevenlabs.io/)
* Go to Voice Library → Choose a voice (e.g., Rachel, Bella)
* Add in `main_code.py` (around lines 21–22):

```python
ELEVENLABS_API_KEY = "your_api_key_here"
ELEVENLABS_VOICE_ID = "your_voice_id_here"
```

---

## 🎮 Operating Modes

### 🔍 Object Detection Mode (YOLO)

* Press **Button 1 (GPIO 12)**
* Detects lab and general objects using YOLOv8
* Measures distance using bounding box + ultrasonic sensor
* Announces via ElevenLabs voice API

### 🧭 Scene Description Mode (Gemini)

* Press **Button 2 (GPIO 20)**
* Captures one frame and sends it to Gemini API
* Receives a concise description and reads it aloud

---

## 🧠 Object Detection

* Custom model: Detects lab-specific tools (e.g., robot arms, printers)
* Base model: General-purpose objects (COCO dataset)
* Widths used for distance estimation stored in:

  * `KNOWN_WIDTHS_CUSTOM`
  * `KNOWN_WIDTHS_BASE`

---

## 🧼 Maintenance

* Keep camera and ultrasonic sensor clean
* Avoid use in dusty or wet conditions
* Monitor API limits for Gemini and ElevenLabs
* Always shutdown safely using `sudo shutdown now`

---

## 📩 Project Contributors

**Group 12 – Symbiosis Institute of Technology, Pune**

* Sahran Altaf – [darsahran12@gmail.com](mailto:darsahran12@gmail.com)
* Gunjay Suhalka
* Mayank Ranade
* Raj Shah

**Faculty Guide**: Dr. Arunkumar Bongale

---

## 📚 User Manual Summary

### Requirements

* Raspberry Pi 5
* PiCamera2 Module
* GPIO Buttons on Pins 12 and 20
* Internet Access
* Google Gemini API Key
* ElevenLabs API Key and Voice ID

### Terminal Commands (Before Use)

```bash
cd /home/pi/Desktop/pbl/
sudo pkill -9 python
python main_code.py
```

### Actions

* **Button 1** → Real-time object detection and speech output
* **Button 2** → Scene analysis and descriptive audio

---

## 📄 License

This project is developed for academic use only.
