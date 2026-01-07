<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Give me steps to connect

Electrobot BME280 5V Digital Temperature Humidity Barometric Pressure Sensor Module with rdk x5 through breadvoard

Yes, you can connect the Electrobot BME280 5 V module to the RDK X5 with a breadboard exactly like you would to a Raspberry Pi, using the I²C pins on the 40‑pin header.[^1][^2]

## 1. Identify the pins

On the **Electrobot BME280 5 V module** (GY‑BME280‑5V–style), you’ll typically see pins like:

- **VIN (or VCC)** – power input (3.3–5 V).[^3][^1]
- **GND** – ground.[^1]
- **SCL** – I²C clock.[^1]
- **SDA** – I²C data.[^1]
- (Sometimes also **CSB, SDO** for SPI – ignore these for I²C).[^4][^5]

On the **RDK X5 40‑pin header** (Raspberry‑Pi compatible):[^2][^6]

- **Pin 1** – 3.3 V
- **Pin 2** – 5 V
- **Pin 3** – SDA1 (I²C data)
- **Pin 5** – SCL1 (I²C clock)
- **Pins 6, 9, 14, 20, 25** – GND


## 2. Breadboard wiring (recommended 3.3 V)

Power off the RDK X5, then:

1. Put the BME280 module on the breadboard.
2. Use female–female jumper wires from the RDK X5 header to the breadboard:

- BME280 **VIN → 3.3 V** (RDK pin 1).
    - The module works from 3.3–5 V, but powering at **3.3 V** keeps I²C pull‑ups at 3.3 V, which is safest for the RDK X5 GPIO.[^7][^1]
- BME280 **GND → GND** (RDK pin 6, 9, or any other GND).[^2][^1]
- BME280 **SCL → SCL1** (RDK pin 5).[^2][^1]
- BME280 **SDA → SDA1** (RDK pin 3).[^2][^1]
- If your board has **CSB/CS** and **SDO** pins, leave them unconnected or tie CSB high and SDO low; for most 4‑pin I²C‑only boards you can ignore this.[^5][^4]

Double‑check that you have not swapped SDA/SCL or 3.3 V/5 V.

## 3. Quick check that the RDK X5 sees the sensor

On Ubuntu 22.04 on the RDK X5:

```bash
sudo apt update
sudo apt install -y i2c-tools python3-smbus
sudo i2cdetect -y 1
```

You should see the BME280 at **0x76 or 0x77** in the scan table.[^8][^5]

If you want to read values in Python, you can then use any Raspberry‑Pi‑style BME280 library (e.g. from Adafruit or LastMinuteEngineers) that talks over `/dev/i2c-1`, and it will work the same on the RDK X5.[^9][^1]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26]</span>

<div align="center">⁂</div>

[^1]: https://lastminuteengineers.com/bme280-arduino-tutorial/

[^2]: https://developer.d-robotics.cc/rdk_doc/en/Quick_start/hardware_introduction/rdk_x5/

[^3]: https://techtonics.in/product/gy-bme280-5v-temperature-and-humidity-sensor/

[^4]: https://forum.arduino.cc/t/bme280-connections/519749

[^5]: https://robu.in/product/gy-bme280-5v-temperature-and-humidity-sensor/

[^6]: https://www.waveshare.com/rdk-x5.htm

[^7]: https://learn.adafruit.com/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout/pinouts

[^8]: https://thinkrobotics.com/products/bme280-digital-sensor

[^9]: https://cdn-learn.adafruit.com/downloads/pdf/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout.pdf

[^10]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/5b346216-e89e-4c0e-b507-9f45675c3cc9/RDX-X5.pdf

[^11]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/451debc6-693f-435d-81b5-e2c6270956dc/Wearable-Module-List.pdf

[^12]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/6f02e808-cd08-4539-9852-ad80739f23b8/Solar-module.pdf

[^13]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/90949f99-1329-402b-a216-cb3ddb417668/Solar-module.pdf

[^14]: https://randomnerdtutorials.com/bme280-sensor-arduino-pressure-temperature-humidity/

[^15]: https://www.mouser.com/datasheet/2/783/BST-BME280-DS002-1509607.pdf

[^16]: https://www.watelectronics.com/bme280-ic/

[^17]: https://www.electroniclinic.com/how-to-make-arduino-development-board-with-5v-3a-power-supply/

[^18]: https://www.electroniclinic.com/i2c-interface-between-arduino-and-raspberry-pi/

[^19]: https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf

[^20]: https://archive.d-robotics.cc/downloads/hardware/rdk_x5_module/RDK%20X5%20Module%20Pinout%20Description%20and%20Application%20Note_V1P0_0526.xlsx

[^21]: https://www.indiamart.com/proddetail/gy-bme280-5v-temperature-and-humidity-sensor-module-2855353720662.html

[^22]: https://cdn-learn.adafruit.com/downloads/pdf/adafruit-feather-32u4-fona.pdf

[^23]: https://probots.co.in/bme280-altimeter-barometric-pressure-temperature-humidity-sensor-module-5v.html

[^24]: https://robocraze.com/products/bme280-temperature-sensor-module

[^25]: https://www.ti.com/lit/pdf/spmu056

[^26]: https://www.bitfoic.com/components/bme280-sensor-datasheet-pinout-and-applications?id=85

