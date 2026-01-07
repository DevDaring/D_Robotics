<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Give me full camera setup so that my friend can do from beginning without any hassle.

Below is a full “from zero” **camera setup guide** for RDK X5 (Ubuntu 22.04 + TROS Humble) that also keeps **Wi‑Fi + Remote‑SSH stable** and supports taking a **single snapshot** from the camera topic. The official D‑Robotics docs confirm the `mipi_cam_dual_channel.launch.py` launch flow on Humble/TROS.[^1]

## Prerequisites (once)

1) Ensure the MIPI stereo camera is connected properly and the RDK is on the same Wi‑Fi as the laptop.
2) On the RDK, install required ROS python libs (only once):
```bash
sudo apt update
sudo apt install -y ros-humble-rclpy ros-humble-sensor-msgs ros-humble-cv-bridge python3-opencv
```


## Step 1 — Make Wi‑Fi stable (RDK side)

### 1A) Disable Wi‑Fi power saving globally (persistent)

This is the main fix for Wi‑Fi dropouts on many Linux boards.[^2][^3]

```bash
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/99-no-wifi-powersave.conf >/dev/null <<'EOF'
[connection]
wifi.powersave=2
EOF
sudo systemctl restart NetworkManager
```


### 1B) Disable power saving for the specific Wi‑Fi profile (recommended)

```bash
nmcli -t -f NAME,DEVICE con show --active
# Example: if it prints home2:wlan0 then do:
sudo nmcli con mod "home2" 802-11-wireless.powersave 2
sudo nmcli con down "home2" || true
sudo nmcli con up "home2"
```

NetworkManager supports disabling powersave at the connection level.[^2]

### 1C) Verify Wi‑Fi is healthy

```bash
iw dev wlan0 get power_save 2>/dev/null || iwconfig wlan0 | grep -i power || true
ip -br a
ping -c 3 -W 1 192.168.0.1
```


## Step 2 — Windows firewall (Laptop side) for Remote‑SSH

On Windows, make sure SSH (port 22) isn’t blocked; otherwise VS Code can time out. Microsoft provides troubleshooting guidance for OpenSSH/firewall scenarios.[^4]

**Quick checks:**

```powershell
Test-NetConnection 192.168.0.117 -Port 22
```

```bat
ping 192.168.0.117
```


## Step 3 — Start the camera (Terminal A on RDK)

Important: to avoid ROS 2 network discovery traffic disturbing Wi‑Fi, run the camera in **localhost-only** ROS mode. ROS docs describe `ROS_LOCALHOST_ONLY=1` to isolate ROS traffic to the local machine.[^5]

```bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 daemon stop

ros2 launch mipi_cam mipi_cam_dual_channel.launch.py
```

This launch command is the documented way to start the dual camera node on Humble/TROS.[^1]

## Step 4 — Verify camera topics (Terminal B on RDK)

```bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1

ros2 topic list -t | grep -i image
```


## Step 5 — Take one snapshot (Terminal B)

### 5A) First confirm the topic encoding (important)

Your camera publishes `nv12`, so cv_bridge can’t convert it directly.[^6]

```bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1

ros2 topic echo -n 1 /image_left_raw --field encoding
```


### 5B) Run `camera_snapshot_once.py` (NV12-aware)

Use the NV12-safe version (OpenCV converts NV12→BGR via `COLOR_YUV2BGR_NV12`).[^7]

```bash
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
source ~/venv_ocr/bin/activate   # only if you need your venv

python3 /home/sunrise/rdk_model_zoo/demos/OCR/PaddleOCR/camera_snapshot_once.py
ls -ltr /home/sunrise/rdk_model_zoo/demos/OCR/PaddleOCR/output | tail
```


## If something fails (fast debug checklist)

Run on RDK (serial preferred):

```bash
echo "=== WIFI ==="; nmcli -t dev status | grep wlan0; iw dev wlan0 get power_save 2>/dev/null || true
echo "=== ROUTE ==="; ip route
echo "=== PING GW ==="; ping -c 3 -W 1 192.168.0.1 || true
echo "=== SSH ==="; systemctl is-active ssh || true; ss -lntp | grep ':22' || true
echo "=== ROS LOCALHOST ==="; echo $ROS_LOCALHOST_ONLY
```

And on Windows:

```powershell
Test-NetConnection 192.168.0.117 -Port 22
```

If your friend shares the output of `ros2 topic list -t | grep -i image` and the encoding line, the snapshot script can be matched perfectly to the exact topic name/format.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://developer.d-robotics.cc/rdk_doc/en/Robot_development/quick_demo/demo_sensor/

[^2]: https://gist.github.com/jcberthon/ea8cfe278998968ba7c5a95344bc8b55

[^3]: https://discussion.fedoraproject.org/t/tip-lower-wifi-latency-by-disabling-wifi-power-management/74534

