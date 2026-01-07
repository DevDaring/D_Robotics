#!/usr/bin/env python3
"""
Care_Giver.py - Main Healthcare Assistant Application

An intelligent healthcare assistant that:
1. Engages in voice conversation about health
2. Captures prescription/medical report images on command
3. Uses PaddleOCR to extract text from documents
4. Analyzes content with Gemini AI
5. Sets medicine reminders/alarms

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)

============================================================
HOW TO RUN:
============================================================

Terminal 1 - Start Camera (REQUIRED):
    source /opt/tros/humble/setup.bash
    export ROS_LOCALHOST_ONLY=1
    ros2 daemon stop
    ros2 launch mipi_cam mipi_cam_dual_channel.launch.py

Terminal 2 - Run Care Giver:
    cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
    source ~/venv_ocr/bin/activate
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Care_Giver.py

============================================================
FEATURES:
============================================================
- Voice input via Jabra microphone
- Text input via keyboard
- Text-to-Speech output
- Prescription/Report OCR analysis
- Medicine alarm scheduling
- Brief, elderly-friendly responses

============================================================
"""

import os
import sys
import gc
import time
import threading
import signal
from typing import Optional
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
    print("\n\n[CARE_GIVER] Shutting down gracefully...")
    _running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ============================================================
# MAIN CARE GIVER CLASS
# ============================================================
class CareGiver:
    """
    Main Care Giver healthcare assistant application.
    
    Manages conversation flow, document analysis, and medicine reminders.
    """
    
    def __init__(self, use_voice: bool = True, use_bose: bool = False):
        """
        Initialize Care Giver.
        
        Args:
            use_voice: If True, enable voice input/output
            use_bose: If True, use Bose speaker for output
        """
        print("=" * 60)
        print("🏥 Care Giver - Healthcare Assistant")
        print("=" * 60)
        print(f"[INIT] Starting initialization...")
        print(f"[INIT] Voice mode: {'Enabled' if use_voice else 'Disabled'}")
        
        self.use_voice = use_voice
        self.use_bose = use_bose
        
        # Conversation state
        self.state = "greeting"
        self.pending_action = None
        self.last_ocr_text = None
        self.extracted_medicines = []
        
        # Input buffer for text input
        self.text_input_buffer = ""
        self.voice_input_buffer = ""
        
        # Initialize modules (lazy - will load on first use)
        self._audio_loaded = False
        self._ocr_loaded = False
        self._gemini_loaded = False
        
        # Start alarm monitor
        self._init_alarms()
        
        print("[INIT] ✅ Care Giver initialized")
        print("-" * 60)
    
    def _init_alarms(self):
        """Initialize alarm monitoring."""
        try:
            from CG_alarm_handler import start_alarm_monitor
            
            def on_alarm(alarm):
                """Callback when alarm triggers."""
                message = f"Time to take your {alarm['medicine']}!"
                print(f"\n⏰ [ALARM] {message}")
                self.speak(message)
            
            start_alarm_monitor(on_alarm, check_interval=30)
        except Exception as e:
            print(f"[INIT] ⚠️ Alarm monitor failed: {e}")
    
    def speak(self, text: str):
        """
        Output text via speech (if enabled) and print.
        
        Args:
            text: Text to speak
        """
        print(f"\n🤖 Care Giver: {text}")
        
        if self.use_voice:
            try:
                from CG_audio_handler import speak
                speak(text, use_bose=self.use_bose)
            except Exception as e:
                print(f"[TTS] Error: {e}")
    
    def listen(self, prompt: str = "", timeout: int = 7) -> str:
        """
        Get user input (voice or text).
        
        Text input takes priority if both are provided.
        
        Args:
            prompt: Optional prompt to display
            timeout: Voice recording timeout in seconds
            
        Returns:
            User input text
        """
        if prompt:
            print(f"\n💬 {prompt}")
        
        # Option 1: Check for text input first
        print("\n[INPUT] Type your response (or press Enter to use voice): ", end="", flush=True)
        
        # Use select/timeout for non-blocking input on Linux
        import select
        
        # Wait for text input with timeout
        text_input = ""
        
        try:
            # Simple approach: try to read with timeout
            import sys
            if sys.stdin in select.select([sys.stdin], [], [], 3)[0]:
                text_input = sys.stdin.readline().strip()
        except:
            # Fallback: just get input normally
            try:
                text_input = input().strip()
            except EOFError:
                text_input = ""
        
        # If text input provided, use it
        if text_input:
            print(f"👤 You (text): {text_input}")
            return text_input
        
        # Option 2: Use voice input
        if self.use_voice:
            print("\n🎤 Listening... (speak now)")
            try:
                from CG_audio_handler import listen
                voice_input = listen(duration=timeout)
                
                if voice_input:
                    print(f"👤 You (voice): {voice_input}")
                    return voice_input
                else:
                    print("⚠️ No speech detected. Please try again or type your response.")
            except Exception as e:
                print(f"[STT] Error: {e}")
        
        return ""
    
    def get_input_with_fallback(self, prompt: str = "", timeout: int = 7) -> str:
        """
        Get user input with multiple attempts.
        
        Args:
            prompt: Prompt to display
            timeout: Recording timeout
            
        Returns:
            User input text
        """
        for attempt in range(2):
            user_input = self.listen(prompt if attempt == 0 else "Please try again:", timeout)
            
            if user_input:
                return user_input
            
            if attempt == 0:
                self.speak("I didn't catch that.")
        
        return ""
    
    def process_intent(self, user_input: str) -> str:
        """
        Process user input and determine response.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text
        """
        from CG_intent_handler import detect_intent, Intent, extract_entities
        
        intent, confidence = detect_intent(user_input)
        
        # Handle based on current state and intent
        
        # EXIT intent - always handle
        if intent == Intent.EXIT:
            self.state = "exit"
            from CG_config import FAREWELL_MESSAGE
            return FAREWELL_MESSAGE
        
        # CAPTURE intent
        if intent == Intent.CAPTURE_IMAGE:
            self.state = "confirm_capture"
            self.pending_action = "capture"
            from CG_config import CONFIRM_CAPTURE
            return CONFIRM_CAPTURE
        
        # CONFIRM/DENY - context dependent
        if intent == Intent.CONFIRM and self.pending_action:
            return self._handle_confirmation()
        
        if intent == Intent.DENY and self.pending_action:
            self.pending_action = None
            return "Okay, cancelled. What would you like to do?"
        
        # CHECK ALARMS
        if intent == Intent.CHECK_ALARMS:
            from CG_alarm_handler import format_alarm_list
            return format_alarm_list()
        
        # GREETING
        if intent == Intent.GREETING:
            from CG_config import GREETING_MESSAGE
            return GREETING_MESSAGE
        
        # THANKS
        if intent == Intent.THANKS:
            return "You're welcome! Let me know if you need anything else."
        
        # HELP
        if intent == Intent.HELP:
            return "I can help you read prescriptions. Say 'take picture' when ready to capture. I can also set medicine reminders."
        
        # HEALTH UPDATE - use Gemini
        if intent == Intent.HEALTH_UPDATE:
            from CG_gemini_handler import get_health_response
            response = get_health_response(user_input)
            self.state = "waiting_prescription"
            return response
        
        # Default - use Gemini for general questions
        from CG_gemini_handler import get_brief_response
        return get_brief_response(user_input)
    
    def _handle_confirmation(self) -> str:
        """Handle confirmed pending actions."""
        action = self.pending_action
        self.pending_action = None
        
        if action == "capture":
            return self._capture_and_analyze()
        
        if action == "set_alarms":
            return self._set_medicine_alarms()
        
        return "Action confirmed."
    
    def _capture_and_analyze(self) -> str:
        """Capture image and perform OCR analysis."""
        from CG_config import CAPTURE_SUCCESS, OCR_ANALYZING
        
        self.speak(CAPTURE_SUCCESS)
        
        # Capture image
        print("\n[CAPTURE] Taking photo...")
        
        try:
            from CG_camera_handler import capture_image_subprocess
            
            image_path = capture_image_subprocess()
            
            if not image_path:
                return "I couldn't capture the image. Please make sure the camera is running and try again."
            
            print(f"[CAPTURE] ✅ Image saved: {image_path}")
            
        except Exception as e:
            print(f"[CAPTURE] ❌ Error: {e}")
            return "There was an error capturing the image. Please try again."
        
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
                return "I couldn't read any text from the image. Please try with a clearer picture."
            
            print(f"\n[OCR] Extracted text:\n{'-'*40}\n{ocr_text}\n{'-'*40}")
            
        except Exception as e:
            print(f"[OCR] ❌ Error: {e}")
            return "There was an error reading the document. Please try again."
        
        # Analyze with Gemini
        try:
            from CG_gemini_handler import analyze_prescription, extract_medicines
            
            # Get analysis
            analysis = analyze_prescription(ocr_text)
            
            # Extract medicines for potential alarms
            self.extracted_medicines = extract_medicines(ocr_text)
            
            # Build response
            response = analysis
            
            # If medicines found, offer to set alarms
            if self.extracted_medicines:
                self.pending_action = "set_alarms"
                self.state = "alarm_prompt"
                
                med_list = ", ".join([m['medicine'] for m in self.extracted_medicines])
                response += f"\n\nI found these medicines: {med_list}. Would you like me to set reminders for them?"
            
            return response
            
        except Exception as e:
            print(f"[GEMINI] ❌ Error: {e}")
            return "I read the document but had trouble analyzing it. The text says: " + ocr_text[:200]
    
    def _set_medicine_alarms(self) -> str:
        """Set alarms for extracted medicines."""
        if not self.extracted_medicines:
            return "No medicines to set alarms for."
        
        try:
            from CG_alarm_handler import add_alarms_from_medicines, format_alarm_list
            
            count = add_alarms_from_medicines(self.extracted_medicines)
            self.extracted_medicines = []
            
            if count > 0:
                from CG_config import ALARM_SET_SUCCESS
                return f"{ALARM_SET_SUCCESS}\n\n{format_alarm_list()}"
            else:
                return "Couldn't set the alarms. Please try again."
                
        except Exception as e:
            print(f"[ALARM] ❌ Error: {e}")
            return "There was an error setting the alarms."
    
    def run(self):
        """
        Main conversation loop.
        
        Runs until user exits or Ctrl+C.
        """
        global _running
        
        # Start with greeting
        from CG_config import GREETING_MESSAGE
        self.speak(GREETING_MESSAGE)
        self.state = "health_check"
        
        # Main loop
        while _running and self.state != "exit":
            try:
                # Get user input
                user_input = self.get_input_with_fallback()
                
                if not user_input:
                    continue
                
                # Process and respond
                response = self.process_intent(user_input)
                self.speak(response)
                
                # Small delay between interactions
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")
                self.speak("I encountered an error. Let me try again.")
        
        # Cleanup
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources on exit."""
        print("\n[CLEANUP] Shutting down...")
        
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
        print("[CLEANUP] ✅ Done")


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Care Giver - Healthcare Assistant")
    parser.add_argument("--no-voice", action="store_true", help="Disable voice input/output")
    parser.add_argument("--bose", action="store_true", help="Use Bose Bluetooth speaker")
    parser.add_argument("--test", action="store_true", help="Run component tests")
    
    args = parser.parse_args()
    
    # Run tests if requested
    if args.test:
        run_tests()
        return
    
    # Check environment
    check_environment()
    
    # Create and run Care Giver
    caregiver = CareGiver(
        use_voice=not args.no_voice,
        use_bose=args.bose
    )
    
    try:
        caregiver.run()
    except Exception as e:
        print(f"\n[FATAL] {e}")
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
    
    print("[CHECK] ✅ Environment OK")


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
