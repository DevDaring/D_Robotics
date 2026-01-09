#!/usr/bin/env python3
"""
Care_Giver.py - Main Healthcare Assistant Application "Kelvin"

An intelligent healthcare assistant that:
1. Listens for wake word "Kelvin" (e.g., "Hey Kelvin, ...")
2. Engages in voice conversation about health
3. Captures prescription/medical report images on command
4. Uses PaddleOCR to extract text from documents
5. Analyzes content with Gemini AI
6. Sets medicine reminders/alarms

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)

============================================================
HOW TO RUN:
============================================================

Terminal 1 - Start Camera (REQUIRED):
    source /opt/tros/humble/setup.bash
    export ROS_LOCALHOST_ONLY=1
    ros2 daemon stop
    ros2 launch mipi_cam mipi_cam_dual_channel.launch.py

Terminal 2 - Run Kelvin (Care Giver):
    cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
    source ~/venv_ocr/bin/activate
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Care_Giver.py

============================================================
USAGE:
============================================================
- Say "Hey Kelvin" followed by your command
- Example: "Hey Kelvin, read my prescription"
- Example: "Hey Kelvin, take a picture"
- Example: "Hey Kelvin, how are you?"

Audio:
- INPUT: Jabra USB Microphone
- OUTPUT: Bose Bluetooth Speaker

============================================================
"""

import os
import sys
import gc
import time
import signal
from typing import Optional, Tuple
from datetime import datetime

# ============================================================
# MEMORY MANAGEMENT - Critical for 4GB RAM
# ============================================================
def free_memory():
    """Force garbage collection to free memory."""
    gc.collect()


# ============================================================
# SIGNAL HANDLING
# ============================================================
_running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global _running
    print("\n\n[KELVIN] Shutting down gracefully...")
    _running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ============================================================
