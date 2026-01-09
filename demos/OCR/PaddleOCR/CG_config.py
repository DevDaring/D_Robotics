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
# INPUT: Jabra USB microphone (card 1, device 0)
# Use 'plughw' instead of 'hw' to avoid PulseAudio conflicts
# 'plughw' allows shared access, 'hw' requires exclusive access
JABRA_CAPTURE_DEV = "plughw:1,0"
JABRA_PLAYBACK_DEV = "plughw:1,0"

# OUTPUT: Bose Bluetooth speaker (PRIMARY)
BOSE_SINK = os.getenv("BOSE_SINK", "bluez_sink.78_2B_64_DD_68_CF.a2dp_sink")

# Audio format settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "S16_LE"
DEFAULT_RECORD_DURATION = 7  # seconds for voice input
WAKE_WORD_LISTEN_DURATION = 5  # seconds for wake word detection

# Temp audio files
TEMP_AUDIO_INPUT = TEMP_DIR / "voice_input.wav"
TEMP_AUDIO_OUTPUT = TEMP_DIR / "voice_output.wav"

# ============================================================
# WAKE WORD CONFIGURATION
# ============================================================
WAKE_WORD = "kelvin"
WAKE_WORD_VARIATIONS = ["kelvin", "calvin", "kevin", "kelven"]  # Common STT misrecognitions
ASSISTANT_NAME = "Kelvin"

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
# IMPORTANT: Keep this list comprehensive - users say many different things!
CAPTURE_KEYWORDS = [
    # Direct capture commands
    "take picture", "take image", "take photo", "capture",
    "take a picture", "take an image", "take a photo",
    "click photo", "click picture", "snap", "photograph",
    "take pic", "click pic", "capture image",
    # "Look at" phrases - very natural way to ask!
    "look at the prescription", "look at prescription",
    "look at the report", "look at report",
    "look at the medicine", "look at medicine",
    "look at this", "look at that", "look at it",
    "look here", "see this", "see that",
    # Prescription-related (most common use case!)
    "read prescription", "read my prescription", "scan prescription",
    "show prescription", "see prescription", "check prescription",
    "read this", "read that", "read it", "scan this", "scan it",
    "read the prescription", "scan the prescription",
    "prescription", "medicine paper", "medical report",
    # Document reading
    "read document", "read paper", "read this paper",
    "scan document", "scan paper", "scan this document",
    "read report", "scan report", "medical document",
    # Camera/photo triggers
    "open camera", "use camera", "camera please",
    "photo please", "picture please", "image please",
    # Short forms
    "pic", "photo", "image", "scan", "read",
]

# Keywords for confirming actions
CONFIRM_KEYWORDS = ["yes", "yeah", "yep", "sure", "ok", "okay", "confirm", "do it", "go ahead", "please"]
DENY_KEYWORDS = ["no", "nope", "nah", "don't", "cancel", "stop", "negative"]

# Keywords for setting alarms
ALARM_KEYWORDS = [
    "alarm", "reminder", "remind", "schedule", "notify",
    "set alarm", "set reminder", "medicine time", "pill time",
    "don't forget", "help me remember"
]

# Keywords for health queries
HEALTH_KEYWORDS = ["health", "feeling", "pain", "ache", "symptom", "sick", "unwell", "condition"]

# Keywords for exit
EXIT_KEYWORDS = ["exit", "quit", "bye", "goodbye", "stop", "end", "close"]

# ============================================================
# CONVERSATION PROMPTS
# ============================================================
GREETING_MESSAGE = "Hello! I am Kelvin, your caring healthcare assistant. I'm here to help you with prescriptions and medicine reminders. Say Hey Kelvin followed by your question or command. How are you feeling today?"

HEALTH_FOLLOWUP = "I understand how you feel. Would you like to show me your prescription or medical report? I can help you understand it better. Say Hey Kelvin take picture when ready."

PRESCRIPTION_PROMPT = "Please hold the prescription or report in front of the camera. I'll read it for you and can set reminders if needed. Say Hey Kelvin take picture when you're ready."

CONFIRM_CAPTURE = "I'm ready to capture the image. Say yes to proceed or no to cancel."

CAPTURE_SUCCESS = "Got it! Let me read the document for you."

OCR_ANALYZING = "Analyzing the document now. Just a moment please."

ALARM_PROMPT = "I found medicine information in your prescription. I can set reminders so you never miss a dose. Would you like me to do that?"

ALARM_SET_SUCCESS = "Wonderful! I've set your medicine reminders. I'll make sure to remind you at the right times. Taking care of you is what I'm here for!"

FAREWELL_MESSAGE = "Take care of yourself! Remember, I'm always here when you need help with your medicines. Stay healthy and goodbye!"

WAKE_WORD_HINT = "Say Hey Kelvin to talk to me. I'm here to help!"

NO_WAKE_WORD_MESSAGE = "I'm listening for Hey Kelvin. Please start your command with Hey Kelvin, and I'll be happy to help!"

# ============================================================
# SYSTEM PROMPT FOR GEMINI
# ============================================================
CAREGIVER_SYSTEM_PROMPT = """You are Kelvin, a friendly and professional healthcare assistant.
Your role is to help elderly patients understand their prescriptions and medical reports.

IMPORTANT RULES:
1. Keep ALL responses VERY BRIEF - maximum 1-3 sentences.
2. Be warm, caring, and reassuring.
3. Use simple language that elderly people can understand.
4. If you see medicine names, mention dosage and timing clearly.
5. For medical reports, summarize only the key findings.
6. Always end with a helpful tip or reassurance.
7. If you're unsure about medical advice, suggest consulting a doctor.
8. Your name is Kelvin. Users activate you by saying "Hey Kelvin".

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
