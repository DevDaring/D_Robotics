# Google Cloud TTS/STT Setup Guide for Kelvin Healthcare Assistant

## Quick Setup (5 minutes)

### Step 1: Create Service Account

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select your project (e.g., `hackathon-472817`)
3. Click **"+ CREATE SERVICE ACCOUNT"**
4. Fill in:
   - Name: `kelvin-tts-stt`
   - Description: `Service account for Kelvin TTS and STT`
5. Click **"CREATE AND CONTINUE"**

### Step 2: Grant Permissions

Add these roles:
- **Cloud Text-to-Speech API User** (`roles/texttospeech.user`)
- **Cloud Speech-to-Text API User** (`roles/speech.speechUser`)

Click **"CONTINUE"** → **"DONE"**

### Step 3: Create JSON Key

1. Click on the service account you just created
2. Go to **"KEYS"** tab
3. Click **"ADD KEY"** → **"Create new key"**
4. Select **JSON** format
5. Click **"CREATE"**
6. **Download the JSON file** (save it securely!)

### Step 4: Upload to RDK X5

```bash
# On your PC, copy the JSON to RDK X5:
scp ~/Downloads/hackathon-472817-xxxxx.json sunrise@192.168.1.xxx:~/gcp-credentials.json

# Or use USB drive, etc.
```

### Step 5: Set Environment Variable on RDK X5

```bash
# Add to ~/.bashrc for permanent setup
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/gcp-credentials.json"' >> ~/.bashrc
source ~/.bashrc

# Verify it's set
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should print: /home/sunrise/gcp-credentials.json
```

### Step 6: Enable APIs (if not already)

Go to these URLs and click **"ENABLE"**:
- https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
- https://console.cloud.google.com/apis/library/speech.googleapis.com

### Step 7: Test

```bash
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
source ~/venv_ocr/bin/activate
python3 -c "
from google.cloud import texttospeech
client = texttospeech.TextToSpeechClient()
print('✅ TTS credentials OK!')

from google.cloud import speech
client = speech.SpeechClient()
print('✅ STT credentials OK!')
"
```

---

## One-Line Setup (if you have the JSON file ready)

```bash
# On RDK X5:
export GOOGLE_APPLICATION_CREDENTIALS="/home/sunrise/gcp-credentials.json"

# Make it permanent:
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/home/sunrise/gcp-credentials.json"' >> ~/.bashrc
```

---

## Troubleshooting

### Error: "Your default credentials were not found"
```bash
# Check if the file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Check if variable is set
echo $GOOGLE_APPLICATION_CREDENTIALS

# If empty, set it:
export GOOGLE_APPLICATION_CREDENTIALS="/home/sunrise/gcp-credentials.json"
```

### Error: "Permission denied" or "API not enabled"
- Go to Google Cloud Console
- Enable Text-to-Speech API and Speech-to-Text API
- Check service account has correct roles

### Error: "Invalid JSON"
- Re-download the JSON key file
- Don't edit the JSON file manually

---

## Alternative: Use Free Fallback (No Credentials Needed)

If you don't want to set up GCP credentials, the system automatically uses:
- **gTTS** for text-to-speech (free Google TTS)
- **SpeechRecognition** for speech-to-text (free Google API)

Just install them:
```bash
pip install gTTS SpeechRecognition
```

The code will automatically fall back to these if GCP credentials are not found.
