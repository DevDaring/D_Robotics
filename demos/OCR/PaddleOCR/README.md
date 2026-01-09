# Kelvin - Healthcare Assistant for RDK X5

An intelligent healthcare assistant designed for elderly care, featuring wake word activation, voice interaction, prescription OCR analysis, and medicine reminders.

## 🎯 Features

- **Wake Word Activation**: Say "Kelvin" to activate (e.g., "Hey Kelvin, read my prescription")
- **Voice Conversation**: Natural voice interaction about health
- **Prescription OCR**: Capture and read prescriptions using camera
- **AI Analysis**: Gemini 2.5 Flash analyzes medical documents
- **Medicine Reminders**: Automatic alarm scheduling for medications
- **Dual Input**: Voice or text input (text takes priority)
- **Elderly-Friendly**: Brief, clear responses in simple language

## 📋 Requirements

- **Hardware**: RDK X5 Kit (4GB RAM)
- **OS**: rdk-x5-ubuntu22-preinstalled-desktop-3.3.3-arm64.img.xz
- **Audio Input**: Jabra USB Microphone (hw:1,0)
- **Audio Output**: Bose Bluetooth Speaker (via PulseAudio)
- **Camera**: MIPI stereo camera (built-in on RDK X5)

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Navigate to project directory
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR

# Activate virtual environment
source ~/venv_ocr/bin/activate

# Install dependencies (with fallback TTS/STT - no Google Cloud credentials needed)
pip install google-generativeai python-dotenv gTTS SpeechRecognition

# Optional: Install Google Cloud TTS/STT (requires service account credentials)
# pip install google-cloud-texttospeech google-cloud-speech
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

**Note**: The system uses **gTTS** and **SpeechRecognition** by default (free, no credentials).
If you want higher quality Google Cloud TTS/STT, set up a service account:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account.json"
```

### 3. Start Camera (Terminal 1)

```bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 daemon stop
ros2 launch mipi_cam mipi_cam_dual_channel.launch.py
```

### 4. Run Kelvin (Terminal 2)

```bash
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
source ~/venv_ocr/bin/activate
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Care_Giver.py
```

## 🗣️ Wake Word Usage

Kelvin only responds when you say the wake word **"Kelvin"** first:

| Example Phrase | What Happens |
|----------------|--------------|
| "Hey Kelvin, read this prescription" | ✅ Activates and processes command |
| "Kelvin, what time is it?" | ✅ Activates and answers |
| "Hi Kelvin, set alarm for 9 AM" | ✅ Activates and sets alarm |
| "Read this prescription" | ❌ Ignored (no wake word) |

**Note**: Text input always takes priority over voice input.

## 💬 Voice Commands

Once activated with "Kelvin", you can use these commands:

| Command | Action |
|---------|--------|
| "Take picture" / "Capture" / "Read prescription" | Captures prescription image |
| "Yes" / "Confirm" | Confirms pending action |
| "No" / "Cancel" | Cancels pending action |
| "Show alarms" / "My reminders" | Lists scheduled reminders |
| "Exit" / "Goodbye" | Ends the conversation |

### Example Conversation

```
🤖 Kelvin: Hello! I'm Kelvin, your healthcare assistant. Say "Hey Kelvin" followed by your question.

👤 You: Hey Kelvin, how are you?

🤖 Kelvin: I'm here and ready to help! How are you feeling today?

👤 You: Kelvin, I have a prescription to show you

🤖 Kelvin: I can help read your prescription. Should I capture an image now?

👤 You: Yes

🤖 Kelvin: Capturing now... Image captured successfully!
             Analyzing the document...
             Your prescription includes Paracetamol 500mg twice daily after meals.
             Would you like me to set reminders for these medicines?

👤 You: Yes

🤖 Kelvin: Perfect! I've set reminders for your medicines. I'll notify you when it's time.
```

## 📁 File Structure

```
demos/OCR/PaddleOCR/
├── Care_Giver.py          # Main application entry point
├── CG_config.py           # Configuration and constants
├── CG_audio_handler.py    # Voice recording and TTS/STT (wake word detection)
├── CG_camera_handler.py   # Camera capture via ROS2
├── CG_ocr_handler.py      # PaddleOCR text extraction
├── CG_gemini_handler.py   # Gemini AI integration
├── CG_alarm_handler.py    # Medicine reminder system
├── CG_intent_handler.py   # Intent recognition
├── CG_alarms.json         # Alarm storage (auto-created)
├── .env                   # API keys (create from template)
├── .env.template          # Environment variable template
├── env.md                 # Environment setup guide
└── CG_README.md           # This file
```

## 🔧 Command Line Options

```bash
# Run with voice enabled (default)
python3 Care_Giver.py

# Run with text-only input
python3 Care_Giver.py --no-voice

# Check audio devices
python3 Care_Giver.py --check

# Run component tests
python3 Care_Giver.py --test
```

## 🔊 Audio Setup

### Input: Jabra USB Microphone
- Device: `hw:1,0` (ALSA)
- Records via `arecord` command

### Output: Bose Bluetooth Speaker
- Device: `bluez_sink.78_2B_64_DD_68_CF.a2dp_sink`
- Plays via `paplay` (PulseAudio)

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
# Check audio devices
python3 Care_Giver.py --check

# List ALSA devices
arecord -l
aplay -l

# Test Jabra USB microphone recording
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav

# Test Bose Bluetooth playback
paplay -d bluez_sink.78_2B_64_DD_68_CF.a2dp_sink test.wav

# List PulseAudio sinks
pactl list sinks short
```

### Wake Word Not Detected
- Speak clearly: "Hey Kelvin" or "Kelvin"
- Ensure microphone is active (check `arecord -l`)
- Try speaking louder or closer to microphone
- The system also recognizes "Calvin" and "Kevin" as variations

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
