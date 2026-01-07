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
from typing import List, Dict, Optional, Callable

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
    
    Args:
        time_str: Time string
        
    Returns:
        datetime object or None
    """
    time_str = time_str.strip().upper()
    now = datetime.now()
    
    # Handle word-based times
    time_mapping = {
        'MORNING': (8, 0),
        'BREAKFAST': (8, 0),
        'LUNCH': (13, 0),
        'AFTERNOON': (14, 0),
        'EVENING': (18, 0),
        'DINNER': (19, 0),
        'NIGHT': (21, 0),
        'BEDTIME': (22, 0),
    }
    
    for word, (hour, minute) in time_mapping.items():
        if word in time_str:
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Try various time formats
    import re
    
    # Format: "8:00 AM" or "08:00 PM"
    match = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)?', time_str)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)
        
        if period == 'PM' and hour != 12:
            hour += 12
        elif period == 'AM' and hour == 12:
            hour = 0
        
        return now.replace(hour=hour % 24, minute=minute, second=0, microsecond=0)
    
    return None


def add_alarm(
    medicine: str,
    timing: str,
    repeat_daily: bool = True
) -> bool:
    """
    Add a new medicine alarm.
    
    Args:
        medicine: Medicine name
        timing: Time string (e.g., "8:00 AM")
        repeat_daily: If True, alarm repeats daily
        
    Returns:
        True if alarm was added
    """
    alarms = load_alarms()
    
    # Parse time
    alarm_time = parse_time(timing)
    if alarm_time is None:
        print(f"[ALARM] ⚠️ Could not parse time: {timing}, using original")
        time_str = timing
    else:
        time_str = alarm_time.strftime("%H:%M")
    
    # Check for duplicates
    for alarm in alarms:
        if alarm['medicine'].lower() == medicine.lower() and alarm['time'] == time_str:
            print(f"[ALARM] ⚠️ Alarm already exists for {medicine} at {time_str}")
            return False
    
    # Add new alarm
    new_alarm = {
        'id': len(alarms) + 1,
        'medicine': medicine,
        'time': time_str,
        'timing_original': timing,
        'repeat_daily': repeat_daily,
        'enabled': True,
        'created': datetime.now().isoformat()
    }
    
    alarms.append(new_alarm)
    save_alarms(alarms)
    
    print(f"[ALARM] ✅ Added alarm: {medicine} at {time_str}")
    return True


def add_alarms_from_medicines(medicines: List[Dict[str, str]]) -> int:
    """
    Add alarms from a list of medicine dictionaries.
    
    Args:
        medicines: List of dicts with 'medicine' and 'timing' keys
        
    Returns:
        Number of alarms added
    """
    count = 0
    for med in medicines:
        if add_alarm(med['medicine'], med.get('timing', 'Morning')):
            count += 1
    return count


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
    Format all alarms as a readable string.
    
    Returns:
        Formatted alarm list
    """
    alarms = load_alarms()
    
    if not alarms:
        return "No alarms set."
    
    lines = ["Your medicine reminders:"]
    for alarm in alarms:
        status = "✅" if alarm.get('enabled', True) else "❌"
        lines.append(f"  {status} {alarm['medicine']} at {alarm['time']}")
    
    return "\n".join(lines)


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