[^4]: https://learn.microsoft.com/en-us/troubleshoot/windows-server/system-management-components/troubleshoot-openssh-windows-firewall-port22

[^5]: https://docs.ros.org/en/foxy/Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment.html

[^6]: http://docs.ros.org/en/lunar/api/cv_bridge/html/python/index.html

[^7]: https://envyen.com/posts/2020-12-11-opencv-yuv-nv12-to-bgr-conversion/

[^8]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/283e84b7-12ff-42b4-a4d2-542f82b2372f/Paddle_OCR_Setup.md

[^9]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/941179ab-7082-4801-8862-45c62a3dd203/WhatsApp-Image-2026-01-04-at-08.44.59.jpg

[^10]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/7e930ef4-3ed5-49ba-b6f5-04cf850d9895/image.jpg

[^11]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/140c9ac8-3973-4359-834a-cba6941ffd64/image.jpg

[^12]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/c47940b2-7a71-4bb4-8987-7cb85f96686e/RDX-X5.pdf

[^13]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/4d106db6-9ee1-473e-bc37-9e347a6958d8/image.jpg

[^14]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/54ea69ad-8872-4c48-a81e-e83caab3a5dd/image.jpg

[^15]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/e7a65707-8dc1-4aa5-a63b-48598c32076b/image.jpg

[^16]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/8db8e810-e162-43c0-af0b-58a4b4139a17/image.jpg

[^17]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/eedc7e58-5562-4a25-936d-a7eb7196fb2e/image.jpg

[^18]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/46e476c9-af1e-4a5c-a56e-7b4fd35c767b/image.jpg

[^19]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/11c4921e-0202-4cbe-887e-0ff461e74f6d/image.jpg

[^20]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/b858bc30-24a4-4318-ad09-87f1b7d5cbb0/image.jpg

[^21]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/9a49d4e2-cb6b-4826-b0d0-75587a226a5d/requirements.txt

[^22]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/a9534420-02f6-4815-8790-8896190343ca/image.jpg

[^23]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/82d41d51-4344-4fe1-b67a-5a8eeb81d767/image.jpg

[^24]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/4a1675da-c4d5-44c2-a8c4-320554f29635/image.jpg

[^25]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/6f64abb5-eab8-4f1e-b287-46d5d7719f50/image.jpg

[^26]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/e1b185ac-e5fc-4347-bcec-978c8e3e6c16/image.jpg

[^27]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/ef186792-6073-434f-b017-4ecc3ab46b66/image.jpg

[^28]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/d9075b8a-ef32-4f84-89a3-c2317691d512/image.jpg

[^29]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/a0dfc5a8-a040-4c27-8213-f66dc49713c8/image.jpg

[^30]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/93b25076-7502-483f-ae18-63fb437c4c2f/image.jpg

[^31]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/08744c75-0a93-45ed-a162-cd26f5ed1524/image.jpg

[^32]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/b1b12673-de58-472f-99b2-460f039b9ca7/image.jpg

[^33]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/f6ca66b1-56df-4a53-b6fc-b795d8e3543f/image.jpg

[^34]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/5af9ab43-419d-4533-89cb-0a68885a6590/image.jpg

[^35]: https://github.com/D-Robotics/hobot_mipi_cam

[^36]: https://github.com/D-Robotics/mono_mobilesam

[^37]: https://www.dfrobot.com/product-2945.html

[^38]: https://www.youtube.com/watch?v=mKs4PMVIh3Y

[^39]: https://forum.manjaro.org/t/how-to-disable-wireless-power-saving-mode-permanently/180296/3

[^40]: https://developer.d-robotics.cc/en/rdkx5

[^41]: https://sir.upc.edu/projects/ros2tutorials/appendices/setup/index.html

[^42]: https://robu.in/product/d-robotics-rdk-x5-development-board-with-4gb-ram/

[^43]: https://github.com/micro-ROS/micro-ROS-Agent/issues/49

[^44]: https://gist.github.com/jcberthon/ea8cfe278998968ba7c5a95344bc8b55?permalink_comment_id=4470639

[^45]: https://www.youtube.com/watch?v=Yc6XdMlLpxI

[^46]: https://discourse.openrobotics.org/t/proposed-changes-to-how-ros-performs-discovery-of-nodes/27640

[^47]: https://www.reddit.com/r/linuxmint/comments/1hds0b9/disabled_power_management_improved_wifi/

[^48]: https://d-robotics.github.io/rdk_doc/en/RDK/

[^49]: https://discuss.px4.io/t/using-ros-localhost-only-with-micrortps-agent/21967

[^50]: https://autowarefoundation.github.io/autoware-documentation/main/installation/additional-settings-for-developers/network-configuration/dds-settings/

