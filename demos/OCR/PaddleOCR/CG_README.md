# Care Giver - Healthcare Assistant for RDK X5

An intelligent healthcare assistant designed for elderly care, featuring voice interaction, prescription OCR analysis, and medicine reminders.

## 🎯 Features

- **Voice Conversation**: Natural voice interaction about health
- **Prescription OCR**: Capture and read prescriptions using camera
- **AI Analysis**: Gemini 2.5 Flash analyzes medical documents
- **Medicine Reminders**: Automatic alarm scheduling for medications
- **Dual Input**: Voice or text input (text takes priority)
- **Elderly-Friendly**: Brief, clear responses in simple language

## 📋 Requirements

- **Hardware**: RDK X5 Kit (4GB RAM)
- **OS**: rdk-x5-ubuntu22-preinstalled-desktop-3.3.3-arm64.img.xz
- **Audio**: Jabra USB headset (or compatible USB audio device)
- **Camera**: MIPI stereo camera (built-in on RDK X5)

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Navigate to project directory
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR

# Activate virtual environment
source ~/venv_ocr/bin/activate

# Install new dependencies
pip install google-generativeai google-cloud-texttospeech google-cloud-speech python-dotenv
```

### 2. Configure API Keys

```bash
# Copy the template
cp .env.template .env

# Edit with your API keys
nano .env
```

Add your Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Start Camera (Terminal 1)

```bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 daemon stop
ros2 launch mipi_cam mipi_cam_dual_channel.launch.py
```

### 4. Run Care Giver (Terminal 2)

```bash
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
source ~/venv_ocr/bin/activate
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Care_Giver.py
```

## 💬 Usage

### Voice Commands

| Command | Action |
|---------|--------|
| "Take picture" / "Capture" | Captures prescription image |
| "Yes" / "Confirm" | Confirms pending action |
| "No" / "Cancel" | Cancels pending action |
| "Show alarms" | Lists scheduled reminders |
| "Exit" / "Goodbye" | Ends the conversation |

### Example Conversation

```
🤖 Care Giver: Hello! I am Care Giver, your healthcare assistant. How are you feeling today?

👤 You: I have a headache and feeling tired

🤖 Care Giver: I'm sorry to hear that. Please take care and rest. Would you like to show me your prescription?

👤 You: Take picture

🤖 Care Giver: I'm ready to capture the image. Please confirm by saying 'yes' to proceed.

👤 You: Yes

🤖 Care Giver: Image captured successfully. Let me read the document for you.
             Analyzing the document...
             Your prescription includes Paracetamol 500mg twice daily after meals.
             Would you like me to set reminders?

👤 You: Yes

🤖 Care Giver: Alarm has been set successfully. I will remind you when it's time.
```

## 📁 File Structure

```
demos/OCR/PaddleOCR/
├── Care_Giver.py          # Main application entry point
├── CG_config.py           # Configuration and constants
├── CG_audio_handler.py    # Voice recording and TTS/STT
├── CG_camera_handler.py   # Camera capture via ROS2
├── CG_ocr_handler.py      # PaddleOCR text extraction
├── CG_gemini_handler.py   # Gemini AI integration
├── CG_alarm_handler.py    # Medicine reminder system
├── CG_intent_handler.py   # Intent recognition
├── CG_alarms.json         # Alarm storage (auto-created)
├── .env                   # API keys (create from template)
├── .env.template          # Environment variable template
├── env.md                 # Environment setup guide
└── requirements.txt       # Python dependencies
```

## 🔧 Command Line Options

```bash
# Run with voice enabled (default)
python3 Care_Giver.py

# Run with text-only input
python3 Care_Giver.py --no-voice

# Use Bose Bluetooth speaker
python3 Care_Giver.py --bose

# Run component tests
python3 Care_Giver.py --test
```

## 🧠 Memory Management

The application is optimized for 4GB RAM:

- **Lazy Loading**: Modules load only when needed
- **OCR Cleanup**: PaddleOCR unloads after use
- **Garbage Collection**: Forced GC after heavy operations
- **Sequential Processing**: One heavy task at a time

## ⚠️ Troubleshooting

### Camera Not Working
```bash
# Check if camera topic exists
source /opt/tros/humble/setup.bash
ros2 topic list | grep image
```

### Audio Issues
```bash
# List audio devices
arecord -l
aplay -l

# Test Jabra recording
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav
aplay -D plughw:1,0 test.wav
```

### API Key Errors
```bash
# Verify .env file
cat .env | grep GEMINI

# Test Gemini connection
python3 -c "from CG_gemini_handler import test_gemini_handler; test_gemini_handler()"
```

### Out of Memory
- Close other applications
- Use `--no-voice` mode to reduce memory usage
- Restart the application between heavy OCR tasks

## 📝 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for intelligent responses
- PaddleOCR for document text extraction
- RDK X5 platform for edge AI capabilities
