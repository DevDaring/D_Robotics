================================================================================
        MAX30102 + RDK X5 - ULTRA QUICK CHEAT SHEET (1 PAGE)
================================================================================

TIME: 15-20 minutes
NO separate venv - uses existing ~/venv_ocr/

================================================================================
PRE-REQUISITE: WIRING (Done already? Skip this)
================================================================================

MAX30102 pins → RDK X5 pins:
  VCC (Red)    → Pin 1  (3.3V)
  GND (Black)  → Pin 6  (GND)
  SDA (Green)  → Pin 3  (GPIO2)
  SCL (Blue)   → Pin 5  (GPIO3)

================================================================================
DO THIS IN PUTTY (Commands to copy-paste)
================================================================================

1. Enable I2C:
   sudo srpi-config
   → 3 → I3 → Enable I2C → Reboot
   (Wait 30 seconds)

2. Verify sensor detected:
   i2cdetect -y 1
   (Look for "57" - if missing, check wiring)

3. Install i2c-tools:
   sudo apt install -y i2c-tools

4. Activate existing venv:
   source ~/venv_ocr/bin/activate

5. Install smbus2:
   pip install smbus2==0.4.3

6. Clone library:
   cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
   git clone https://github.com/doug-burrell/max30102.git
   cd max30102
   pip install -e .

7. Test I2C:
   python3 << 'EOF'
   import smbus2
   bus = smbus2.SMBus(1)
   data = bus.read_byte(0x57)
   print(f"[✓] Sensor: 0x{data:02x}")
   bus.close()
   EOF

================================================================================
DO THIS IN VS CODE
================================================================================

1. Create new file: max30102_record.py

2. Copy the code from: max30102_record_simple.py file

3. Save as: max30102_record.py
   Location: ~/rdk_model_zoo/demos/OCR/PaddleOCR/

================================================================================
FINAL STEP: RUN IN PUTTY
================================================================================

cd ~/rdk_model_zoo/demos/OCR/PaddleOCR

source ~/venv_ocr/bin/activate

env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 max30102_record.py

WAIT: 30 seconds for BPM to show real value
STOP: Ctrl+C

Verify:
cat max30102_data_*.csv

✓ SUCCESS!

================================================================================
IF ERROR
================================================================================

"Module not found" → pip install smbus2==0.4.3
"Address not found" → Check wiring, enable I2C, reboot
"BPM shows 0" → Normal - wait 30 seconds, keep finger on sensor
"LD_LIBRARY_PATH" → Use: env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 ...

================================================================================

TOTAL TIME: 15-20 minutes ✓