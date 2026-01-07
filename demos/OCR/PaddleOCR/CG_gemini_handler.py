#!/usr/bin/env python3
"""
CG_gemini_handler.py - Gemini AI Handler for Care Giver

This module handles interactions with Google Gemini 2.5 Flash model
for generating responses and analyzing prescription/medical text.

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)
"""

import json
import re
from typing import Optional, List, Dict, Any

# Global model instance (lazy loaded)
_gemini_model = None
_chat_session = None


def get_gemini_model():
    """
    Get or create Gemini model instance (lazy loading).
    
    Returns:
        GenerativeModel instance or None on error
    """
    global _gemini_model
    
    if _gemini_model is None:
        try:
            import google.generativeai as genai
            from CG_config import (
                GEMINI_API_KEY, GEMINI_MODEL,
                GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS,
                CAREGIVER_SYSTEM_PROMPT
            )
            
            if not GEMINI_API_KEY:
                print("[GEMINI] ❌ API key not configured in .env file")
                return None
            
            # Configure API
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Create model with system instruction
            _gemini_model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "temperature": GEMINI_TEMPERATURE,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": GEMINI_MAX_TOKENS,
                },
                system_instruction=CAREGIVER_SYSTEM_PROMPT
            )
            
            print(f"[GEMINI] ✅ Model initialized: {GEMINI_MODEL}")
            
        except ImportError:
            print("[GEMINI] ❌ google-generativeai not installed")
            print("[GEMINI] Run: pip3 install google-generativeai")
            return None
        except Exception as e:
            print(f"[GEMINI] ❌ Error initializing model: {e}")
            return None
    
    return _gemini_model


def get_chat_session():
    """
    Get or create a chat session for conversational context.
    
    Returns:
        Chat session instance
    """
    global _chat_session
    
    model = get_gemini_model()
    if model is None:
        return None
    
    if _chat_session is None:
        _chat_session = model.start_chat(history=[])
    
    return _chat_session


def reset_chat_session():
    """Reset the chat session to start fresh."""
    global _chat_session
    _chat_session = None
    print("[GEMINI] Chat session reset")


def generate_response(prompt: str, use_chat: bool = True) -> str:
    """
    Generate a response from Gemini.
    
    Args:
        prompt: User prompt or question
        use_chat: If True, use chat session for context
        
    Returns:
        Generated response text
    """
    try:
        if use_chat:
            session = get_chat_session()
            if session is None:
                return "I'm having trouble connecting to my thinking system. Please try again."
            
            response = session.send_message(prompt)
        else:
            model = get_gemini_model()
            if model is None:
                return "I'm having trouble connecting to my thinking system. Please try again."
            
            response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "I couldn't generate a response. Please try again."
            
    except Exception as e:
        print(f"[GEMINI] ❌ Error: {e}")
        return "I encountered an error. Please try again."


def analyze_prescription(ocr_text: str) -> str:
    """
    Analyze OCR text from a prescription and provide summary.
    
    Args:
        ocr_text: Text extracted from prescription image
        
    Returns:
        Brief summary of prescription
    """
    from CG_config import OCR_ANALYSIS_PROMPT
    
    if not ocr_text or ocr_text.strip() == "":
        return "I couldn't read any text from the image. Please try again with a clearer picture."
    
    prompt = OCR_ANALYSIS_PROMPT.format(ocr_text=ocr_text)
    
    return generate_response(prompt, use_chat=False)


def extract_medicines(ocr_text: str) -> List[Dict[str, str]]:
    """
    Extract medicine names and timings from prescription text.
    
    Args:
        ocr_text: Text extracted from prescription
        
    Returns:
        List of dicts with 'medicine' and 'timing' keys
    """
    try:
        from CG_config import MEDICINE_EXTRACTION_PROMPT
        
        if not ocr_text or ocr_text.strip() == "":
            return []
        
        prompt = MEDICINE_EXTRACTION_PROMPT.format(ocr_text=ocr_text)
        
        response = generate_response(prompt, use_chat=False)
        
        # Try to parse JSON from response
        # Look for JSON array in the response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        
        if json_match:
            medicines = json.loads(json_match.group())
            
            # Validate structure
            valid_medicines = []
            for med in medicines:
                if isinstance(med, dict) and 'medicine' in med:
                    valid_medicines.append({
                        'medicine': med.get('medicine', ''),
                        'timing': med.get('timing', 'As prescribed')
                    })
            
            print(f"[GEMINI] Extracted {len(valid_medicines)} medicines")
            return valid_medicines
        
        return []
        
    except json.JSONDecodeError:
        print("[GEMINI] Could not parse medicine data as JSON")
        return []
    except Exception as e:
        print(f"[GEMINI] ❌ Error extracting medicines: {e}")
        return []


def get_health_response(user_input: str) -> str:
    """
    Generate a caring response to health-related input.
    
    Args:
        user_input: User's description of how they feel
        
    Returns:
        Empathetic response
    """
    prompt = f"""The user is describing how they feel. Respond with empathy and care.
Keep response to 1-2 sentences. Be warm and reassuring.
Then gently suggest they can show their prescription or medical report for help.

User says: {user_input}"""
    
    return generate_response(prompt, use_chat=True)


def get_brief_response(user_input: str) -> str:
    """
    Generate a brief conversational response.
    
    Args:
        user_input: User's message
        
    Returns:
        Brief response (1-3 sentences)
    """
    prompt = f"""Respond briefly (1-2 sentences max) to: {user_input}"""
    
    return generate_response(prompt, use_chat=True)


def format_alarm_confirmation(medicines: List[Dict[str, str]]) -> str:
    """
    Format a confirmation message for medicine alarms.
    
    Args:
        medicines: List of medicine dicts
        
    Returns:
        Formatted confirmation message
    """
    if not medicines:
        return "No medicines found to set alarms for."
    
    lines = ["I'll set reminders for:"]
    for med in medicines:
        lines.append(f"• {med['medicine']} at {med['timing']}")
    
    lines.append("\nShall I set these alarms?")
    
    return "\n".join(lines)


# ============================================================
# TEST FUNCTION
# ============================================================
def test_gemini_handler():
    """Test Gemini API functionality."""
    print("=" * 50)
    print("🤖 Gemini Handler Test")
    print("=" * 50)
    
    # Test basic response
    print("\n[TEST] Testing basic response...")
    response = generate_response("Hello, introduce yourself briefly.")
    print(f"Response: {response}")
    
    # Test health response
    print("\n[TEST] Testing health response...")
    response = get_health_response("I'm not feeling well today, having some headache.")
    print(f"Response: {response}")
    
    # Test prescription analysis
    print("\n[TEST] Testing prescription analysis...")
    sample_prescription = """
    Dr. Smith's Clinic
    Patient: John Doe
    Date: 2024-01-15
    
    Rx:
    1. Paracetamol 500mg - Take 1 tablet twice daily after meals
    2. Vitamin D3 1000IU - Take 1 tablet morning with breakfast
    3. Omeprazole 20mg - Take 1 capsule before dinner
    
    Follow up after 1 week
    """
    
    analysis = analyze_prescription(sample_prescription)
    print(f"Analysis: {analysis}")
    
    # Test medicine extraction
    print("\n[TEST] Testing medicine extraction...")
    medicines = extract_medicines(sample_prescription)
    print(f"Medicines: {medicines}")
    
    # Reset session
    reset_chat_session()
    
    print("\n[TEST] Gemini test complete!")


if __name__ == "__main__":
    test_gemini_handler()
