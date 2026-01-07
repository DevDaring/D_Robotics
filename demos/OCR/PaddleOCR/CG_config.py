#!/usr/bin/env python3
"""
CG_config.py - Configuration and Constants for Care Giver System

This module contains all configuration constants, paths, and settings
for the Care Giver healthcare assistant.

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
# Load .env file from the same directory
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

# ============================================================
# API KEYS (loaded from .env)
# ============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
DATA_DIR = BASE_DIR / "data"
ALARM_FILE = BASE_DIR / "CG_alarms.json"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# ============================================================
# AUDIO CONFIGURATION
# ============================================================
# Jabra USB device (card 1, device 0 based on RDK_X5_commands.txt)
JABRA_CAPTURE_DEV = "hw:1,0"
JABRA_PLAYBACK_DEV = "plughw:1,0"
BOSE_SINK = os.getenv("BOSE_SINK", "bluez_sink.78_2B_64_DD_68_CF.a2dp_sink")

# Audio format settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "S16_LE"
DEFAULT_RECORD_DURATION = 7  # seconds for voice input

# Temp audio files
TEMP_AUDIO_INPUT = TEMP_DIR / "voice_input.wav"
TEMP_AUDIO_OUTPUT = TEMP_DIR / "voice_output.wav"

# ============================================================
# TTS CONFIGURATION
# ============================================================
TTS_LANGUAGE_CODE = "en-US"
TTS_VOICE_NAME = "en-US-Neural2-J"
TTS_SPEAKING_RATE = 1.0
TTS_PITCH = 0.0

# ============================================================
# STT CONFIGURATION
# ============================================================
STT_LANGUAGE_CODE = "en-US"
STT_MODEL = "default"

# ============================================================
# CAMERA CONFIGURATION
# ============================================================
CAMERA_TOPIC = "/image_left_raw"
CAMERA_TIMEOUT_SEC = 10.0
SNAPSHOT_PREFIX = "prescription_"

# ============================================================
# OCR CONFIGURATION
# ============================================================
OCR_LANG = "en"
OCR_USE_ANGLE_CLS = False
OCR_FONT_PATH = str(BASE_DIR / "doc" / "fonts" / "simfang.ttf")

# ============================================================
# GEMINI CONFIGURATION
# ============================================================
GEMINI_MODEL = "gemini-2.5-flash-lite-preview-09-2025"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 256  # Keep responses brief (1-3 lines)

# ============================================================
# INTENT KEYWORDS
# ============================================================
# Keywords for triggering photo capture
CAPTURE_KEYWORDS = [
    "take picture", "take image", "take photo", "capture",
    "take a picture", "take an image", "take a photo",
    "click photo", "click picture", "snap", "photograph"
]

# Keywords for confirming actions
CONFIRM_KEYWORDS = ["yes", "yeah", "yep", "sure", "ok", "okay", "confirm", "do it", "go ahead", "please"]
DENY_KEYWORDS = ["no", "nope", "nah", "don't", "cancel", "stop", "negative"]

# Keywords for setting alarms
ALARM_KEYWORDS = ["alarm", "reminder", "remind", "schedule", "set alarm", "notify"]

# Keywords for health queries
HEALTH_KEYWORDS = ["health", "feeling", "pain", "ache", "symptom", "sick", "unwell", "condition"]

# Keywords for exit
EXIT_KEYWORDS = ["exit", "quit", "bye", "goodbye", "stop", "end", "close"]

# ============================================================
# CONVERSATION PROMPTS
# ============================================================
GREETING_MESSAGE = "Hello! I am Care Giver, your healthcare assistant. How are you feeling today?"

HEALTH_FOLLOWUP = "I understand. Can you please show me your prescription or clinical report? Say 'take picture' when ready."

PRESCRIPTION_PROMPT = "Please hold the prescription or report in front of the camera. Say 'take picture' or 'capture' when you're ready."

CONFIRM_CAPTURE = "I'm ready to capture the image. Please confirm by saying 'yes' to proceed."

CAPTURE_SUCCESS = "Image captured successfully. Let me read the document for you."

OCR_ANALYZING = "Analyzing the document. Please wait a moment."

ALARM_PROMPT = "I found medicine information in your prescription. Would you like me to set reminders for your medicines?"

ALARM_SET_SUCCESS = "Alarm has been set successfully. I will remind you when it's time to take your medicine."

FAREWELL_MESSAGE = "Take care of yourself! Remember to take your medicines on time. Goodbye!"

# ============================================================
# SYSTEM PROMPT FOR GEMINI
# ============================================================
CAREGIVER_SYSTEM_PROMPT = """You are Care Giver, a friendly and professional healthcare assistant.
Your role is to help elderly patients understand their prescriptions and medical reports.

IMPORTANT RULES:
1. Keep ALL responses VERY BRIEF - maximum 1-3 sentences.
2. Be warm, caring, and reassuring.
3. Use simple language that elderly people can understand.
4. If you see medicine names, mention dosage and timing clearly.
5. For medical reports, summarize only the key findings.
6. Always end with a helpful tip or reassurance.
7. If you're unsure about medical advice, suggest consulting a doctor.

You are running on a device with limited memory, so keep responses concise."""

OCR_ANALYSIS_PROMPT = """Based on the following text extracted from a medical document (prescription or report), 
provide a brief summary in 1-3 sentences. Focus on:
- Medicine names and dosages if present
- Key medical findings if it's a report
- Any important instructions

Keep your response conversational and easy to understand for an elderly person.

Extracted text:
{ocr_text}"""

MEDICINE_EXTRACTION_PROMPT = """From the following prescription text, extract medicine names and their timings.
Return ONLY a JSON array of objects with "medicine" and "timing" fields.
If no clear medicine timing is found, return an empty array [].

Example format: [{"medicine": "Paracetamol", "timing": "8:00 AM"}, {"medicine": "Vitamin D", "timing": "9:00 PM"}]

Text:
{ocr_text}"""

# ============================================================
# STATE MACHINE STATES
# ============================================================
class ConversationState:
    GREETING = "greeting"
    HEALTH_CHECK = "health_check"
    WAITING_PRESCRIPTION = "waiting_prescription"
    CONFIRM_CAPTURE = "confirm_capture"
    ANALYZING_OCR = "analyzing_ocr"
    SHOWING_RESULTS = "showing_results"
    ALARM_PROMPT = "alarm_prompt"
    IDLE = "idle"
    EXIT = "exit"