# MAIN CARE GIVER CLASS - "KELVIN"
# ============================================================
class CareGiver:
    """
    Main Care Giver healthcare assistant "Kelvin".
    
    Wake word activated: User must say "Hey Kelvin" to interact.
    
    Audio Flow:
    - INPUT: Jabra USB Microphone (hw:1,0)
    - OUTPUT: Bose Bluetooth Speaker (via PulseAudio)
    """
    
    def __init__(self, use_voice: bool = True):
        """
        Initialize Kelvin (Care Giver).
        
        Args:
            use_voice: If True, enable voice input/output
        """
        print("=" * 60)
        print("🏥 KELVIN - Healthcare Assistant")
        print("=" * 60)
        print(f"[INIT] Starting initialization...")
        print(f"[INIT] Voice mode: {'Enabled' if use_voice else 'Text-only'}")
        print(f"[INIT] Wake word: 'Hey Kelvin'")
        
        self.use_voice = use_voice
        
        # Conversation state
        self.state = "idle"  # idle, awaiting_confirmation, awaiting_response, awaiting_medicine, awaiting_timing
        self.pending_action = None
        self.last_ocr_text = None
        self.extracted_medicines = []
        self.awaiting_followup = False  # True when we expect response without wake word
        
        # Alarm setting state (for interactive flow)
        self.pending_alarm_medicine = None
        self.pending_alarm_timing = None
        
        # Start alarm monitor
        self._init_alarms()
        
        # Check audio devices
        self._check_audio()
        
        print("[INIT] ✅ Kelvin initialized")
        print("-" * 60)
    
    def _check_audio(self):
        """Check audio devices are available."""
        try:
            from CG_audio_handler import check_audio_devices
            devices = check_audio_devices()
            
            if devices["jabra_capture"]:
                print("[INIT] ✅ Microphone: Jabra USB ready")
            else:
                print("[INIT] ⚠️ Microphone: Jabra not found, check connection")
            
            if devices["bluetooth_sink"]:
                print(f"[INIT] ✅ Speaker: Bluetooth ready ({devices.get('bluetooth_sink_name', 'connected')})")
            else:
                print("[INIT] ⚠️ Speaker: Bluetooth not found, check pairing")
        except Exception as e:
            print(f"[INIT] ⚠️ Audio check failed: {e}")
    
    def _init_alarms(self):
        """Initialize alarm monitoring with caring reminders."""
        try:
            from CG_alarm_handler import start_alarm_monitor, get_caring_alarm_message
            
            def on_alarm(alarm):
                """Callback when alarm triggers - uses caring messages."""
                message = get_caring_alarm_message(alarm)
                print(f"\n⏰ [ALARM] {message}")
                self.speak(message)
            
            start_alarm_monitor(on_alarm, check_interval=30)
            print("[INIT] ✅ Alarm monitor started")
        except Exception as e:
            print(f"[INIT] ⚠️ Alarm monitor failed: {e}")
    
    def speak(self, text: str):
        """
        Output text via Bluetooth speaker (TTS) and print to console.
        
        Args:
            text: Text to speak
        """
        print(f"\n🤖 Kelvin: {text}")
        
        if self.use_voice:
            try:
                from CG_audio_handler import speak
                speak(text)  # Defaults to Bluetooth speaker
            except Exception as e:
                print(f"[TTS] ⚠️ Speech output error: {e}")
    
    def listen_for_wake_word(self, duration: int = 5) -> Tuple[bool, str]:
        """
        Listen for wake word "Kelvin" and extract command.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Tuple of (wake_word_detected, command_text)
        """
        if not self.use_voice:
            return False, ""
        
        try:
            from CG_audio_handler import listen_for_wake_word
            return listen_for_wake_word(duration=duration)
        except Exception as e:
            print(f"[LISTEN] ⚠️ Error: {e}")
            return False, ""
    
    def listen_for_response(self, duration: int = 7) -> str:
        """
        Listen for response (no wake word required - for follow-up).
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Transcribed text
        """
        if not self.use_voice:
            return ""
        
        try:
            from CG_audio_handler import listen
            return listen(duration=duration)
        except Exception as e:
            print(f"[LISTEN] ⚠️ Error: {e}")
            return ""
    
    def get_input(self, require_wake_word: bool = True) -> str:
        """
        Get user input via voice or text.
        
        Text input always takes priority if provided.
        Voice input requires wake word "Kelvin" unless awaiting followup.
        
        Args:
            require_wake_word: If True, voice must start with "Hey Kelvin"
            
        Returns:
            User command/input text
        """
        import sys
        import select
        import threading
        
        # Show prompt based on state
        if require_wake_word:
            print(f"\n💬 Say 'Hey Kelvin' + command, or type: ", end="", flush=True)
        else:
            print(f"\n💬 Listening for your response (or type): ", end="", flush=True)
        
        # Check for text input first using non-blocking approach
        text_input = ""
        text_ready = threading.Event()
        
        def read_stdin():
            nonlocal text_input
            try:
                # Check if there's data available (works on Linux)
                import select as sel
                if sel.select([sys.stdin], [], [], 0.1)[0]:
                    text_input = sys.stdin.readline().strip()
                    if text_input:
                        text_ready.set()
            except Exception:
                pass
        
        # Try to read text input (brief check)
        stdin_thread = threading.Thread(target=read_stdin, daemon=True)
        stdin_thread.start()
        stdin_thread.join(timeout=0.5)  # Very short wait
        
        # If text provided, use it (text takes priority)
        if text_input:
            print(f"\n👤 You (text): {text_input}")
            return text_input
        
        # Otherwise, use voice input
        if self.use_voice:
            if require_wake_word:
                # Listen for wake word
                print("\n🎤 Listening for 'Hey Kelvin'...")
                detected, command = self.listen_for_wake_word(duration=5)
                
                if detected and command:
                    print(f"👤 You: Hey Kelvin, {command}")
                    return command
                elif detected:
                    # Wake word detected but no command
                    self.speak("Yes, I'm listening. What can I help you with?")
                    response = self.listen_for_response(duration=7)
                    if response:
                        print(f"👤 You: {response}")
                        return response
                # No wake word detected - continue listening
                return ""
            else:
                # Follow-up response (no wake word needed)
                print("\n🎤 Listening...")
                response = self.listen_for_response(duration=7)
                if response:
                    print(f"👤 You: {response}")
                return response
        
        return ""
    
    def process_command(self, command: str) -> Tuple[str, bool]:
        """
        Process user command and generate response.
        
        Args:
            command: User's command text (wake word already stripped)
            
        Returns:
            Tuple of (response_text, needs_followup)
            needs_followup: If True, next input doesn't need wake word
        """
        from CG_intent_handler import detect_intent, Intent
        
        intent, confidence = detect_intent(command)
        
        print(f"[INTENT] Detected: {intent.name} (confidence: {confidence:.0%})")
        
        # EXIT intent
        if intent == Intent.EXIT:
            self.state = "exit"
            from CG_config import FAREWELL_MESSAGE
            return FAREWELL_MESSAGE, False
        
        # CAPTURE intent - ALWAYS ask for confirmation before capturing
        if intent == Intent.CAPTURE_IMAGE:
            self.state = "awaiting_confirmation"
            self.pending_action = "capture"
            from CG_config import CONFIRM_CAPTURE
            return CONFIRM_CAPTURE, True  # Needs followup (yes/no)
        
        # CONFIRM - handle pending action
        if intent == Intent.CONFIRM and self.pending_action:
            return self._handle_confirmation()
        
        # DENY - cancel pending action
        if intent == Intent.DENY and self.pending_action:
            self.pending_action = None
            self.state = "idle"
            return "Okay, cancelled. Say Hey Kelvin when you need me.", False
        
        # CHECK ALARMS
        if intent == Intent.CHECK_ALARMS:
            from CG_alarm_handler import format_alarm_list
            return format_alarm_list(), False
        
        # SET ALARM - Interactive conversational flow
        if intent == Intent.SET_ALARM:
            return self._handle_set_alarm_intent(command)
        
        # Handle alarm follow-up states
        if self.state == "awaiting_medicine":
            return self._handle_medicine_input(command)
        
        if self.state == "awaiting_timing":
            return self._handle_timing_input(command)
        
        # GREETING
        if intent == Intent.GREETING:
            return "Hello! I'm Kelvin. I can help you read prescriptions and set medicine reminders. How can I help?", False
        
        # THANKS
        if intent == Intent.THANKS:
            return "You're welcome! Say Hey Kelvin if you need anything else.", False
        
        # HELP
        if intent == Intent.HELP:
            return "Say Hey Kelvin take picture to capture a prescription. I'll read it and can set medicine reminders for you.", False
        
        # HEALTH UPDATE - respond with empathy
        if intent == Intent.HEALTH_UPDATE:
            from CG_gemini_handler import get_health_response
            response = get_health_response(command)
            return response, False
        
        # Default - use Gemini for general questions
        from CG_gemini_handler import get_brief_response
        return get_brief_response(command), False
    
    def _handle_confirmation(self) -> Tuple[str, bool]:
        """
        Handle confirmed pending actions.
        
        Returns:
            Tuple of (response_text, needs_followup)
        """
        action = self.pending_action
        self.pending_action = None
        self.state = "idle"
        
        if action == "capture":
            return self._capture_and_analyze()
        
        if action == "set_alarms":
            return self._set_medicine_alarms()
        
        return "Action completed.", False
    
    def _capture_and_analyze(self) -> Tuple[str, bool]:
        """
        Capture image and perform OCR analysis.
        
        Returns:
            Tuple of (response_text, needs_followup)
        """
        from CG_config import CAPTURE_SUCCESS, OCR_ANALYZING
        
        self.speak(CAPTURE_SUCCESS)
        
        # Capture image
        print("\n[CAPTURE] Taking photo...")
        
        try:
            from CG_camera_handler import capture_image_subprocess
            
            image_path = capture_image_subprocess()
            
            if not image_path:
                return "I couldn't capture the image. Please make sure the camera is running and try again.", False
            
            print(f"[CAPTURE] ✅ Image saved: {image_path}")
            
        except Exception as e:
            print(f"[CAPTURE] ❌ Error: {e}")
            return "There was an error capturing the image. Please try again.", False
        
        # Perform OCR
        self.speak(OCR_ANALYZING)
        
        try:
            from CG_ocr_handler import extract_text, unload_ocr
            
            ocr_text = extract_text(image_path)
            self.last_ocr_text = ocr_text
            
            # Free OCR memory after use
            unload_ocr()
            free_memory()
            
            if not ocr_text:
                return "I couldn't read any text from the image. Please try with a clearer picture.", False
            
            print(f"\n[OCR] Extracted text:\n{'-'*40}\n{ocr_text}\n{'-'*40}")
            
        except Exception as e:
            print(f"[OCR] ❌ Error: {e}")
            return "There was an error reading the document. Please try again.", False
        
        # Analyze with Gemini
        try:
            from CG_gemini_handler import analyze_prescription, extract_medicines
            
            # Get analysis
            analysis = analyze_prescription(ocr_text)
            
            # Extract medicines for potential alarms
            self.extracted_medicines = extract_medicines(ocr_text)
            
            # Build response
            response = analysis
            
            # If medicines found, offer to set alarms with caring tone
            if self.extracted_medicines:
                self.pending_action = "set_alarms"
                self.state = "awaiting_confirmation"
                
                med_list = ", ".join([m['medicine'] for m in self.extracted_medicines])
                num_meds = len(self.extracted_medicines)
                
                if num_meds == 1:
                    response += f"\n\nI found {med_list} in your prescription. Would you like me to set a reminder so you don't forget to take it?"
                else:
                    response += f"\n\nI found {num_meds} medicines: {med_list}. Would you like me to set reminders for these? I want to make sure you never miss a dose!"
                return response, True  # Needs followup (yes/no)
            
            return response, False
            
        except Exception as e:
            print(f"[GEMINI] ❌ Error: {e}")
            return "I read the document but had trouble analyzing it. The text says: " + ocr_text[:200], False
    
    def _set_medicine_alarms(self) -> Tuple[str, bool]:
        """
        Set alarms for extracted medicines from prescription.
        
        Returns:
            Tuple of (response_text, needs_followup)
        """
        if not self.extracted_medicines:
            return "No medicines to set alarms for. But don't worry, you can tell me anytime! Just say 'set alarm for' followed by the medicine name.", False
        
        try:
            from CG_alarm_handler import add_alarms_from_medicines, format_alarm_list
            
            count, messages = add_alarms_from_medicines(self.extracted_medicines)
            self.extracted_medicines = []
            
            if count > 0:
                meds_summary = ", ".join(messages[:3])  # First 3 for brevity
                if count > 3:
                    meds_summary += f" and {count - 3} more"
                
                response = f"Perfect! I've set {count} reminder{'s' if count > 1 else ''} for you: {meds_summary}. "
                response += "I'll make sure to remind you at the right times. Your health is my priority! 💚"
                
                return response, False
            else:
                return "I couldn't set the alarms. Please try again or tell me the medicine name directly.", False
                
        except Exception as e:
            print(f"[ALARM] ❌ Error: {e}")
            return "There was an error setting the alarms. But don't worry, we can try again!", False
    
    def _handle_set_alarm_intent(self, command: str) -> Tuple[str, bool]:
        """
        Handle SET_ALARM intent with interactive flow.
        
        Parses the command to extract medicine/timing, asks for missing info.
        
        Args:
            command: User's command
            
        Returns:
            Tuple of (response_text, needs_followup)
        """
        from CG_alarm_handler import parse_alarm_command, add_alarm, get_friendly_time, parse_time
        
        # Parse the command
        parsed = parse_alarm_command(command)
        medicine = parsed.get('medicine')
        timing = parsed.get('timing')
        
        print(f"[ALARM] Parsed command - Medicine: {medicine}, Timing: {timing}")
        
        # If we have both, set the alarm directly
        if medicine and timing:
            success, message = add_alarm(medicine, timing)
            return message, False
        
        # If we only have medicine, ask for timing
        if medicine:
            self.pending_alarm_medicine = medicine
            self.state = "awaiting_timing"
            return f"Got it, {medicine}! When would you like me to remind you? You can say things like 'morning', 'after breakfast', '8 AM', or 'before dinner'.", True
        
        # If we only have timing, ask for medicine
        if timing:
            self.pending_alarm_timing = timing
            self.state = "awaiting_medicine"
            return f"Sure, I'll set a reminder for {timing}. Which medicine is it for?", True
        
        # Neither provided - ask for medicine first
        self.state = "awaiting_medicine"
        return "I'd love to help you set a reminder! Which medicine would you like me to remind you about?", True
    
    def _handle_medicine_input(self, command: str) -> Tuple[str, bool]:
        """
        Handle medicine name input during alarm setting.
        
        Args:
            command: User's response with medicine name
            
        Returns:
            Tuple of (response_text, needs_followup)
        """
        from CG_alarm_handler import add_alarm
        from CG_intent_handler import detect_intent, Intent
        
        # Check if user wants to cancel
        intent, _ = detect_intent(command)
        if intent == Intent.DENY or intent == Intent.EXIT:
            self.state = "idle"
            self.pending_alarm_medicine = None
            self.pending_alarm_timing = None
            return "No problem, cancelled. Just say Hey Kelvin whenever you need me!", False
        
        # Clean up the medicine name
        medicine = command.strip().title()
        
        # Remove common prefixes
        import re
        medicine = re.sub(r'^(it\'?s?|the|my|for|i need|i take|i want)\s+', '', medicine, flags=re.IGNORECASE)
        medicine = medicine.strip().title()
        
        # If we already have timing, set the alarm
        if self.pending_alarm_timing:
            timing = self.pending_alarm_timing
            self.pending_alarm_timing = None
            self.state = "idle"
            
            success, message = add_alarm(medicine, timing)
            return message, False
        
        # Store medicine and ask for timing
        self.pending_alarm_medicine = medicine
        self.state = "awaiting_timing"
        return f"Great, {medicine}! When should I remind you? You can say 'morning', 'evening', 'after meals', or a specific time like '8 AM'.", True
    
    def _handle_timing_input(self, command: str) -> Tuple[str, bool]:
        """
        Handle timing input during alarm setting.
        
        Args:
            command: User's response with timing
            
        Returns:
            Tuple of (response_text, needs_followup)
        """
        from CG_alarm_handler import add_alarm
        from CG_intent_handler import detect_intent, Intent
        
        # Check if user wants to cancel
        intent, _ = detect_intent(command)
        if intent == Intent.DENY or intent == Intent.EXIT:
            self.state = "idle"
            self.pending_alarm_medicine = None
            self.pending_alarm_timing = None
            return "No problem, cancelled. Just say Hey Kelvin whenever you need me!", False
        
        timing = command.strip()
        medicine = self.pending_alarm_medicine
        
        # Reset state
        self.pending_alarm_medicine = None
        self.pending_alarm_timing = None
        self.state = "idle"
        
        if not medicine:
            return "Oops, I forgot which medicine. Let's start over - just say 'set alarm for' followed by the medicine name.", False
        
        success, message = add_alarm(medicine, timing)
        return message, False
    
    def run(self):
        """
        Main conversation loop.
        
        Listens for wake word "Kelvin" and processes commands.
        Runs until user says exit/bye or Ctrl+C.
        """
        global _running
        
        # Start with greeting
        from CG_config import GREETING_MESSAGE
        self.speak(GREETING_MESSAGE)
        self.state = "idle"
        
        needs_followup = False  # When True, next input doesn't require wake word
        
        # Main loop
        while _running and self.state != "exit":
            try:
                # Get user input
                if needs_followup:
                    # Awaiting response (yes/no) - no wake word needed
                    command = self.get_input(require_wake_word=False)
                    needs_followup = False
                else:
                    # Normal mode - require wake word
                    command = self.get_input(require_wake_word=True)
                
                if not command:
                    # No valid input received, continue listening
                    continue
                
                # Process command and get response
                response, needs_followup = self.process_command(command)
                self.speak(response)
                
                # Small delay between interactions
                time.sleep(0.3)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")
                self.speak("I encountered an error. Please try again.")
                needs_followup = False
        
        # Cleanup
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources on exit."""
        print("\n[CLEANUP] Shutting down Kelvin...")
        
        try:
            from CG_alarm_handler import stop_alarm_monitor
            stop_alarm_monitor()
        except:
            pass
        
        try:
            from CG_ocr_handler import unload_ocr
            unload_ocr()
        except:
            pass
        
        try:
            from CG_audio_handler import cleanup_temp_audio
            cleanup_temp_audio()
        except:
            pass
        
        try:
            from CG_camera_handler import shutdown_ros2
            shutdown_ros2()
        except:
            pass
        
        free_memory()
        print("[CLEANUP] ✅ Done. Goodbye!")


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    """
    Main entry point for Kelvin Healthcare Assistant.
    
    Usage:
        python Care_Giver.py              # Normal mode (voice + Bluetooth)
        python Care_Giver.py --no-voice   # Text-only mode
        python Care_Giver.py --test       # Run component tests
        python Care_Giver.py --check      # Check audio devices only
    
    Audio Setup:
        - Input: Jabra USB Microphone (hw:1,0)
        - Output: Bose Bluetooth Speaker (via PulseAudio)
    
    Wake Word: "Kelvin" (or "Hey Kelvin", "Hi Kelvin", etc.)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Kelvin - Your Personal Healthcare Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Care_Giver.py              Start Kelvin with voice
  python Care_Giver.py --no-voice   Text-only mode
  python Care_Giver.py --test       Run component tests
  python Care_Giver.py --check      Check audio devices

