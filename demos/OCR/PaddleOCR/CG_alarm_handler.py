#!/usr/bin/env python3
"""
CG_alarm_handler.py - Medicine Alarm/Reminder Handler

This module handles setting, managing, and triggering medicine reminders.
Alarms are stored in a JSON file for persistence across restarts.

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Tuple

# Global alarm thread
_alarm_thread = None
_alarm_running = False
_alarm_callback = None


def get_alarm_file() -> str:
    """Get path to alarm storage file."""
    from CG_config import ALARM_FILE
    return str(ALARM_FILE)


def load_alarms() -> List[Dict]:
    """
    Load alarms from storage file.
    
    Returns:
        List of alarm dictionaries
    """
    alarm_file = get_alarm_file()
    
    if not os.path.exists(alarm_file):
        return []
    
    try:
        with open(alarm_file, 'r') as f:
            alarms = json.load(f)
        return alarms
    except Exception as e:
        print(f"[ALARM] ❌ Error loading alarms: {e}")
        return []


def save_alarms(alarms: List[Dict]) -> bool:
    """
    Save alarms to storage file.
    
    Args:
        alarms: List of alarm dictionaries
        
    Returns:
        True if successful
    """
    try:
        alarm_file = get_alarm_file()
        
        with open(alarm_file, 'w') as f:
            json.dump(alarms, f, indent=2)
        
        print(f"[ALARM] ✅ Saved {len(alarms)} alarms")
        return True
    except Exception as e:
        print(f"[ALARM] ❌ Error saving alarms: {e}")
        return False


def parse_time(time_str: str) -> Optional[datetime]:
    """
    Parse time string to datetime for today.
    
    Supported formats:
    - "8:00 AM", "8:00AM", "08:00 AM"
    - "20:00", "8:00"
    - "morning", "afternoon", "evening", "night"
    - "before breakfast", "after lunch", "before dinner"
    - "twice daily", "three times daily"
    
    Args:
        time_str: Time string
        
    Returns:
        datetime object or None
    """
    if not time_str:
        return None
        
    time_str = time_str.strip().upper()
    now = datetime.now()
    
    # Handle word-based times - comprehensive mapping
    time_mapping = {
        # Morning times
        'MORNING': (8, 0),
        'EARLY MORNING': (6, 0),
        'BREAKFAST': (8, 0),
        'BEFORE BREAKFAST': (7, 30),
        'AFTER BREAKFAST': (9, 0),
        'WITH BREAKFAST': (8, 0),
        # Noon/Lunch times
        'NOON': (12, 0),
        'LUNCH': (13, 0),
        'BEFORE LUNCH': (12, 30),
        'AFTER LUNCH': (14, 0),
        'WITH LUNCH': (13, 0),
        'MIDDAY': (12, 0),
        # Afternoon times
        'AFTERNOON': (15, 0),
        'LATE AFTERNOON': (17, 0),
        # Evening times
        'EVENING': (18, 0),
        'DINNER': (19, 0),
        'BEFORE DINNER': (18, 30),
        'AFTER DINNER': (20, 0),
        'WITH DINNER': (19, 0),
        'SUPPER': (19, 0),
        # Night times
        'NIGHT': (21, 0),
        'BEDTIME': (22, 0),
        'BEFORE BED': (22, 0),
        'BEFORE SLEEP': (22, 0),
        'AT NIGHT': (21, 0),
        # Meal-related
        'BEFORE MEAL': (8, 0),  # Default to breakfast
        'AFTER MEAL': (9, 0),
        'WITH MEAL': (8, 0),
        'EMPTY STOMACH': (7, 0),
        'ON EMPTY STOMACH': (7, 0),
    }
    
    # Check for exact matches first
    for word, (hour, minute) in time_mapping.items():
        if word in time_str:
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Try various time formats
    import re
    
    # Format: "8:00 AM" or "08:00 PM" or "8 AM"
    match = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM|A\.M\.|P\.M\.)?', time_str)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)
        
        if period and ('PM' in period or 'P.M.' in period) and hour != 12:
            hour += 12
        elif period and ('AM' in period or 'A.M.' in period) and hour == 12:
            hour = 0
        
        return now.replace(hour=hour % 24, minute=minute, second=0, microsecond=0)
    
    return None


def get_friendly_time(time_str: str) -> str:
    """
    Convert time to a friendly human-readable format.
    
    Args:
        time_str: Time in HH:MM format
        
    Returns:
        Friendly time string like "8 in the morning"
    """
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        hour = time_obj.hour
        minute = time_obj.minute
        
        # Determine period of day
        if 5 <= hour < 12:
            period = "in the morning"
        elif 12 <= hour < 17:
            period = "in the afternoon"
        elif 17 <= hour < 21:
            period = "in the evening"
        else:
            period = "at night"
        
        # Format time
        if hour > 12:
            hour_12 = hour - 12
        elif hour == 0:
            hour_12 = 12
        else:
            hour_12 = hour
        
        if minute == 0:
            return f"{hour_12} o'clock {period}"
        else:
            return f"{hour_12}:{minute:02d} {period}"
    except:
        return time_str


def add_alarm(
    medicine: str,
    timing: str,
    repeat_daily: bool = True
) -> Tuple[bool, str]:
    """
    Add a new medicine alarm.
    
    Args:
        medicine: Medicine name
        timing: Time string (e.g., "8:00 AM", "morning", "after breakfast")
        repeat_daily: If True, alarm repeats daily
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    alarms = load_alarms()
    
    # Clean up medicine name
    medicine = medicine.strip().title()
    
    # Parse time
    alarm_time = parse_time(timing)
    if alarm_time is None:
        # Default to morning if time can't be parsed
        alarm_time = parse_time("morning")
        time_str = "08:00"
        original_timing = timing or "morning"
    else:
        time_str = alarm_time.strftime("%H:%M")
        original_timing = timing
    
    # Check for duplicates
    for alarm in alarms:
        if alarm['medicine'].lower() == medicine.lower() and alarm['time'] == time_str:
            friendly_time = get_friendly_time(time_str)
            msg = f"You already have a reminder for {medicine} at {friendly_time}. No worries, I'll keep reminding you!"
            print(f"[ALARM] ⚠️ Duplicate: {medicine} at {time_str}")
            return True, msg  # Return True since alarm exists
    
    # Generate unique ID
    max_id = max([a.get('id', 0) for a in alarms], default=0)
    
    # Add new alarm
    new_alarm = {
        'id': max_id + 1,
        'medicine': medicine,
        'time': time_str,
        'timing_original': original_timing,
        'repeat_daily': repeat_daily,
        'enabled': True,
        'created': datetime.now().isoformat()
    }
    
    alarms.append(new_alarm)
    save_alarms(alarms)
    
    friendly_time = get_friendly_time(time_str)
    msg = f"Done! I'll remind you to take {medicine} at {friendly_time} every day. Your health is my priority!"
    print(f"[ALARM] ✅ Added alarm: {medicine} at {time_str}")
    return True, msg


