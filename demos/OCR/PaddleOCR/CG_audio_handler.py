#!/usr/bin/env python3
"""
CG_audio_handler.py - Audio Recording and Text-to-Speech Handler

This module handles:
- Recording audio from Jabra USB microphone (INPUT)
- Text-to-Speech using Google Cloud TTS
- Speech-to-Text using Google Cloud STT
- Playing audio through Bluetooth speaker - Bose (OUTPUT)
- Wake word detection for "Kelvin"

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)

Audio Flow:
- INPUT: Jabra USB Microphone (hw:1,0) via arecord
- OUTPUT: Bose Bluetooth Speaker (via PulseAudio paplay)
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple

# Lazy imports for memory efficiency
_tts_client = None
_stt_client = None


def _get_tts_client():
    """Lazy load TTS client to save memory."""
    global _tts_client
    if _tts_client is None:
        from google.cloud import texttospeech
        _tts_client = texttospeech.TextToSpeechClient()
    return _tts_client


def _get_stt_client():
    """Lazy load STT client to save memory."""
    global _stt_client
    if _stt_client is None:
        from google.cloud import speech
        _stt_client = speech.SpeechClient()
    return _stt_client


# ============================================================
# RECORDING - From Jabra USB Microphone
# ============================================================
def _discover_jabra_device() -> str:
    """
    Auto-discover Jabra USB microphone device.
    
    IMPORTANT: Jabra is typically on card 1 (USB), card 0 is usually built-in.
    Only override if we explicitly find Jabra on a different card.
    
    Returns:
        ALSA device string (e.g., 'plughw:1,0') - defaults to card 1
    """
    default_device = "plughw:1,0"  # Jabra USB is typically card 1
    
    try:
        result = subprocess.run(
            ["arecord", "-l"],
            capture_output=True, text=True, timeout=5
        )
        
        output = result.stdout
        print(f"[AUDIO] Available capture devices:\n{output.strip()}")
        
        # Look for Jabra specifically
        for line in output.split('\n'):
            line_lower = line.lower()
            if "jabra" in line_lower:
                # Extract card number: "card 1: Jabra [...]"
                import re
                match = re.search(r'card\s+(\d+)', line)
                if match:
                    card_num = match.group(1)
                    device = f"plughw:{card_num},0"
                    print(f"[AUDIO] Found Jabra on card {card_num}")
                    return device
        
        # If no Jabra found, check for USB audio (usually card 1)
        for line in output.split('\n'):
            line_lower = line.lower()
            if "usb" in line_lower and "card 1" in line_lower:
                print(f"[AUDIO] Using USB audio on card 1")
                return "plughw:1,0"
        
        # Check if card 1 exists at all
        if "card 1:" in output:
            print(f"[AUDIO] Using card 1 (USB typically)")
            return "plughw:1,0"
        
        # Last resort: use card 0
        print(f"[AUDIO] ⚠️ No Jabra/USB found, using card 0")
        return "plughw:0,0"
            
    except Exception as e:
        print(f"[AUDIO] ⚠️ Discovery error: {e}, using default")
    
    return default_device


def _release_audio_device():
    """
    Release audio device by killing any processes holding it.
    This helps avoid 'Device or resource busy' errors.
    """
    try:
        # Kill any existing arecord processes
        subprocess.run(["pkill", "-9", "arecord"], capture_output=True, timeout=2)
    except:
        pass
    
    try:
        # Small delay to ensure device is released
        import time
        time.sleep(0.2)
    except:
        pass


def record_audio(
    output_path: str,
    duration: int = 7,
    device: Optional[str] = None,
    sample_rate: int = 16000,
    channels: int = 1
) -> bool:
    """
    Record audio from Jabra USB microphone using arecord.
    
    Uses 'plughw' instead of 'hw' to avoid PulseAudio device conflicts.
    
    Args:
        output_path: Path to save the WAV file
        duration: Recording duration in seconds
        device: ALSA capture device (default: plughw:1,0)
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        
    Returns:
        True if recording successful, False otherwise
    """
    try:
        from CG_config import JABRA_CAPTURE_DEV
        
        # Convert hw:X,Y to plughw:X,Y to avoid PulseAudio conflicts
        configured_dev = device or JABRA_CAPTURE_DEV
        if configured_dev.startswith("hw:"):
            configured_dev = "plug" + configured_dev  # hw:1,0 -> plughw:1,0
        device = configured_dev
        
        # Auto-discover if needed
        if "1,0" in device:
            discovered = _discover_jabra_device()
            if discovered and discovered != device:
                device = discovered
                print(f"[AUDIO] Using discovered microphone: {device}")
        
        # Release any held audio devices first
        _release_audio_device()
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file if any
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # Try recording with retry logic
        max_retries = 2
        for attempt in range(max_retries + 1):
            # Method 1: Try arecord with plughw (preferred)
            cmd = [
                "arecord",
                "-D", device,
                "-f", "S16_LE",
                "-r", str(sample_rate),
                "-c", str(channels),
                "-d", str(duration),
                output_path
            ]
            
            print(f"[AUDIO] 🎤 Recording for {duration} seconds (attempt {attempt + 1})...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
            
            if result.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"[AUDIO] ✅ Recorded: {output_path} ({file_size} bytes)")
                return True
            
            # Check if it's a "device busy" error
            if "busy" in result.stderr.lower() or "resource" in result.stderr.lower():
                print(f"[AUDIO] ⚠️ Device busy, releasing and retrying...")
                _release_audio_device()
                import time
                time.sleep(0.5)
                continue
            else:
                print(f"[AUDIO] ❌ Recording failed: {result.stderr}")
                break
        
        # Method 2: Fallback to PulseAudio parecord if arecord fails
        print("[AUDIO] ⚠️ Trying PulseAudio fallback (parecord)...")
        return _record_audio_pulseaudio(output_path, duration, sample_rate, channels)
            
    except subprocess.TimeoutExpired:
        print("[AUDIO] ❌ Recording timed out")
        return False
    except Exception as e:
        print(f"[AUDIO] ❌ Error: {e}")
        return False


def _record_audio_pulseaudio(
    output_path: str,
    duration: int,
    sample_rate: int = 16000,
    channels: int = 1
) -> bool:
    """
    Record audio using PulseAudio's parecord (fallback method).
    
    This works even when ALSA device is held by PulseAudio.
    """
    try:
        # Find Jabra source in PulseAudio
        source = _discover_pulseaudio_source()
        
        cmd = [
            "parecord",
            "--channels", str(channels),
            "--rate", str(sample_rate),
            "--format", "s16le",
            "--file-format", "wav",
        ]
        
        if source:
            cmd.extend(["--device", source])
        
        cmd.append(output_path)
        
        print(f"[AUDIO] 🎤 Recording via PulseAudio for {duration} seconds...")
        
        # parecord doesn't have a duration flag, so we use timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 1)
        
        # parecord exits when we timeout, which is expected
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            file_size = os.path.getsize(output_path)
            print(f"[AUDIO] ✅ Recorded via PulseAudio: {output_path} ({file_size} bytes)")
            return True
        else:
            print(f"[AUDIO] ❌ PulseAudio recording failed")
            return False
            
    except subprocess.TimeoutExpired:
        # This is expected - we use timeout to stop recording
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            file_size = os.path.getsize(output_path)
            print(f"[AUDIO] ✅ Recorded via PulseAudio: {output_path} ({file_size} bytes)")
            return True
        return False
    except Exception as e:
        print(f"[AUDIO] ❌ PulseAudio error: {e}")
        return False


def _discover_pulseaudio_source() -> Optional[str]:
    """
    Discover Jabra microphone as a PulseAudio source.
    
    Returns:
        PulseAudio source name or None
    """
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sources"],
            capture_output=True, text=True, timeout=5
        )
        
        for line in result.stdout.split('\n'):
            # Look for Jabra or USB input source
            if "jabra" in line.lower() or ("input" in line.lower() and "usb" in line.lower()):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
            # Also check for alsa_input with card 1
            if "alsa_input" in line and "card1" in line.replace(" ", "").replace("_", ""):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
    except:
        pass
    
    return None


# ============================================================
# PLAYBACK - Through Bluetooth Speaker (Bose) - PRIMARY OUTPUT
# ============================================================
def play_audio_bluetooth(audio_path: str, sink: Optional[str] = None) -> bool:
    """
    Play audio through Bluetooth speaker (Bose) using paplay.
    
    This is the PRIMARY output method for Care Giver.
    Auto-discovers Bluetooth sink if configured one is not available.
    
    Args:
        audio_path: Path to WAV file
        sink: PulseAudio sink name (default from config, auto-discovers if needed)
        
    Returns:
        True if playback successful
    """
    try:
        from CG_config import BOSE_SINK
        sink = sink or BOSE_SINK
        
        if not os.path.exists(audio_path):
            print(f"[AUDIO] ❌ File not found: {audio_path}")
            return False
        
        # Try configured sink first
        cmd = ["paplay", "-d", sink, audio_path]
        print(f"[AUDIO] 🔊 Playing through Bluetooth speaker...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return True
        
        # If configured sink failed, try to auto-discover Bluetooth sink
        print(f"[AUDIO] ⚠️ Configured sink failed, auto-discovering Bluetooth...")
        discovered_sink = _discover_bluetooth_sink()
        
        if discovered_sink and discovered_sink != sink:
            cmd = ["paplay", "-d", discovered_sink, audio_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"[AUDIO] ✅ Using discovered sink: {discovered_sink}")
                return True
        
        # Fallback to default
        print(f"[AUDIO] ⚠️ Bluetooth playback failed, trying default...")
        return play_audio_default(audio_path)
        
    except Exception as e:
        print(f"[AUDIO] ❌ Bluetooth playback error: {e}")
        return play_audio_default(audio_path)


def _discover_bluetooth_sink() -> Optional[str]:
    """
    Auto-discover available Bluetooth audio sink.
    
    Returns:
        Bluetooth sink name or None
    """
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sinks"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            if "bluez_sink" in line:
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
    except:
        pass
    return None


def play_audio_default(audio_path: str) -> bool:
    """
    Fallback: Play audio through default PulseAudio sink.
    
    Args:
        audio_path: Path to WAV file
        
    Returns:
        True if playback successful
    """
    try:
        if not os.path.exists(audio_path):
            return False
        
        cmd = ["paplay", audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0
        
    except Exception as e:
        print(f"[AUDIO] ❌ Default playback error: {e}")
        return False


def play_audio_jabra(audio_path: str, device: Optional[str] = None) -> bool:
    """
    Play audio through Jabra headset using aplay (BACKUP option).
    
    Args:
        audio_path: Path to WAV file
        device: ALSA playback device
        
    Returns:
        True if playback successful
    """
    try:
        from CG_config import JABRA_PLAYBACK_DEV
        device = device or JABRA_PLAYBACK_DEV
        
        if not os.path.exists(audio_path):
            print(f"[AUDIO] ❌ File not found: {audio_path}")
            return False
            
        cmd = ["aplay", "-D", device, audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"[AUDIO] ❌ Jabra playback error: {e}")
        return False


def play_audio(audio_path: str, use_bose: bool = True) -> bool:
    """
    Play audio through speaker.
    
    Default: Bluetooth speaker (Bose)
    
    Args:
        audio_path: Path to WAV file
        use_bose: If True (default), use Bluetooth speaker
        
    Returns:
        True if playback successful
    """
    if use_bose:
        return play_audio_bluetooth(audio_path)
    else:
        return play_audio_jabra(audio_path)


def text_to_speech(
    text: str,
    output_path: str,
    language_code: str = "en-US",
    voice_name: str = "en-US-Neural2-J",
    sample_rate: int = 16000
) -> bool:
    """
    Convert text to speech.
    
    Tries Google Cloud TTS first, falls back to gTTS (free) if credentials not available.
    
    Args:
        text: Text to convert to speech
        output_path: Output WAV file path
        language_code: Language code
        voice_name: Voice name (for Google Cloud TTS)
        sample_rate: Output sample rate
        
    Returns:
        True if successful
    """
    # Try Google Cloud TTS first
    if _try_google_cloud_tts(text, output_path, language_code, voice_name, sample_rate):
        return True
    
    # Fallback to gTTS (free, no credentials needed)
    print("[TTS] Trying gTTS fallback...")
    return _try_gtts(text, output_path)


def _try_google_cloud_tts(
    text: str,
    output_path: str,
    language_code: str,
    voice_name: str,
    sample_rate: int
) -> bool:
    """Try Google Cloud TTS (requires credentials)."""
    try:
        from google.cloud import texttospeech
        
        client = _get_tts_client()
        
        # Prepare input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        
        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        # Generate speech
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(response.audio_content)
        
        print(f"[TTS] ✅ Generated (Google Cloud): {output_path}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "credentials" in error_msg.lower():
            print(f"[TTS] ⚠️ Google Cloud credentials not configured")
        else:
            print(f"[TTS] ⚠️ Google Cloud TTS error: {e}")
        return False


def _try_gtts(text: str, output_path: str) -> bool:
    """
    Fallback TTS using gTTS (Google Text-to-Speech - free, no credentials).
    
    Note: gTTS outputs MP3, we need to convert to WAV for consistency.
    """
    try:
        from gtts import gTTS
        import tempfile
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Generate speech (gTTS outputs MP3)
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save as MP3 first
        mp3_path = output_path.replace('.wav', '.mp3')
        if mp3_path == output_path:
            mp3_path = output_path + '.mp3'
        
        tts.save(mp3_path)
        
        # Convert MP3 to WAV using ffmpeg or direct play
        # Try ffmpeg first
        try:
            cmd = ["ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                os.remove(mp3_path)  # Clean up MP3
                print(f"[TTS] ✅ Generated (gTTS): {output_path}")
                return True
        except:
            pass
        
        # If ffmpeg fails, just use MP3 directly (paplay can handle it)
        if os.path.exists(mp3_path):
            # Rename to output path (it's MP3 but should still play)
            if output_path != mp3_path:
                import shutil
                shutil.move(mp3_path, output_path)
            print(f"[TTS] ✅ Generated (gTTS/MP3): {output_path}")
            return True
        
        return False
        
    except ImportError:
        print("[TTS] ❌ gTTS not installed. Install with: pip install gTTS")
        return False
    except Exception as e:
        print(f"[TTS] ❌ gTTS error: {e}")
        return False


def speech_to_text(
    audio_path: str,
    language_code: str = "en-US",
    sample_rate: int = 16000
) -> Tuple[str, float]:
    """
    Convert speech to text.
    
    Tries Google Cloud STT first, falls back to SpeechRecognition library.
    
    Args:
        audio_path: Path to WAV audio file
        language_code: Language code
        sample_rate: Audio sample rate
        
    Returns:
        Tuple of (transcribed_text, confidence)
    """
    # Try Google Cloud STT first
    result = _try_google_cloud_stt(audio_path, language_code, sample_rate)
    if result[0]:  # If we got text
        return result
    
    # Fallback to SpeechRecognition library (free Google API)
    print("[STT] Trying SpeechRecognition fallback...")
    return _try_speech_recognition(audio_path)


def _try_google_cloud_stt(
    audio_path: str,
    language_code: str,
    sample_rate: int
) -> Tuple[str, float]:
    """Try Google Cloud STT (requires credentials)."""
    try:
        from google.cloud import speech
        
        client = _get_stt_client()
        
        # Read audio file
        with open(audio_path, "rb") as f:
            audio_content = f.read()
        
        # Configure audio
        audio = speech.RecognitionAudio(content=audio_content)
        
        # Configure recognition with speech context for wake word
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            enable_automatic_punctuation=True,
            model="default",
            speech_contexts=[
                speech.SpeechContext(
                    phrases=["Kelvin", "Hey Kelvin", "Hi Kelvin", "OK Kelvin", "Calvin", "Kevin"],
                    boost=20.0  # Strongly boost recognition of wake word
                )
            ]
        )
        
        # Perform recognition
        response = client.recognize(config=config, audio=audio)
        
        # Extract transcription
        transcript = ""
        confidence = 0.0
        
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
            confidence = max(confidence, result.alternatives[0].confidence)
        
        transcript = transcript.strip()
        
        if transcript:
            print(f"[STT] ✅ Heard (Google Cloud): '{transcript}' (confidence: {confidence:.2%})")
        else:
            print("[STT] ⚠️ No speech detected")
        
        return transcript, confidence
        
    except Exception as e:
        error_msg = str(e)
        if "credentials" in error_msg.lower():
            print(f"[STT] ⚠️ Google Cloud credentials not configured")
        else:
            print(f"[STT] ⚠️ Google Cloud STT error: {e}")
        return "", 0.0


def _try_speech_recognition(audio_path: str) -> Tuple[str, float]:
    """
    Fallback STT using SpeechRecognition library with Google's free API.
    
    This uses Google's free speech recognition (not Cloud API - no credentials needed).
    Has daily usage limits but works for personal use.
    """
    try:
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        
        # Load audio file
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        
        # Try Google's free API first
        try:
            transcript = recognizer.recognize_google(audio)
            print(f"[STT] ✅ Heard (SpeechRecognition): '{transcript}'")
            return transcript, 0.85  # Estimated confidence
        except sr.UnknownValueError:
            print("[STT] ⚠️ Could not understand audio")
            return "", 0.0
        except sr.RequestError as e:
            print(f"[STT] ⚠️ Google free API error: {e}")
            return "", 0.0
            
    except ImportError:
        print("[STT] ❌ SpeechRecognition not installed. Install with: pip install SpeechRecognition")
        return "", 0.0
    except Exception as e:
        print(f"[STT] ❌ SpeechRecognition error: {e}")
        return "", 0.0


# ============================================================
# WAKE WORD DETECTION - "Kelvin"
# ============================================================
def detect_wake_word(text: str) -> Tuple[bool, str]:
    """
    Check if text contains wake word "Kelvin" and extract the command.
    
    Handles variations: "Kelvin", "Hey Kelvin", "Calvin", "Kevin" (common STT misrecognitions)
    
    Examples:
        "Hey Kelvin read my prescription" -> (True, "read my prescription")
        "Kelvin take a picture" -> (True, "take a picture")
        "Hello there" -> (False, "")
    
    Args:
        text: Transcribed text from STT
        
    Returns:
        Tuple of (wake_word_detected, command_text)
    """
    if not text:
        return False, ""
    
    text_lower = text.lower().strip()
    
    # Wake word patterns (case-insensitive)
    # Include common misrecognitions by speech recognition
    wake_patterns = [
        r'\b(?:hey\s+)?kelvin\b',
        r'\b(?:hey\s+)?calvin\b',
        r'\b(?:hey\s+)?kevin\b',
        r'\b(?:hey\s+)?kelven\b',
        r'\b(?:hi\s+)?kelvin\b',
        r'\b(?:ok\s+)?kelvin\b',
        r'\b(?:okay\s+)?kelvin\b',
    ]
    
    for pattern in wake_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Extract command after wake word
            command = text_lower[match.end():].strip()
            
            # Clean up command (remove leading punctuation/filler words)
            command = re.sub(r'^[,.\s]+', '', command)
            command = re.sub(r'^(and|please|can you|could you|i need you to)\s+', '', command, flags=re.IGNORECASE)
            
            print(f"[WAKE] ✅ Wake word detected! Command: '{command}'")
            return True, command.strip()
    
    return False, ""


def listen_for_wake_word(duration: int = 5) -> Tuple[bool, str]:
    """
    Listen for the wake word "Kelvin" and extract the command.
    
    This is the main entry point for voice input. The system only
    processes commands that start with "Kelvin" or "Hey Kelvin".
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        Tuple of (wake_word_detected, command_text)
    """
    from CG_config import TEMP_AUDIO_INPUT, JABRA_CAPTURE_DEV
    
    input_path = str(TEMP_AUDIO_INPUT)
    
    # Record audio from Jabra microphone
    if record_audio(input_path, duration=duration, device=JABRA_CAPTURE_DEV):
        # Transcribe
        text, confidence = speech_to_text(input_path)
        
        if text:
            # Check for wake word
            detected, command = detect_wake_word(text)
            return detected, command
    
    return False, ""


def speak(text: str, use_bose: bool = True) -> bool:
    """
    Speak text aloud through Bluetooth speaker (default).
    
    Args:
        text: Text to speak
        use_bose: If True (default), use Bluetooth speaker
        
    Returns:
        True if successful
    """
    from CG_config import TEMP_AUDIO_OUTPUT
    
    output_path = str(TEMP_AUDIO_OUTPUT)
    
    # Generate speech
    if text_to_speech(text, output_path):
        # Play through Bluetooth speaker (default)
        return play_audio(output_path, use_bose=use_bose)
    
    return False


def listen(duration: int = 7) -> str:
    """
    Record and transcribe speech (for follow-up, no wake word required).
    
    Use this ONLY for follow-up questions after wake word was already detected.
    For initial input, use listen_for_wake_word() instead.
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        Transcribed text
    """
    from CG_config import TEMP_AUDIO_INPUT, JABRA_CAPTURE_DEV
    
    input_path = str(TEMP_AUDIO_INPUT)
    
    # Record audio from Jabra microphone
    if record_audio(input_path, duration=duration, device=JABRA_CAPTURE_DEV):
        # Transcribe
        text, _ = speech_to_text(input_path)
        return text
    
    return ""


def cleanup_temp_audio():
    """Clean up temporary audio files to free memory."""
    from CG_config import TEMP_DIR
    
    for wav_file in TEMP_DIR.glob("*.wav"):
        try:
            wav_file.unlink()
        except:
            pass


# ============================================================
# AUDIO DEVICE CHECKS
# ============================================================
def check_audio_devices() -> dict:
    """
    Check available audio devices.
    
    Returns:
        Dict with device status
    """
    status = {
        "jabra_capture": False,
        "bluetooth_sink": False,
        "bluetooth_sink_name": None,
    }
    
    # Check Jabra capture device
    try:
        result = subprocess.run(
            ["arecord", "-l"],
            capture_output=True, text=True, timeout=5
        )
        if "Jabra" in result.stdout or "card 1" in result.stdout:
            status["jabra_capture"] = True
    except:
        pass
    
    # Check Bluetooth sink
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sinks"],
            capture_output=True, text=True, timeout=5
        )
        if "bluez_sink" in result.stdout:
            status["bluetooth_sink"] = True
            # Extract sink name
            for line in result.stdout.split('\n'):
                if "bluez_sink" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        status["bluetooth_sink_name"] = parts[1]
                    break
    except:
        pass
    
    return status


# ============================================================
# TEST FUNCTION
# ============================================================
def test_audio_handler():
    """Test audio recording and playback."""
    print("=" * 60)
    print("🎤 Audio Handler Test - Kelvin Wake Word")
    print("=" * 60)
    
    # Check devices
    print("\n[TEST] Checking audio devices...")
    devices = check_audio_devices()
    print(f"  Jabra Microphone: {'✅ Ready' if devices['jabra_capture'] else '❌ Not found'}")
    print(f"  Bluetooth Speaker: {'✅ ' + (devices['bluetooth_sink_name'] or 'Ready') if devices['bluetooth_sink'] else '❌ Not found'}")
    
    # Test wake word detection patterns
    print("\n[TEST] Testing wake word detection patterns...")
    test_phrases = [
        ("Hey Kelvin read my prescription", True, "read my prescription"),
        ("Kelvin take a picture", True, "take a picture"),
        ("Calvin help me please", True, "help me please"),
        ("Kevin what time is it", True, "what time is it"),
        ("Hello there", False, ""),
        ("hey kelvin, please take a picture", True, "take a picture"),
        ("OK Kelvin set an alarm", True, "set an alarm"),
    ]
    
    all_passed = True
    for phrase, expected_detected, expected_cmd in test_phrases:
        detected, command = detect_wake_word(phrase)
        passed = (detected == expected_detected)
        status = "✅" if passed else "❌"
        print(f"  {status} '{phrase}' -> detected={detected}, cmd='{command}'")
        if not passed:
            all_passed = False
    
    print(f"\n  Wake word tests: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    
    # Test TTS + Bluetooth playback
    print("\n[TEST] Testing Text-to-Speech + Bluetooth playback...")
    from CG_config import TEMP_DIR
    test_wav = str(TEMP_DIR / "test_tts.wav")
    
    if text_to_speech("Hello! I am Kelvin, your healthcare assistant. Say Hey Kelvin to talk to me.", test_wav):
        print("[TEST] TTS successful, playing through Bluetooth speaker...")
        if play_audio_bluetooth(test_wav):
            print("[TEST] ✅ Bluetooth playback successful")
        else:
            print("[TEST] ⚠️ Bluetooth playback failed, check connection")
    
    # Test live recording + wake word
    print("\n[TEST] Live test: Say 'Hey Kelvin' followed by a command (5 seconds)...")
    detected, command = listen_for_wake_word(duration=5)
    
    if detected:
        print(f"[TEST] ✅ Wake word detected! Command: '{command}'")
        speak(f"I heard your command: {command}")
    else:
        print("[TEST] ❌ Wake word 'Kelvin' not detected")
        print("[TEST] Remember to say 'Hey Kelvin' before your command")
    
    print("\n" + "=" * 60)
    print("🎤 Audio test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_audio_handler()