Wake Word Usage:
  Say "Hey Kelvin, read this prescription" to analyze documents
  Say "Kelvin, what time is it?" for general queries
  Say "Kelvin, set alarm for 9 AM" to create reminders
        """
    )
    parser.add_argument(
        "--no-voice", 
        action="store_true", 
        help="Disable voice input/output (text-only mode)"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run component tests"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check audio devices and exit"
    )
    
    args = parser.parse_args()
    
    # Check audio devices only
    if args.check:
        check_audio_devices()
        return
    
    # Run tests if requested
    if args.test:
        run_tests()
        return
    
    # Check environment
    check_environment()
    
    # Banner
    print("\n" + "=" * 60)
    print("  👋 KELVIN - Your Personal Healthcare Assistant")
    print("=" * 60)
    print("  Wake word: 'Kelvin' (e.g., 'Hey Kelvin, ...')")
    print("  Voice input: Jabra USB Microphone")
    print("  Voice output: Bose Bluetooth Speaker")
    print("  Text input: Type when prompted (priority over voice)")
    print("=" * 60 + "\n")
    
    # Create and run Kelvin
    caregiver = CareGiver(use_voice=not args.no_voice)
    
    try:
        caregiver.run()
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def check_environment():
    """Check that required environment is set up."""
    print("[CHECK] Verifying environment...")
    
    # Check .env file
    from pathlib import Path
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("[CHECK] ⚠️ .env file not found!")
        print("[CHECK] Please create .env file with GEMINI_API_KEY")
        print("[CHECK] See env.md for template")
    
    # Check API key
    from CG_config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        print("[CHECK] ❌ GEMINI_API_KEY not set in .env file!")
        print("[CHECK] Please add your Gemini API key to .env")
        sys.exit(1)
    
    # Check Google credentials
    import os
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not google_creds:
        print("[CHECK] ⚠️ GOOGLE_APPLICATION_CREDENTIALS not set")
        print("[CHECK] Voice features may not work")
    
    print("[CHECK] ✅ Environment OK")


def check_audio_devices():
    """Check audio device availability."""
    print("\n" + "=" * 60)
    print("  🔊 Audio Device Check")
    print("=" * 60)
    
    try:
        from CG_audio_handler import check_audio_devices as check_devices
        check_devices()
    except Exception as e:
        print(f"[CHECK] ❌ Error checking audio: {e}")


def run_tests():
    """Run all component tests."""
    print("=" * 60)
    print("🧪 Running Component Tests")
    print("=" * 60)
    
    tests = [
        ("Intent Handler", "CG_intent_handler", "test_intent_handler"),
        ("Alarm Handler", "CG_alarm_handler", "test_alarm_handler"),
        ("Gemini Handler", "CG_gemini_handler", "test_gemini_handler"),
    ]
    
    for name, module, func in tests:
        print(f"\n{'='*40}")
        print(f"Testing: {name}")
        print(f"{'='*40}")
        
        try:
            mod = __import__(module)
            test_func = getattr(mod, func)
            test_func()
            print(f"✅ {name} - PASSED")
        except Exception as e:
            print(f"❌ {name} - FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 Tests Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
