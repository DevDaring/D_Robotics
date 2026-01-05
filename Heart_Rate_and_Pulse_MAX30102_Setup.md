<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I will use this sensor (MAX30102 Heart Rate and Pulse Oximeter Sensor Module) with rdk x5 kit. I have flashed this os on rdk - rdk-x5-ubuntu22-preinstalled-desktop-3.3.3-arm64.img.xz . I will put MAX30102 Heart Rate and Pulse Oximeter Sensor Module breadboard then I will connect with jumper wise.

You can read the MAX30102 from your RDK X5 on Ubuntu 22.04 almost exactly like on a Raspberry Pi: power it from 3.3 V, wire it to the 40‑pin header I²C pins with jumpers, then use a Python library over I²C.[^1][^2][^3]

Below is a simple, safe way to do it with a breadboard.

***

## 1. Wiring MAX30102 to the RDK X5

Most MAX30102 breakout boards have these pins: **VIN, GND, SCL, SDA, INT (optional), IRD, RD**. You only need VIN, GND, SCL, SDA to start.[^4][^2][^1]

Treat the RDK X5 40‑pin header like a Raspberry Pi header (it exposes 3.3 V and I²C on the same pins).[^3][^5]

**Connections (breadboard + jumper wires):**

- MAX30102 **VIN → 3.3 V** on RDK X5 (e.g. physical pin 1 or 17).
    - The module usually accepts 3.3–5 V, but using **3.3 V** keeps logic levels safe.[^2][^1]
- MAX30102 **GND → any GND** pin on RDK X5 (e.g. pin 6 or 9).[^1]
- MAX30102 **SDA → SDA1** on RDK X5 (I²C data, physical pin 3).[^3][^1]
- MAX30102 **SCL → SCL1** on RDK X5 (I²C clock, physical pin 5).[^1][^3]
- MAX30102 **INT**: leave unconnected for now (you can add it to a GPIO later if you want interrupts).[^6][^1]

Place the MAX30102 on a breadboard, run female‑to‑female jumpers from the RDK X5 header to the breadboard rails and module pins.

***

## 2. Check that I²C is visible on Ubuntu 22.04

On many Ubuntu images for Pi‑like boards, I²C is already enabled; you just need the tools.[^7][^8]

On the RDK X5:

```bash
sudo apt update
sudo apt install -y i2c-tools python3-smbus python3-pip
```

Then scan the I²C bus:

```bash
sudo i2cdetect -y 1
```

You should see an address appear (often **0x57**) where the MAX30102 is connected.[^9][^6]
If you see nothing, double‑check wiring (3.3 V, GND, SDA/SCL pins).

***

## 3. Read raw data with a ready-made Python library

Instead of writing a driver from scratch, reuse a Raspberry‑Pi‑oriented MAX30102 library; it works on any Linux SBC that exposes `/dev/i2c-1`.[^10][^9]

For example, using the `max30102` library from GitHub:

```bash
cd ~
git clone https://github.com/doug-burrell/max30102.git
cd max30102
pip3 install -r requirements.txt
```

Then try the example (adapt paths if needed):

```bash
python3 examples/heartrate.py
```

or a simple script like:

```python
import max30102
import time

m = max30102.MAX30102()

while True:
    red, ir = m.read_sequential()
    print("RED:", red[-1], "IR:", ir[-1])
    time.sleep(0.1)
```

This will give you raw IR/RED readings; many example scripts in that repo compute heart rate and SpO₂ on top of those.[^11][^9][^10]

***

## 4. Easiest “LLM-friendly” pattern

For your hackathon, an easy pattern is:

- Run the Python script on RDK X5 to **sample MAX30102 periodically** and compute heart rate / SpO₂.[^2][^11]
- Expose those values to your LLM or UI via:
    - a local HTTP/REST endpoint,
    - a small WebSocket server, or
    - a shared file/Redis key the LLM side reads.

That way, you keep the hardware part simple (just I²C + one Python script) and focus your time on integrating the vitals into your LLM/VLM logic.

If you share the exact MAX30102 product link you bought, more precise notes (3.3 V vs 5 V, any quirks) and a minimal ready‑to‑run script can be tailored to your board.
<span style="display:none">[^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29]</span>

<div align="center">⁂</div>

[^1]: https://docs.cirkitdesigner.com/component/3145d4c7-689a-49dd-af9c-f854456c2561/gy-max30102

[^2]: https://lastminuteengineers.com/max30102-pulse-oximeter-heart-rate-sensor-arduino-tutorial/

[^3]: https://developer.d-robotics.cc/rdk_doc/en/Quick_start/hardware_introduction/rdk_x5/

[^4]: https://circuitdigest.com/microcontroller-projects/how-max30102-pulse-oximeter-and-heart-rate-sensor-works-and-how-to-interface-with-arduino

[^5]: https://www.waveshare.com/rdk-x5.htm

[^6]: https://www.fabian.com.mt/viewer/43730/pdf.pdf

[^7]: https://www.theredreactor.com/2022/10/14/ubuntu/

[^8]: https://github.com/Joshua-Riek/ubuntu-rockchip/issues/229

[^9]: https://38-3d.co.uk/blogs/blog/using-the-max30102-with-the-raspberry-pi

[^10]: https://github.com/doug-burrell/max30102

[^11]: https://docs.sunfounder.com/projects/umsk/en/latest/05_raspberry_pi/pi_lesson14_max30102.html

[^12]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/5b346216-e89e-4c0e-b507-9f45675c3cc9/RDX-X5.pdf

[^13]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/451debc6-693f-435d-81b5-e2c6270956dc/Wearable-Module-List.pdf

[^14]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/6f02e808-cd08-4539-9852-ad80739f23b8/Solar-module.pdf

[^15]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/90949f99-1329-402b-a216-cb3ddb417668/Solar-module.pdf

[^16]: https://archive.d-robotics.cc/downloads/hardware/rdk_x5_module/RDK%20X5%20Module%20Hardware%20Design%20Guide_V1P0_0526.pdf

[^17]: https://www.ti.com/lit/pdf/spmu056

[^18]: https://www.electroniclinic.com/i2c-interface-between-arduino-and-raspberry-pi/

[^19]: https://www.facebook.com/ebokify/photos/httpssclickaliexpresscome_oes8nhfrdk-x5-poe-module-for-power-over-ethernet-ieee-/122182715486767319/

[^20]: https://cdn-learn.adafruit.com/downloads/pdf/adafruit-feather-32u4-fona.pdf

[^21]: https://www.egalnetsoftwares.com/apps/raspcontroller/enable_i2c_interface/

[^22]: https://archive.d-robotics.cc/downloads/hardware/rdk_x5_module/RDK%20X5%20Module%20Pinout%20Description%20and%20Application%20Note_V1P0_0526.xlsx

[^23]: https://www.instructables.com/Guide-to-Using-MAX30102-Heart-Rate-and-Oxygen-Sens/

[^24]: https://www.electroniclinic.com/arduino-i2c-scanner-and-multiple-i2c-sensors-interfacing-programming/

[^25]: https://easyelecmodule.com/max30100-max30102-pulse-oximeter-and-heart-rate-sensor-module/

[^26]: https://openest.io/non-classe-en/activate-raspberry-pi-4-i2c-bus/

[^27]: https://spotpear.com/index/product/detail/id/972.html

[^28]: https://store.roboticsbd.com/development-boards/94-8-arduino-uno-r3-robotics-bangladesh.html

[^29]: https://stackoverflow.com/questions/77074857/how-to-change-i2c-clock-on-ubuntu-22-04-rpi-4

