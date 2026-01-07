================================================================================
                    MAX30102 + RDK X5 - 15 MINUTE FAST SETUP
                   NO SEPARATE VENV - ADD TO EXISTING SETUP
================================================================================

TIME: 15-20 minutes total
TOOLS: Putty + VS Code already open
ACTION: Copy-paste and run commands

================================================================================
STEP 1: ENABLE I2C (2 minutes) - ON RDK X5 VIA PUTTY
================================================================================

In Putty terminal:

$ sudo srpi-config

NAVIGATE:
1. Go to: 3 Interface Options
2. Go to: I3 Peripheral bus config  
3. Enable: I2C
4. Select: YES to reboot

Wait for reboot (~30 seconds)

Back in Putty after reboot:

$ i2cdetect -y 1

VERIFY: You should see "57" in the output (MAX30102 address)
If you don't see 57: Check your wiring first!

================================================================================
STEP 2: INSTALL I2C TOOLS (1 minute) - IN PUTTY
================================================================================

$ sudo apt install -y i2c-tools

================================================================================
STEP 3: ADD TO EXISTING ENVIRONMENT (2 minutes) - IN PUTTY
================================================================================

Activate your existing venv:

$ source ~/venv_ocr/bin/activate

Install ONLY 2 packages (won't conflict):

$ pip install smbus2==0.4.3

That's it! numpy already in requirements.txt

Verify:

$ python3 << 'EOF'
import smbus2
print("[✓] smbus2 working")
EOF

================================================================================
STEP 4: GET MAX30102 LIBRARY (2 minutes) - IN PUTTY
================================================================================

$ cd ~/rdk_model_zoo/demos/OCR/PaddleOCR

$ git clone https://github.com/doug-burrell/max30102.git

$ cd max30102

$ pip install -e .

Verify:

$ python3 -c "from heartrate_monitor import HeartRateMonitor; print('[✓] Library ready')"

================================================================================
STEP 5: CREATE RECORDING SCRIPT (3 minutes) - IN VS CODE
================================================================================

In VS Code, create new file:

File → New File → Save as: max30102_record.py

Copy code from: max30102_record_simple.py file

Save location: ~/rdk_model_zoo/demos/OCR/PaddleOCR/

================================================================================
STEP 6: TEST I2C IN PYTHON (2 minutes) - IN PUTTY
================================================================================

In Putty, in the OCR/PaddleOCR directory:

$ source ~/venv_ocr/bin/activate

$ python3 << 'EOF'
import smbus2
bus = smbus2.SMBus(1)
try:
    data = bus.read_byte(0x57)
    print(f"[✓] MAX30102 responding: 0x{data:02x}")
except:
    print("[✗] Sensor not found - check wiring!")
finally:
    bus.close()
EOF

EXPECTED: [✓] MAX30102 responding: 0x...

================================================================================
STEP 7: RUN THE SCRIPT (5+ minutes) - IN PUTTY
================================================================================

Navigate to script directory:

$ cd ~/rdk_model_zoo/demos/OCR/PaddleOCR

Activate venv:

$ source ~/venv_ocr/bin/activate

Run the recording:

$ env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 max30102_record.py

WAIT: For "Warming up sensor" message
PLACE FINGER: On the sensor
WAIT: 30 seconds for BPM to show actual value

OUTPUT:
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

STOP: Press Ctrl+C when done

================================================================================
STEP 8: VERIFY DATA (1 minute) - IN PUTTY
================================================================================

$ cat max30102_data_*.csv

EXPECTED OUTPUT:
Timestamp,BPM,Status
2026-01-07 14:00:15.123,Init,Stabilizing
2026-01-07 14:00:16.234,Init,Stabilizing
2026-01-07 14:00:17.345,72,Active
2026-01-07 14:00:18.456,73,Active

If you see this = SUCCESS! ✓

================================================================================
QUICK VERIFICATION CHECKLIST
================================================================================

Before running, check:

[ ] sudo srpi-config → I2C enabled → Rebooted
[ ] i2cdetect -y 1 → Shows "57"
[ ] pip install smbus2 → Done
[ ] git clone max30102 → Done
[ ] max30102_record.py created → In VS Code
[ ] activate venv → source ~/venv_ocr/bin/activate
[ ] Test I2C in Python → [✓] response

If all checked → Go to Step 7!

================================================================================
WIRING (IF NOT ALREADY DONE)
================================================================================

MAX30102 pins → RDK X5 pins:

VCC (Red)    → Pin 1  (3.3V)
GND (Black)  → Pin 6  (GND)
SDA (Green)  → Pin 3  (GPIO2)
SCL (Blue)   → Pin 5  (GPIO3)

Check now - if not wired, do this first!

================================================================================
TROUBLESHOOTING QUICK FIXES (IF ERRORS)
================================================================================

ERROR: "No module named smbus2"
FIX: pip install smbus2==0.4.3

ERROR: "No I2C device found" (i2cdetect shows nothing)
FIX: Check wiring (pins 3, 5, 1, 6)
FIX: Reboot: sudo reboot

ERROR: "Address 0x57 not found"
FIX: Check sensor power LED is ON
FIX: Check wiring is firm

ERROR: "BPM stays 0"
FIX: Normal first 30 seconds - WAIT
FIX: Keep finger on sensor

ERROR: "LD_LIBRARY_PATH conflict"
FIX: Use this command:
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 max30102_record.py

================================================================================
WHAT YOU'LL HAVE IN 15 MINUTES
================================================================================

✓ I2C enabled on RDK X5
✓ smbus2 installed (in existing venv)
✓ MAX30102 library cloned and installed
✓ Recording script ready
✓ First heart rate data recorded
✓ CSV file with timestamps and BPM
✓ NO separate venv (uses existing ~/venv_ocr/)
✓ NO conflicts with existing packages
✓ NO issues with requirements.txt

================================================================================
NEXT STEPS (AFTER 15 MIN)
================================================================================

1. Record more data during different activities
2. Analyze CSV file (Excel, Python, etc.)
3. Optional: Add database storage
4. Optional: Add real-time plotting
5. Optional: Add SpO2 extraction

For now, you have a working MAX30102 sensor! ✓

================================================================================
                        YOU'RE READY TO GO!
                    Total time: 15-20 minutes
================================================================================

Created: January 7, 2026
Purpose: Super fast setup
No separate venv - uses existing