# Care Giver - Environment Setup Guide

## Overview

This document explains how to set up the environment variables required for the Care Giver healthcare assistant application.

## Required API Keys

### 1. Gemini API Key (REQUIRED)

The Gemini API key is essential for the AI-powered responses and prescription analysis.

**How to get your Gemini API key:**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Select your project (e.g., `hackathon-472817`)
5. Copy the generated API key

**Placeholder in .env:**
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. GCP Project ID (Optional)

Used for Google Cloud Text-to-Speech and Speech-to-Text services.

**How to find your project ID:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Your project ID is shown in the project selector dropdown

**Placeholder in .env:**
```
GCP_PROJECT_ID=your_project_id_here
```

### 3. Bose Bluetooth Sink (Optional)

If you want to use a Bose Bluetooth speaker for audio output.

**How to find your Bose sink name:**
```bash
# First, pair and connect your Bose speaker via Bluetooth
# Then run:
pactl list short sinks
```

Look for a sink like `bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink`

**Placeholder in .env:**
```
BOSE_SINK=bluez_sink.YOUR_MAC_ADDRESS.a2dp_sink
```

## Setting Up .env File

1. Copy the template:
   ```bash
   cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
   cp .env.template .env
   ```

2. Edit the .env file:
   ```bash
   nano .env
   ```

3. Replace placeholders with your actual values:
   ```
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   GCP_PROJECT_ID=hackathon-472817
   BOSE_SINK=bluez_sink.78_2B_64_DD_68_CF.a2dp_sink
   ```

4. Save and exit (Ctrl+X, Y, Enter in nano)

## Security Notes

⚠️ **IMPORTANT:**
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Keep your API keys private
- Rotate keys if they are accidentally exposed

## Verifying Setup

Run the following to verify your environment is set up correctly:

```bash
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
source ~/venv_ocr/bin/activate
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 -c "from CG_config import GEMINI_API_KEY; print('API Key configured!' if GEMINI_API_KEY else 'Missing API key!')"
```

## Troubleshooting

### "GEMINI_API_KEY not set" Error
- Make sure .env file exists in the correct directory
- Check that the key is not empty
- Ensure there are no extra spaces around the = sign

### TTS/STT Not Working
- Ensure you have set up Google Cloud credentials
- Run: `gcloud auth application-default login`
- Or set: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json`

### Bose Speaker Not Playing
- Make sure Bluetooth is connected: `bluetoothctl info <MAC>`
- Check sink exists: `pactl list short sinks`
- Verify PulseAudio is running: `pulseaudio --check`
