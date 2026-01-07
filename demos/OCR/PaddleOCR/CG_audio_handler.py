#!/usr/bin/env python3
"""
CG_audio_handler.py - Audio Recording and Text-to-Speech Handler

This module handles:
- Recording audio from Jabra USB microphone
- Text-to-Speech using Google Cloud TTS
- Speech-to-Text using Google Cloud STT
- Playing audio through Jabra or Bose speaker

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)
"""

import os
import subprocess
import threading
import time
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


def record_audio(
    output_path: str,
    duration: int = 7,
    device: str = "hw:1,0",
    sample_rate: int = 16000,
    channels: int = 1
) -> bool:
    """
    Record audio from Jabra microphone using arecord.
    
    Args:
        output_path: Path to save the WAV file
        duration: Recording duration in seconds
        device: ALSA device (default: hw:1,0 for Jabra)
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        
    Returns:
        True if recording successful, False otherwise
    """
    try:
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file if any
        if os.path.exists(output_path):
            os.remove(output_path)
        
        cmd = [
            "arecord",
            "-D", device,
            "-f", "S16_LE",
            "-r", str(sample_rate),
            "-c", str(channels),
            "-d", str(duration),
            output_path
        ]
        
        print(f"[AUDIO] Recording for {duration} seconds...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
        
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"[AUDIO] ✅ Recorded: {output_path} ({file_size} bytes)")
            return True
        else:
            print(f"[AUDIO] ❌ Recording failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[AUDIO] ❌ Recording timed out")
        return False
    except Exception as e:
        print(f"[AUDIO] ❌ Error: {e}")
        return False


def play_audio_jabra(audio_path: str, device: str = "plughw:1,0") -> bool:
    """
    Play audio through Jabra headset using aplay.
    
    Args:
        audio_path: Path to WAV file
        device: ALSA playback device
        
    Returns:
        True if playback successful
    """
    try:
        if not os.path.exists(audio_path):
            print(f"[AUDIO] ❌ File not found: {audio_path}")
            return False
            
        cmd = ["aplay", "-D", device, audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"[AUDIO] ❌ Playback error: {e}")
        return False


def play_audio_bose(audio_path: str, sink: str = None) -> bool:
    """
    Play audio through Bose Bluetooth speaker using paplay.
    
    Args:
        audio_path: Path to WAV file
        sink: PulseAudio sink name
        
    Returns:
        True if playback successful
    """
    try:
        from CG_config import BOSE_SINK
        sink = sink or BOSE_SINK
        
        if not os.path.exists(audio_path):
            print(f"[AUDIO] ❌ File not found: {audio_path}")
            return False
            
        cmd = ["paplay", "-d", sink, audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"[AUDIO] ❌ Bose playback error: {e}")
        return False


def play_audio(audio_path: str, use_bose: bool = False) -> bool:
    """
    Play audio through available speaker.
    
    Args:
        audio_path: Path to WAV file
        use_bose: If True, use Bose Bluetooth speaker
        
    Returns:
        True if playback successful
    """
    if use_bose:
        return play_audio_bose(audio_path)
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
    Convert text to speech using Google Cloud TTS.
    
    Args:
        text: Text to convert to speech
        output_path: Output WAV file path
        language_code: Language code
        voice_name: Voice name
        sample_rate: Output sample rate
        
    Returns:
        True if successful
    """
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
        
        print(f"[TTS] ✅ Generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"[TTS] ❌ Error: {e}")
        return False


def speech_to_text(
    audio_path: str,
    language_code: str = "en-US",
    sample_rate: int = 16000
) -> Tuple[str, float]:
    """
    Convert speech to text using Google Cloud STT.
    
    Args:
        audio_path: Path to WAV audio file
        language_code: Language code
        sample_rate: Audio sample rate
        
    Returns:
        Tuple of (transcribed_text, confidence)
    """
    try:
        from google.cloud import speech
        
        client = _get_stt_client()
        
        # Read audio file
        with open(audio_path, "rb") as f:
            audio_content = f.read()
        
        # Configure audio
        audio = speech.RecognitionAudio(content=audio_content)
        
        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            enable_automatic_punctuation=True,
            model="default",
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
            print(f"[STT] ✅ Transcribed: '{transcript}' (confidence: {confidence:.2%})")
        else:
            print("[STT] ⚠️ No speech detected")
        
        return transcript, confidence
        
    except Exception as e:
        print(f"[STT] ❌ Error: {e}")
        return "", 0.0


def speak(text: str, use_bose: bool = False) -> bool:
    """
    Convenience function to speak text aloud.
    
    Args:
        text: Text to speak
        use_bose: If True, use Bose speaker
        
    Returns:
        True if successful
    """
    from CG_config import TEMP_AUDIO_OUTPUT
    
    output_path = str(TEMP_AUDIO_OUTPUT)
    
    # Generate speech
    if text_to_speech(text, output_path):
        # Play audio
        return play_audio(output_path, use_bose)
    
    return False


def listen(duration: int = 7) -> str:
    """
    Convenience function to record and transcribe speech.
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        Transcribed text
    """
    from CG_config import TEMP_AUDIO_INPUT, JABRA_CAPTURE_DEV
    
    input_path = str(TEMP_AUDIO_INPUT)
    
    # Record audio
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
# TEST FUNCTION
# ============================================================
def test_audio_handler():
    """Test audio recording and playback."""
    print("=" * 50)
    print("🎤 Audio Handler Test")
    print("=" * 50)
    
    # Test TTS
    print("\n[TEST] Testing Text-to-Speech...")
    from CG_config import TEMP_DIR
    test_wav = str(TEMP_DIR / "test_tts.wav")
    
    if text_to_speech("Hello, I am Care Giver. How are you feeling today?", test_wav):
        print("[TEST] TTS successful, playing audio...")
        play_audio_jabra(test_wav)
    
    # Test recording
    print("\n[TEST] Testing recording (5 seconds)...")
    record_wav = str(TEMP_DIR / "test_record.wav")
    
    if record_audio(record_wav, duration=5):
        print("[TEST] Recording successful, transcribing...")
        text, confidence = speech_to_text(record_wav)
        print(f"[TEST] You said: {text}")
    
    print("\n[TEST] Audio test complete!")


if __name__ == "__main__":
    test_audio_handler()
