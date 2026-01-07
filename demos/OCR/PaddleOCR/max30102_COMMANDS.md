================================================================================
                    COPY-PASTE COMMANDS - 15 MIN SETUP
================================================================================

✅ COMMAND 1: Enable I2C (in Putty)
────────────────────────────────────

$ sudo srpi-config

Then navigate:
3 → I3 → Enable I2C → Reboot

Wait 30 seconds for reboot...

================================================================================

✅ COMMAND 2: Verify I2C (in Putty, after reboot)
──────────────────────────────────────────────────

$ i2cdetect -y 1

Expected: See "57" in output
If YES → Continue
If NO → Check wiring!

================================================================================

✅ COMMAND 3: Install i2c-tools (in Putty)
────────────────────────────────────────────

$ sudo apt install -y i2c-tools

================================================================================

✅ COMMAND 4: Activate Existing venv (in Putty)
─────────────────────────────────────────────────

$ source ~/venv_ocr/bin/activate

(You should see (venv_ocr) in prompt)

================================================================================

✅ COMMAND 5: Install smbus2 (in Putty)
─────────────────────────────────────────

$ pip install smbus2==0.4.3

================================================================================

✅ COMMAND 6: Clone MAX30102 Library (in Putty)
────────────────────────────────────────────────

$ cd ~/rdk_model_zoo/demos/OCR/PaddleOCR

$ git clone https://github.com/doug-burrell/max30102.git

$ cd max30102

$ pip install -e .

================================================================================

✅ COMMAND 7: Test I2C in Python (in Putty)
─────────────────────────────────────────────

$ python3 << 'EOF'
import smbus2
bus = smbus2.SMBus(1)
try:
    data = bus.read_byte(0x57)
    print(f"[✓] MAX30102 responding: 0x{data:02x}")
except:
    print("[✗] Sensor not responding")
finally:
    bus.close()
EOF

Expected: [✓] MAX30102 responding: 0x...

================================================================================

✅ COMMAND 8: Create Python Script (in VS Code)
────────────────────────────────────────────────

In VS Code:
File → New File

Copy code from: max30102_record_simple.py

Save as: max30102_record.py
Save location: ~/rdk_model_zoo/demos/OCR/PaddleOCR/

================================================================================

✅ COMMAND 9: Run the Recording (in Putty)
────────────────────────────────────────────

$ cd ~/rdk_model_zoo/demos/OCR/PaddleOCR

$ source ~/venv_ocr/bin/activate

$ env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 max30102_record.py

You should see:
==================================================
MAX30102 Heart Rate Recorder
==================================================

[1] Initializing sensor...
[✓] Sensor initialized

[2] Warming up sensor (5 seconds)...

[3] Recording to: max30102_data_20260107_140000.csv
[•] Place finger on sensor
[•] Press Ctrl+C to stop

Sample #0005 | Time: 5s | BPM: Init
Sample #0010 | Time: 10s | BPM: Init
Sample #0015 | Time: 15s | BPM: 72
Sample #0020 | Time: 20s | BPM: 73

WAIT: For 30 seconds until you see actual BPM
PLACE FINGER: On sensor for accurate readings

================================================================================

✅ COMMAND 10: Stop Recording (in Putty)
─────────────────────────────────────────

Press: Ctrl+C

Expected:
[✓] Stopped. File: max30102_data_20260107_140000.csv
[•] Total samples: 40

================================================================================

✅ COMMAND 11: Verify Data (in Putty)
───────────────────────────────────────

$ cat max30102_data_*.csv

Expected Output:
Timestamp,BPM,Status
2026-01-07 14:00:15.123,Init,Stabilizing
2026-01-07 14:00:16.234,Init,Stabilizing
2026-01-07 14:00:17.345,72,Active
2026-01-07 14:00:18.456,73,Active
2026-01-07 14:00:19.567,72,Active

If you see this → SUCCESS! ✓

================================================================================
                    TOTAL TIME: 15-20 MINUTES
================================================================================

Copy-paste each command in order
Follow the steps in the order shown
Don't skip any steps

If error: Check troubleshooting section in FAST_15_MIN_SETUP.txt

Good luck! 🚀