def add_alarms_from_medicines(medicines: List[Dict[str, str]]) -> Tuple[int, List[str]]:
    """
    Add alarms from a list of medicine dictionaries.
    
    Args:
        medicines: List of dicts with 'medicine' and 'timing' keys
        
    Returns:
        Tuple of (count of alarms added, list of summary messages)
    """
    count = 0
    messages = []
    
    for med in medicines:
        medicine_name = med.get('medicine', '').strip()
        timing = med.get('timing', 'Morning')
        
        if not medicine_name:
            continue
            
        success, msg = add_alarm(medicine_name, timing)
        if success:
            count += 1
            friendly_time = get_friendly_time(parse_time(timing).strftime("%H:%M") if parse_time(timing) else "08:00")
            messages.append(f"{medicine_name} at {friendly_time}")
    
    return count, messages


def set_alarm_interactive(
    medicine: str = None,
    timing: str = None
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Interactive alarm setting - returns what info is still needed.
    
    Args:
        medicine: Medicine name (optional)
        timing: Timing (optional)
        
    Returns:
        Tuple of (response_message, missing_field, current_value)
        missing_field is 'medicine', 'timing', or None if complete
    """
    if not medicine:
        return (
            "I'd be happy to set a reminder for you! Which medicine would you like me to remind you about?",
            "medicine",
            None
        )
    
    if not timing:
        return (
            f"Got it, {medicine}. When should I remind you? You can say things like 'morning', 'after breakfast', '8 AM', or 'twice daily'.",
            "timing",
            medicine
        )
    
    # Both provided - set the alarm
    success, message = add_alarm(medicine, timing)
    return (message, None, None)


def remove_alarm(alarm_id: int) -> bool:
    """
    Remove an alarm by ID.
    
    Args:
        alarm_id: Alarm ID to remove
        
    Returns:
        True if alarm was removed
    """
    alarms = load_alarms()
    
    original_count = len(alarms)
    alarms = [a for a in alarms if a.get('id') != alarm_id]
    
    if len(alarms) < original_count:
        save_alarms(alarms)
        print(f"[ALARM] ✅ Removed alarm {alarm_id}")
        return True
    
    return False


def clear_all_alarms() -> bool:
    """Clear all alarms."""
    return save_alarms([])


def get_upcoming_alarms(minutes: int = 60) -> List[Dict]:
    """
    Get alarms that are due within the specified minutes.
    
    Args:
        minutes: Look-ahead window in minutes
        
    Returns:
        List of upcoming alarms
    """
    alarms = load_alarms()
    now = datetime.now()
    upcoming = []
    
    for alarm in alarms:
        if not alarm.get('enabled', True):
            continue
        
        try:
            # Parse alarm time
            alarm_time = datetime.strptime(alarm['time'], "%H:%M")
            alarm_datetime = now.replace(
                hour=alarm_time.hour,
                minute=alarm_time.minute,
                second=0,
                microsecond=0
            )
            
            # If time has passed today, check for tomorrow (for repeating alarms)
            if alarm_datetime < now:
                if alarm.get('repeat_daily', True):
                    alarm_datetime += timedelta(days=1)
                else:
                    continue
            
            # Check if within window
            time_diff = (alarm_datetime - now).total_seconds() / 60
            
            if 0 <= time_diff <= minutes:
                upcoming.append({
                    **alarm,
                    'alarm_datetime': alarm_datetime,
                    'minutes_until': int(time_diff)
                })
        except Exception:
            continue
    
    # Sort by time
    upcoming.sort(key=lambda x: x['alarm_datetime'])
    
    return upcoming


def check_due_alarms() -> List[Dict]:
    """
    Check for alarms that are due right now (within 1 minute window).
    
    Returns:
        List of due alarms
    """
    alarms = load_alarms()
    now = datetime.now()
    due = []
    
    for alarm in alarms:
        if not alarm.get('enabled', True):
            continue
        
        try:
            alarm_time = datetime.strptime(alarm['time'], "%H:%M")
            
            # Check if current time matches alarm time (within 1 minute)
            if (now.hour == alarm_time.hour and 
                now.minute == alarm_time.minute):
                due.append(alarm)
        except Exception:
            continue
    
    return due


def format_alarm_list() -> str:
    """
    Format all alarms as a friendly readable string.
    
    Returns:
        Formatted alarm list with caring tone
    """
    alarms = load_alarms()
    
    if not alarms:
        return "You don't have any medicine reminders set yet. Would you like me to help you set one? Just say 'set alarm for' followed by the medicine name."
    
    lines = ["Here are your medicine reminders. I'll make sure you never miss a dose! 💊"]
    
    # Group by time of day for better readability
    morning = []
    afternoon = []
    evening = []
    night = []
    
    for alarm in alarms:
        if not alarm.get('enabled', True):
            continue
        try:
            hour = int(alarm['time'].split(':')[0])
            friendly_time = get_friendly_time(alarm['time'])
            entry = f"  • {alarm['medicine']} - {friendly_time}"
            
            if 5 <= hour < 12:
                morning.append(entry)
            elif 12 <= hour < 17:
                afternoon.append(entry)
            elif 17 <= hour < 21:
                evening.append(entry)
            else:
                night.append(entry)
        except:
            lines.append(f"  • {alarm['medicine']} at {alarm['time']}")
    
    if morning:
        lines.append("\n🌅 Morning:")
        lines.extend(morning)
    if afternoon:
        lines.append("\n☀️ Afternoon:")
        lines.extend(afternoon)
    if evening:
        lines.append("\n🌆 Evening:")
        lines.extend(evening)
    if night:
        lines.append("\n🌙 Night:")
        lines.extend(night)
    
    lines.append("\nI'm here to help you stay healthy!")
    return "\n".join(lines)


def get_caring_alarm_message(alarm: Dict) -> str:
    """
    Generate a caring, friendly alarm message.
    
    Args:
        alarm: Alarm dictionary
        
    Returns:
        Caring message string
    """
    medicine = alarm.get('medicine', 'your medicine')
    
    # Variety of caring messages
    caring_phrases = [
        f"Time to take your {medicine}! Your health matters to me. 💊",
        f"Gentle reminder: It's time for {medicine}. Taking care of you is my job!",
        f"Hey there! Don't forget your {medicine}. I'm here to keep you healthy!",
        f"Medicine time! Please take your {medicine}. You're doing great staying on schedule!",
        f"Reminder: {medicine} is due now. Remember, I care about your wellbeing!",
    ]
    
    # Use alarm ID to pick a message (varies but consistent for same alarm)
    idx = alarm.get('id', 0) % len(caring_phrases)
    return caring_phrases[idx]


def parse_alarm_command(text: str) -> Dict[str, Optional[str]]:
    """
    Parse a natural language alarm command to extract medicine and timing.
    
    Examples:
        "set alarm for paracetamol at 8 AM" -> {'medicine': 'paracetamol', 'timing': '8 AM'}
        "remind me to take vitamin D in the morning" -> {'medicine': 'vitamin D', 'timing': 'morning'}
        "alarm for aspirin" -> {'medicine': 'aspirin', 'timing': None}
    
    Args:
        text: Natural language command
        
    Returns:
        Dict with 'medicine' and 'timing' keys (values may be None)
    """
    import re
    
    text = text.lower().strip()
    result = {'medicine': None, 'timing': None}
    
    # Remove common prefixes
    prefixes = [
        r'^(hey kelvin,?\s*)?',
        r'^(set\s+)?(an?\s+)?(alarm|reminder)\s+(for\s+)?',
        r'^remind\s+me\s+(to\s+take\s+)?',
        r'^(i\s+need\s+)?(to\s+take\s+)?',
    ]
    
    cleaned = text
    for prefix in prefixes:
        cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
    
    # Common timing patterns
    timing_patterns = [
        r'\s+at\s+(.+)$',
        r'\s+in\s+the\s+(morning|afternoon|evening|night)$',
        r'\s+(morning|afternoon|evening|night|breakfast|lunch|dinner|bedtime)$',
        r'\s+(before|after)\s+(breakfast|lunch|dinner|meal|bed|sleep)$',
        r'\s+every\s+(morning|afternoon|evening|night|day)$',
        r'\s+(\d{1,2}:?\d{0,2}\s*(?:am|pm)?)$',
    ]
    
    # Try to extract timing
    for pattern in timing_patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            result['timing'] = match.group(0).strip()
            # Remove timing from the text to get medicine name
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
            break
    
    # Clean up remaining text as medicine name
    # Remove filler words
    fillers = ['my', 'the', 'a', 'an', 'some', 'please', 'for', 'to take']
    medicine = cleaned
    for filler in fillers:
        medicine = re.sub(rf'\b{filler}\b', '', medicine, flags=re.IGNORECASE)
    
    medicine = ' '.join(medicine.split()).strip()
    
    if medicine:
        result['medicine'] = medicine.title()
    
    # Clean up timing
    if result['timing']:
        result['timing'] = result['timing'].strip(' at in the').strip()
    
    return result


def start_alarm_monitor(callback: Callable[[Dict], None], check_interval: int = 30):
    """
    Start background thread to monitor alarms.
    
    Args:
        callback: Function to call when alarm triggers (receives alarm dict)
        check_interval: How often to check alarms (seconds)
    """
    global _alarm_thread, _alarm_running, _alarm_callback
    
    if _alarm_running:
        print("[ALARM] Monitor already running")
        return
    
    _alarm_callback = callback
    _alarm_running = True
    
    def monitor_loop():
        last_triggered = {}  # Track triggered alarms to avoid duplicates
        
        while _alarm_running:
            try:
                due_alarms = check_due_alarms()
                
                for alarm in due_alarms:
                    alarm_key = f"{alarm['id']}_{datetime.now().strftime('%H:%M')}"
                    
                    if alarm_key not in last_triggered:
                        last_triggered[alarm_key] = True
                        
                        if _alarm_callback:
                            _alarm_callback(alarm)
                
                # Clean old triggers (keep only last hour)
                current_time = datetime.now()
                keys_to_remove = []
                for key in last_triggered:
                    try:
                        time_part = key.split('_')[1]
                        trigger_time = datetime.strptime(time_part, "%H:%M")
                        trigger_datetime = current_time.replace(
                            hour=trigger_time.hour,
                            minute=trigger_time.minute
                        )
                        if (current_time - trigger_datetime).total_seconds() > 3600:
                            keys_to_remove.append(key)
                    except:
                        pass
                
                for key in keys_to_remove:
                    del last_triggered[key]
                
            except Exception as e:
                print(f"[ALARM] Monitor error: {e}")
            
            time.sleep(check_interval)
    
    _alarm_thread = threading.Thread(target=monitor_loop, daemon=True)
    _alarm_thread.start()
    print("[ALARM] ✅ Alarm monitor started")


def stop_alarm_monitor():
    """Stop the alarm monitoring thread."""
    global _alarm_running
    _alarm_running = False
    print("[ALARM] Alarm monitor stopped")


# ============================================================
# TEST FUNCTION
# ============================================================
def test_alarm_handler():
    """Test alarm functionality."""
    print("=" * 50)
    print("⏰ Alarm Handler Test")
    print("=" * 50)
    
    # Clear existing alarms
    print("\n[TEST] Clearing existing alarms...")
    clear_all_alarms()
    
    # Add test alarms
    print("\n[TEST] Adding test alarms...")
    add_alarm("Paracetamol", "8:00 AM")
    add_alarm("Vitamin D", "morning")
    add_alarm("Omeprazole", "7:00 PM")
    
    # List alarms
    print("\n[TEST] Current alarms:")
    print(format_alarm_list())
    
    # Check upcoming
    print("\n[TEST] Upcoming alarms (next 24 hours):")
    upcoming = get_upcoming_alarms(minutes=24*60)
    for alarm in upcoming:
        print(f"  - {alarm['medicine']} in {alarm['minutes_until']} minutes")
    
    # Test monitor (brief)
    print("\n[TEST] Testing alarm monitor (5 seconds)...")
    
    def on_alarm(alarm):
        print(f"[ALARM TRIGGERED] Time to take {alarm['medicine']}!")
    
    start_alarm_monitor(on_alarm, check_interval=1)
    time.sleep(5)
    stop_alarm_monitor()
    
    print("\n[TEST] Alarm test complete!")


if __name__ == "__main__":
    test_alarm_handler()
