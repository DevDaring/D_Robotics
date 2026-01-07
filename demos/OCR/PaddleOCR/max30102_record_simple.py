#!/usr/bin/env python3
"""
MAX30102 Heart Rate Monitor - Quick Record (Simple Version)
Works with existing venv - NO conflicts
Created: January 7, 2026
Time: 15 minutes setup
"""

import csv
import time
from datetime import datetime
from heartrate_monitor import HeartRateMonitor

def main():
    print("=" * 50)
    print("MAX30102 Heart Rate Recorder")
    print("=" * 50)
    
    # Initialize sensor
    print("\n[1] Initializing sensor...")
    try:
        hrm = HeartRateMonitor()
        print("[✓] Sensor initialized")
    except Exception as e:
        print(f"[✗] Error: {e}")
        print("    Check: Wiring correct? I2C enabled? Sensor powered?")
        return
    
    # Wait for warmup
    print("\n[2] Warming up sensor (5 seconds)...")
    time.sleep(5)
    
    # Create CSV file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"max30102_data_{timestamp}.csv"
    
    print(f"\n[3] Recording to: {csv_file}")
    print("[•] Place finger on sensor")
    print("[•] Press Ctrl+C to stop\n")
    
    try:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Timestamp', 'BPM', 'Status'])
            writer.writeheader()
            
            sample = 0
            start = time.time()
            
            while True:
                sample += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                bpm = hrm.bpm if hrm.bpm > 0 else "Init"
                status = "Active" if hrm.bpm > 0 else "Stabilizing"
                
                writer.writerow({
                    'Timestamp': now,
                    'BPM': bpm,
                    'Status': status
                })
                f.flush()
                
                if sample % 5 == 0:
                    elapsed = time.time() - start
                    print(f"Sample #{sample:04d} | Time: {elapsed:.0f}s | BPM: {bpm} | {status}")
                
                time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n\n[✓] Recording stopped")
        print(f"[✓] File saved: {csv_file}")
        print(f"[•] Total samples: {sample}")
    
    finally:
        print("[•] Done!")

if __name__ == "__main__":
    main()