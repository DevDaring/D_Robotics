#!/usr/bin/env python3
"""
CG_intent_handler.py - Intent Recognition and Command Parsing

This module handles:
- Recognizing user intents from text (voice or typed)
- Extracting commands and entities
- Routing to appropriate handlers

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)
"""

import re
from enum import Enum
from typing import Tuple, Optional, Dict, Any


class Intent(Enum):
    """User intent categories."""
    CAPTURE_IMAGE = "capture_image"
    CONFIRM = "confirm"
    DENY = "deny"
    SET_ALARM = "set_alarm"
    CHECK_ALARMS = "check_alarms"
    HEALTH_UPDATE = "health_update"
    ASK_QUESTION = "ask_question"
    EXIT = "exit"
    UNKNOWN = "unknown"
    GREETING = "greeting"
    THANKS = "thanks"
    HELP = "help"


def normalize_text(text: str) -> str:
    """
    Normalize text for intent matching.
    
    Args:
        text: Raw input text
        
    Returns:
        Normalized lowercase text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower().strip()
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove common punctuation for matching
    text = re.sub(r'[.,!?;:]', '', text)
    
    return text


def detect_intent(text: str) -> Tuple[Intent, float]:
    """
    Detect the user's intent from their input.
    
    Args:
        text: User input text
        
    Returns:
        Tuple of (Intent, confidence_score)
    """
    from CG_config import (
        CAPTURE_KEYWORDS, CONFIRM_KEYWORDS, DENY_KEYWORDS,
        ALARM_KEYWORDS, HEALTH_KEYWORDS, EXIT_KEYWORDS
    )
    
    normalized = normalize_text(text)
    
    if not normalized:
        return Intent.UNKNOWN, 0.0
    
    # Check for exit intent FIRST (safety)
    for keyword in EXIT_KEYWORDS:
        if keyword in normalized:
            return Intent.EXIT, 0.9
    
    # Check for capture intent - EXPANDED DETECTION
    # This is the most important intent for the healthcare assistant
    capture_detected = False
    
    # Method 1: Check exact keywords
    for keyword in CAPTURE_KEYWORDS:
        if keyword in normalized:
            capture_detected = True
            break
    
    # Method 2: Check for prescription/document + action words
    if not capture_detected:
        doc_words = ["prescription", "medicine", "report", "document", "paper", "label"]
        action_words = ["read", "scan", "show", "see", "check", "take", "capture", "look", "view"]
        
        has_doc = any(word in normalized for word in doc_words)
        has_action = any(word in normalized for word in action_words)
        
        if has_doc and has_action:
            capture_detected = True
        elif has_doc:  # Just saying "prescription" alone might mean capture
            capture_detected = True
    
    # Method 3: Check for camera-related words
    if not capture_detected:
        camera_words = ["camera", "photo", "picture", "image", "pic", "snap", "capture"]
        if any(word in normalized for word in camera_words):
            capture_detected = True
    
    if capture_detected:
        print(f"[INTENT] 📸 Capture intent detected: '{text}'")
        return Intent.CAPTURE_IMAGE, 0.95
    
    # Check for confirm/deny (context-dependent)
    for keyword in CONFIRM_KEYWORDS:
        if normalized == keyword or normalized.startswith(keyword + " "):
            return Intent.CONFIRM, 0.9
    
    for keyword in DENY_KEYWORDS:
        if normalized == keyword or normalized.startswith(keyword + " "):
            return Intent.DENY, 0.85
    
    # Check for alarm-related intents - IMPROVED DETECTION
    alarm_set_patterns = [
        "set alarm", "set reminder", "set a reminder", "set an alarm",
        "remind me", "reminder for", "alarm for",
        "add alarm", "add reminder", "create alarm", "create reminder",
        "need reminder", "want reminder", "need alarm", "want alarm",
        "medicine reminder", "medicine alarm",
    ]
    alarm_check_patterns = ["check alarm", "show alarm", "list alarm", "my alarm", "what alarm", "see alarm"]
    
    for pattern in alarm_check_patterns:
        if pattern in normalized:
            return Intent.CHECK_ALARMS, 0.9
    
    for pattern in alarm_set_patterns:
        if pattern in normalized:
            return Intent.SET_ALARM, 0.9
    
    # Also check for basic alarm keywords with action context
    for keyword in ALARM_KEYWORDS:
        if keyword in normalized:
            if any(w in normalized for w in ["check", "show", "list", "see", "what", "my"]):
                return Intent.CHECK_ALARMS, 0.85
            if any(w in normalized for w in ["set", "add", "create", "remind", "for", "need", "want"]):
                return Intent.SET_ALARM, 0.85
    
    # Check for greetings
    greeting_words = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
    for greeting in greeting_words:
        if normalized.startswith(greeting):
            return Intent.GREETING, 0.8
    
    # Check for thanks
    thanks_words = ["thank", "thanks", "appreciate"]
    for word in thanks_words:
        if word in normalized:
            return Intent.THANKS, 0.8
    
    # Check for help request
    help_words = ["help", "assist", "what can you do", "how do i"]
    for word in help_words:
        if word in normalized:
            return Intent.HELP, 0.8
    
    # Check for health-related content
    for keyword in HEALTH_KEYWORDS:
        if keyword in normalized:
            return Intent.HEALTH_UPDATE, 0.7
    
    # Check for questions
    question_words = ["what", "why", "how", "when", "where", "who", "can you", "could you"]
    for qword in question_words:
        if normalized.startswith(qword):
            return Intent.ASK_QUESTION, 0.6
    
    # Default to health update or question based on length
    if len(normalized.split()) > 3:
        return Intent.HEALTH_UPDATE, 0.5
    
    return Intent.UNKNOWN, 0.3


def extract_entities(text: str, intent: Intent) -> Dict[str, Any]:
    """
    Extract relevant entities from text based on intent.
    
    Args:
        text: User input text
        intent: Detected intent
        
    Returns:
        Dictionary of extracted entities
    """
    entities = {}
    normalized = normalize_text(text)
    
    if intent == Intent.SET_ALARM:
        # Try to extract time
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',
            r'(\d{1,2}\s*(?:am|pm))',
            r'(morning|afternoon|evening|night|breakfast|lunch|dinner)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                entities['time'] = match.group(1)
                break
        
        # Try to extract medicine name (words before "at" or "for")
        med_match = re.search(r'(?:for|reminder for|alarm for)\s+(.+?)(?:\s+at|\s*$)', normalized)
        if med_match:
            entities['medicine'] = med_match.group(1).strip()
    
    return entities


def get_intent_response_hint(intent: Intent) -> str:
    """
    Get a hint about how to respond to an intent.
    
    Args:
        intent: Detected intent
        
    Returns:
        Response hint string
    """
    hints = {
        Intent.CAPTURE_IMAGE: "User wants to capture image. Confirm before capturing.",
        Intent.CONFIRM: "User confirmed. Proceed with pending action.",
        Intent.DENY: "User denied. Cancel pending action and ask what else.",
        Intent.SET_ALARM: "User wants to set alarm. Extract medicine and time.",
        Intent.CHECK_ALARMS: "User wants to see alarms. List current alarms.",
        Intent.HEALTH_UPDATE: "User sharing health info. Respond empathetically.",
        Intent.ASK_QUESTION: "User asking question. Answer briefly.",
        Intent.EXIT: "User wants to exit. Say goodbye.",
        Intent.GREETING: "User greeted. Respond warmly and introduce yourself.",
        Intent.THANKS: "User thanked. Acknowledge and offer more help.",
        Intent.HELP: "User needs help. Explain available features.",
        Intent.UNKNOWN: "Could not determine intent. Ask for clarification.",
    }
    
    return hints.get(intent, "Process user input appropriately.")


def should_wait_for_confirmation(intent: Intent) -> bool:
    """
    Check if the action requires confirmation before proceeding.
    
    Args:
        intent: Detected intent
        
    Returns:
        True if confirmation needed
    """
    # Actions that need confirmation
    confirmation_required = [
        Intent.CAPTURE_IMAGE,
        Intent.SET_ALARM,
    ]
    
    return intent in confirmation_required


# ============================================================
# TEST FUNCTION
# ============================================================
def test_intent_handler():
    """Test intent detection."""
    print("=" * 50)
    print("🎯 Intent Handler Test")
    print("=" * 50)
    
    test_inputs = [
        "Take a picture",
        "Capture the image please",
        "Yes, go ahead",
        "No, cancel that",
        "Set alarm for paracetamol at 8 AM",
        "Show me my alarms",
        "I'm feeling tired and have a headache",
        "What medicines should I take?",
        "Hello there!",
        "Thank you very much",
        "Help me please",
        "Bye goodbye",
        "random text here",
    ]
    
    for text in test_inputs:
        intent, confidence = detect_intent(text)
        entities = extract_entities(text, intent)
        
        print(f"\nInput: '{text}'")
        print(f"  Intent: {intent.value} (confidence: {confidence:.2f})")
        if entities:
            print(f"  Entities: {entities}")
        print(f"  Hint: {get_intent_response_hint(intent)}")
    
    print("\n[TEST] Intent test complete!")


if __name__ == "__main__":
    test_intent_handler()
