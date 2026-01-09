<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Now it worked fine. Give me all final solutions step by step so that I can again make it work if everything is formatted. Give me all proper steps

Great to hear it is working! Here is the complete, consolidated "Master Guide" to setting this up from scratch on a formatted RDK X3 system. Save this for future reference.

This guide fixes three critical issues:

1. **Wi-Fi drops** (caused by power saving).
2. **Internet/Bluetooth Hardware Crash** (caused by ROS 2 multicast flooding).
3. **Bluetooth "Unknown Connection"** (caused by audio profile issues).

***

### **Phase 1: Permanent Wi-Fi Power Fix**

*Prevents the Wi-Fi chip from "sleeping" and disconnecting randomly.*

Run this once in the terminal:

```bash
# 1. Create the power-save override file
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/99-no-wifi-powersave.conf >/dev/null <<'EOF'
[connection]
wifi.powersave=2
EOF

# 2. Restart Network Manager to apply
sudo systemctl restart NetworkManager
```


***

### **Phase 2: Global ROS 2 Network Isolation**

*Prevents the camera from flooding the router and crashing the Bluetooth/Wi-Fi chip.*

Run this to ensure **every** terminal (local or PuTTY) is isolated automatically:

```bash
# 1. Append these lines to your user's startup script
cat >> ~/.bashrc <<'EOF'

# --- ROS 2 ISOLATION SETTINGS ---
source /opt/tros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export ROS_DOMAIN_ID=42
# --------------------------------
EOF

# 2. Apply changes immediately
source ~/.bashrc
```

**Verification:** Open a *new* terminal and type `echo $ROS_LOCALHOST_ONLY`. It **must** print `1`.

***

### **Phase 3: Bluetooth Speaker Setup**

*Ensures high-quality audio and reliable connection.*

1. **Install Audio Drivers** (Required for A2DP high-quality audio):

```bash
sudo apt update
sudo apt install pulseaudio-module-bluetooth bluez
sudo killall pulseaudio
pulseaudio --start
```

2. **Connect Speaker (One-time pairing):**
*Put your Bose speaker in pairing mode (blinking blue).*

```bash
bluetoothctl scan on
# Wait for "78:2B:64:DD:68:CF" to appear, then Ctrl+C

bluetoothctl trust 78:2B:64:DD:68:CF
bluetoothctl pair 78:2B:64:DD:68:CF
bluetoothctl connect 78:2B:64:DD:68:CF
```

3. **Set Audio Defaults:**
Once connected, force the output to the speaker:

```bash
pactl set-default-sink bluez_sink.78_2B_64_DD_68_CF.a2dp_sink
pactl set-sink-volume bluez_sink.78_2B_64_DD_68_CF.a2dp_sink 60%
```


***

### **Phase 4: Launching the Camera (Routine)**

Now, whenever you need to run the camera, you can just run the standard command. The protection from Phase 2 will handle everything automatically.

```bash
# No extra exports needed anymore!
ros2 launch mipi_cam mipi_cam_dual_channel.launch.py
```


### **Emergency Recovery**

If the Wi-Fi/Bluetooth ever crashes again (showing `hci0 command tx timeout`):

1. **Shutdown** the RDK.
2. **Unplug power** for 10 seconds (to drain the chip).
3. **Restart**.
<span style="display:none">[^1][^2][^3][^4][^5][^6]</span>

<div align="center">⁂</div>

[^1]: Look-this-problem-arised-again.-I-have-started-cam.md

[^2]: image.jpg

[^3]: selected_image_4765194127006733622.jpg

[^4]: selected_image_8459897944949791000.jpg

[^5]: image.jpg

[^6]: image.jpg

