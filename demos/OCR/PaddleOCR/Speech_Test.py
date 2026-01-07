#!/usr/bin/env python3
"""
Speech Test - Standalone TTS and STT Test Script

This script demonstrates:
1. Text-to-Speech (TTS): Convert text to WAV audio file
2. Speech-to-Text (STT): Convert WAV audio file back to text

Uses Google Cloud Platform Text-to-Speech and Speech-to-Text APIs.

Required packages for Ubuntu 22.04:
    sudo apt update
    sudo apt install -y python3-pip ffmpeg
    pip3 install google-cloud-texttospeech google-cloud-speech

Usage:
    python3 Speech_Test.py
"""

import os
import io

# ============================================================
# CONFIGURATION - GCP Credentials
# ============================================================
GCP_PROJECT_ID = "hackathon-472817"

# Set environment variable for GCP authentication
# Option 1: Use Application Default Credentials (run: gcloud auth application-default login)
# Option 2: Set path to service account JSON file
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/service-account.json"

# ============================================================
# DUMMY TEXT FOR TESTING (approximately 5 seconds of speech)
# ============================================================
DUMMY_TEXT = """
Welcome to Care Giver Project, your intelligent caring companion. 
Today we will explore the fascinating world of artificial intelligence 
and discover how machine learning is transforming healthcare. 
Let's begin our exciting journey together!
"""

OUTPUT_WAV_FILE = "speech_test_output.wav"


def text_to_speech(text: str, output_file: str) -> bool:
    """
    Convert text to speech and save as WAV file.
    
    Args:
        text: Text to convert to speech
        output_file: Output WAV file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from google.cloud import texttospeech
        
        # Create TTS client
        client = texttospeech.TextToSpeechClient()
        
        # Set the text input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-J",  # High quality neural voice
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        
        # Configure audio output - LINEAR16 WAV format
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,  # 16kHz for STT compatibility
            speaking_rate=1.0,
            pitch=0.0
        )
        
        # Perform TTS
        print(f"[TTS] Converting text to speech...")
        print(f"[TTS] Text: {text[:100]}...")
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save to WAV file
        with open(output_file, "wb") as f:
            f.write(response.audio_content)
        
        file_size = os.path.getsize(output_file)
        duration_seconds = file_size / (16000 * 2)  # 16kHz, 16-bit mono
        
        print(f"[TTS] ✅ Success! Saved to: {output_file}")
        print(f"[TTS] File size: {file_size} bytes")
        print(f"[TTS] Estimated duration: {duration_seconds:.1f} seconds")
        
        return True
        
    except Exception as e:
        print(f"[TTS] ❌ Error: {e}")
        return False


def speech_to_text(audio_file: str) -> str:
    """
    Convert speech audio file to text.
    
    Args:
        audio_file: Path to WAV audio file
        
    Returns:
        Transcribed text or empty string on error
    """
    try:
        from google.cloud import speech
        
        # Create STT client
        client = speech.SpeechClient()
        
        # Read audio file
        with open(audio_file, "rb") as f:
            audio_content = f.read()
        
        # Configure audio
        audio = speech.RecognitionAudio(content=audio_content)
        
        # Configure recognition settings
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="default",
        )
        
        # Perform STT
        print(f"\n[STT] Converting speech to text...")
        print(f"[STT] Input file: {audio_file}")
        
        response = client.recognize(config=config, audio=audio)
        
        # Extract transcription
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
            confidence = result.alternatives[0].confidence
            print(f"[STT] Confidence: {confidence:.2%}")
        
        transcript = transcript.strip()
        
        if transcript:
            print(f"[STT] ✅ Success!")
            print(f"[STT] Transcription: {transcript}")
        else:
            print(f"[STT] ⚠️  No speech detected in audio")
        
        return transcript
        
    except Exception as e:
        print(f"[STT] ❌ Error: {e}")
        return ""


def main():
    """Main function to run TTS and STT test."""
    print("=" * 60)
    print("🎤 GenLearn AI - Speech Test (TTS + STT)")
    print("=" * 60)
    print(f"\nProject ID: {GCP_PROJECT_ID}")
    print(f"Output file: {OUTPUT_WAV_FILE}")
    print("-" * 60)
    
    # Step 1: Text to Speech
    print("\n📝 STEP 1: Text-to-Speech")
    print("-" * 40)
    tts_success = text_to_speech(DUMMY_TEXT.strip(), OUTPUT_WAV_FILE)
    
    if not tts_success:
        print("\n❌ TTS failed. Cannot proceed with STT.")
        return
    
    # Step 2: Speech to Text
    print("\n🎧 STEP 2: Speech-to-Text")
    print("-" * 40)
    transcription = speech_to_text(OUTPUT_WAV_FILE)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"\n[Original Text]")
    print(DUMMY_TEXT.strip())
    print(f"\n[Transcribed Text]")
    print(transcription if transcription else "(No transcription)")
    
    # Cleanup option
    print("\n" + "-" * 60)
    print(f"💾 Audio file saved: {OUTPUT_WAV_FILE}")
    print("   Delete manually if not needed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
