<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Give me all steps written here. SO that my friend can execute step by step. Give me all steps about wifi, firewall, camera running from begining

Below is the complete **step-by-step** procedure your friend can follow from zero: Windows firewall → stable Wi‑Fi on RDK X5 → VS Code Remote‑SSH → run the camera → take one snapshot into your `output` folder.[^1][^2][^3]

## Windows PC steps (Firewall + SSH test)

1) **Connect PC and RDK to the same Wi‑Fi** (same router/subnet).
2) **Allow SSH in Windows Firewall (safe)**: ensure OpenSSH traffic on TCP 22 is allowed (Windows Firewall can block SSH if port 22 is blocked).[^3]

- GUI: “Allow an app through firewall” → ensure `ssh.exe` is allowed on **Private** network (Public optional).[^3]
- Test from Windows PowerShell:

```powershell
Test-NetConnection 192.168.0.117 -Port 22
```

This confirms port 22 reachability.

3) **If VS Code Remote-SSH still times out**, first confirm basic network:

```bat
ping 192.168.0.117
```


## RDK X5 Wi‑Fi (stable, safe)

These are the **only** Wi‑Fi fixes recommended (no watchdog/timer services).[^1]

### Step A: Disable Wi‑Fi powersave (persistent, system-wide)

1) On RDK (serial console or local terminal):
```bash
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/99-no-wifi-powersave.conf >/dev/null <<'EOF'
[connection]
wifi.powersave=2
EOF
sudo systemctl restart NetworkManager
```

`wifi.powersave=2` means “disable powersave” in NetworkManager config.[^1]

### Step B: Disable powersave per Wi‑Fi profile (most reliable)

1) Find the active profile name:
```bash
nmcli -t -f NAME,DEVICE con show --active
```

2) Example (profile name `home2`):
```bash
sudo nmcli con mod "home2" 802-11-wireless.powersave 2
sudo nmcli con down "home2" || true
sudo nmcli con up "home2"
```

Setting `802-11-wireless.powersave 2` disables Wi‑Fi powersave for that specific connection profile.[^1]

3) Verify:
```bash
nmcli -f 802-11-wireless.powersave con show "home2"
iw dev wlan0 get power_save 2>/dev/null || iwconfig wlan0 | grep -i power || true
ip -br a
ping -c 3 -W 1 192.168.0.1
```

**Important:** Do **not** run the watchdog/timer approach if your Wi‑Fi driver is unstable; keep only the two powersave-off steps above.[^1]

## VS Code Remote‑SSH setup

1) Install VS Code + extension **Remote – SSH** on Windows.
2) In VS Code: `Remote-SSH: Connect to Host...` → enter:
    - Host: `192.168.0.117`
    - User: `sunrise`
    - Platform: **Linux**
3) If connection fails, verify again from Windows:
```powershell
Test-NetConnection 192.168.0.117 -Port 22
```


## Camera launch WITHOUT breaking Wi‑Fi

Your remote SSH breaks when you launch the camera because ROS 2 can generate network discovery traffic; the safest fix is to run ROS locally only.[^2]

### Terminal A (on RDK): start camera (localhost-only)

```bash
source /opt/ros/humble/setup.bash
source /opt/tros/humble/setup.bash

export ROS_LOCALHOST_ONLY=1
ros2 daemon stop

ros2 launch mipi_cam mipi_cam_dual_channel.launch.py
```

`ROS_LOCALHOST_ONLY=1` limits ROS 2 communication to localhost so topics/services aren’t visible on Wi‑Fi and don’t spam the network.[^2]

### Terminal B (on RDK): check topics

```bash
source /opt/ros/humble/setup.bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1

ros2 topic list -t | grep -i image
```


## One-snapshot script (saves into your output folder)

Save as:
`/home/sunrise/rdk_model_zoo/demos/OCR/PaddleOCR/camera_snapshot_once.py`

```python
#!/usr/bin/env python3
import os
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

OUTPUT_DIR = "/home/sunrise/rdk_model_zoo/demos/OCR/PaddleOCR/output"
TOPIC = "/image_left_raw"     # change if your topic differs
ENCODING = "bgr8"
TIMEOUT_SEC = 10.0

class OneShotSnap(Node):
    def __init__(self):
        super().__init__("one_shot_snapshot")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.bridge = CvBridge()
        self.done = False
        self.create_subscription(Image, TOPIC, self.cb, qos_profile_sensor_data)
        self.get_logger().info(f"Waiting for 1 frame on: {TOPIC} (timeout {TIMEOUT_SEC}s)")

    def cb(self, msg: Image):
        if self.done:
            return
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding=ENCODING)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_path = os.path.join(OUTPUT_DIR, f"snapshot_{ts}.jpg")
        if not cv2.imwrite(out_path, frame):
            raise RuntimeError(f"cv2.imwrite failed for {out_path}")
        self.get_logger().info(f"Saved: {out_path}")
        self.done = True

def main():
    rclpy.init()
    node = OneShotSnap()
    start = node.get_clock().now()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.2)
            elapsed = (node.get_clock().now() - start).nanoseconds / 1e9
            if elapsed > TIMEOUT_SEC:
                node.get_logger().error("Timeout: no image received. Check topic name with: ros2 topic list -t | grep -i image")
                break
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
```


### Terminal B (on RDK): run snapshot (localhost-only)

```bash
source /opt/ros/humble/setup.bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1

# if using your OCR venv:
source ~/venv_ocr/bin/activate

python3 /home/sunrise/rdk_model_zoo/demos/OCR/PaddleOCR/camera_snapshot_once.py
ls -ltr /home/sunrise/rdk_model_zoo/demos/OCR/PaddleOCR/output | tail
```


## Quick “when it breaks” verification (copy/paste)

Run on RDK serial:

```bash
echo "=== WIFI ==="; nmcli -t dev status | grep wlan0; iw dev wlan0 get power_save 2>/dev/null || true
echo "=== IP/ROUTE ==="; ip -br a; ip route
echo "=== PING GW ==="; ping -c 3 -W 1 192.168.0.1 || true
echo "=== SSH ==="; systemctl is-active ssh || true; ss -lntp | grep ':22' || true
```

If you want this as a single `.md` file for your friend to copy, say “make a README” and it will be formatted for direct sharing.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^4][^40][^41][^42][^43][^44][^45][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://gist.github.com/jcberthon/ea8cfe278998968ba7c5a95344bc8b55

[^2]: https://docs.ros.org/en/foxy/Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment.html

[^3]: https://learn.microsoft.com/en-us/troubleshoot/windows-server/system-management-components/troubleshoot-openssh-windows-firewall-port22

[^4]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/283e84b7-12ff-42b4-a4d2-542f82b2372f/Paddle_OCR_Setup.md

[^5]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/941179ab-7082-4801-8862-45c62a3dd203/WhatsApp-Image-2026-01-04-at-08.44.59.jpg

[^6]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/7e930ef4-3ed5-49ba-b6f5-04cf850d9895/image.jpg

[^7]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/140c9ac8-3973-4359-834a-cba6941ffd64/image.jpg

[^8]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/c47940b2-7a71-4bb4-8987-7cb85f96686e/RDX-X5.pdf

[^9]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/4d106db6-9ee1-473e-bc37-9e347a6958d8/image.jpg

[^10]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/54ea69ad-8872-4c48-a81e-e83caab3a5dd/image.jpg

[^11]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/e7a65707-8dc1-4aa5-a63b-48598c32076b/image.jpg

[^12]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/8db8e810-e162-43c0-af0b-58a4b4139a17/image.jpg

[^13]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/eedc7e58-5562-4a25-936d-a7eb7196fb2e/image.jpg

[^14]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/46e476c9-af1e-4a5c-a56e-7b4fd35c767b/image.jpg

[^15]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/11c4921e-0202-4cbe-887e-0ff461e74f6d/image.jpg

[^16]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/b858bc30-24a4-4318-ad09-87f1b7d5cbb0/image.jpg

[^17]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/9a49d4e2-cb6b-4826-b0d0-75587a226a5d/requirements.txt

[^18]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/a9534420-02f6-4815-8790-8896190343ca/image.jpg

[^19]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/82d41d51-4344-4fe1-b67a-5a8eeb81d767/image.jpg

[^20]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/4a1675da-c4d5-44c2-a8c4-320554f29635/image.jpg

[^21]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/6f64abb5-eab8-4f1e-b287-46d5d7719f50/image.jpg

[^22]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/e1b185ac-e5fc-4347-bcec-978c8e3e6c16/image.jpg

[^23]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/ef186792-6073-434f-b017-4ecc3ab46b66/image.jpg

[^24]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/d9075b8a-ef32-4f84-89a3-c2317691d512/image.jpg

[^25]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/a0dfc5a8-a040-4c27-8213-f66dc49713c8/image.jpg

[^26]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/93b25076-7502-483f-ae18-63fb437c4c2f/image.jpg

[^27]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/08744c75-0a93-45ed-a162-cd26f5ed1524/image.jpg

[^28]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/b1b12673-de58-472f-99b2-460f039b9ca7/image.jpg

[^29]: https://discourse.ubuntu.com/t/power-management-and-wifi-issues/62998?page=2

[^30]: https://forum.manjaro.org/t/how-to-permanently-turn-off-power-management-and-avoid-internet-disconnections/145501

[^31]: https://www.reddit.com/r/linux4noobs/comments/1pmndzc/wifi_works_for_a_few_minutes_then_cuts_out/

[^32]: https://community.frame.work/t/solved-wi-fi-dropouts-on-ubuntu-22-04/27853

[^33]: https://forum.zorin.com/t/wifi-completely-stops-working-after-a-few-hours/51920

[^34]: https://www.danaukes.com/notebook/ros2/10-installing-ros2-on-a-vm/

[^35]: https://www.devart.com/dbforge/edge/install-ssh-server.html

[^36]: https://bbs.archlinux.org/viewtopic.php?id=228107

[^37]: https://sir.upc.edu/projects/ros2tutorials/appendices/setup/index.html

[^38]: https://stackoverflow.com/questions/68594235/allow-ssh-protocol-through-win-10-firewall

[^39]: https://github.com/micro-ROS/micro-ROS-Agent/issues/49

[^40]: https://learn.microsoft.com/en-us/answers/questions/4151585/windows-defender-firewall-blocking-ssh-in-windows

[^41]: https://autowarefoundation.github.io/autoware-documentation/main/installation/additional-settings-for-developers/network-configuration/dds-settings/

[^42]: https://www.imab.dk/blocking-ssh-binaries-with-applocker-and-port-22-in-windows-firewall-using-microsoft-intune/

[^43]: https://docs.pal-robotics.com/25.01/development/robot-communication-ros2.html

[^44]: https://www.youtube.com/watch?v=VD99TyrhJ7w

[^45]: https://olive-robotics.com/docs/developers/quick-start-ezd_ampersand-onboarding/faq/

