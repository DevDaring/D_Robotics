<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Write step by step how to configure audio devices so that my friend can do from beginning

Below is a “from zero” checklist your friend can follow on a fresh RDK X5 (Ubuntu 22.04) to configure **Jabra USB** for record/play and **Bose Bluetooth** for playback, then run your Python script (with no extra pip audio deps, so minimal conflict risk). `bluetoothctl` pairing needs an agent (`agent on` + `default-agent`) and then `pair/trust/connect`.[^1]

## Install required packages

```bash
sudo apt update
sudo apt install -y alsa-utils usbutils pulseaudio-utils bluez
```

`pulseaudio-utils` provides `pactl` and `paplay`, which are used to select the Bose sink.[^2][^3]

## Configure Jabra (USB audio)

1) Plug in the Jabra headset.
2) Confirm Linux sees it:
```bash
lsusb | grep -i jabra
```

3) Get ALSA card/device numbers:
```bash
arecord -l
aplay -l
```

On your system, Jabra appears as `card 1, device 0` for both capture and playback.[^4]

4) Test record (5 sec) + play to Jabra:
```bash
# IMPORTANT: Use 'plughw' instead of 'hw' to avoid "Device or resource busy" error
# 'hw:1,0' requires exclusive access - PulseAudio may block it
# 'plughw:1,0' allows shared access - works alongside PulseAudio

arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav
aplay -D plughw:1,0 test.wav
```

**Troubleshooting "Device or resource busy" error:**
```bash
# 1. Check what's using the audio device
fuser -v /dev/snd/*

# 2. If PulseAudio is holding it, you have two options:

# Option A: Use plughw (recommended - allows shared access)
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav

# Option B: Kill conflicting arecord processes
pkill -9 arecord
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav
```

Using `plughw` for playback avoids mono-channel playback issues you already hit.[^5]

## Configure Bose (Bluetooth audio output)

1) Put Bose Micro into pairing mode (LED blinking blue).
If it was paired to a phone/laptop, disconnect there first (otherwise Linux may time out).
2) Pair/connect using `bluetoothctl`:
```bash
bluetoothctl
power on
agent on
default-agent
scan on
# wait for Bose MAC to appear, then:
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
quit
```

This is the standard BlueZ pairing flow and helps avoid GUI pairing failures.[^1]

3) Verify Bose is connected:
```bash
bluetoothctl info XX:XX:XX:XX:XX:XX
```

4) Find the PulseAudio sink name for Bose:
```bash
pactl list short sinks
```

You should see a sink like `bluez_sink.<MAC>.a2dp_sink` when Bose is connected (your example was `bluez_sink.78_2B_64_DD_68_CF.a2dp_sink`).[^6]

5) Quick Bose playback test (choose your Bose sink name):
```bash
paplay -d bluez_sink.78_2B_64_DD_68_CF.a2dp_sink test.wav
```

`paplay -d` plays to a specific PulseAudio sink.[^3]

## Run Python with your venv (no-conflict style)

1) Save your final script as `jabra_record_play.py` (the one with the Bose sink name filled).
2) Run exactly like this (matches your proven pattern):[^4]
```bash
source ~/venv_ocr/bin/activate
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 jabra_record_play.py
```

If your friend’s Bose MAC differs, only this line in the Python file must be changed:

```python
BOSE_SINK = "bluez_sink.<THEIR_MAC>.a2dp_sink"
```

Plain question: should the “beginner steps” assume **GUI pairing** (Settings → Bluetooth) only, or should they always use `bluetoothctl` like above for reliability?
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://documentation.ubuntu.com/core/explanation/system-snaps/bluetooth/pairing/

[^2]: https://www.mankier.com/1/pactl

[^3]: https://manpages.debian.org/testing/pulseaudio-utils/paplay.1.en.html

[^4]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/9f35be18-3f9e-40a2-847a-9fc3c0d126d3/RDK_X5_commands.txt

[^5]: https://www.alsa-project.org/wiki/SoundcardTesting

[^6]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/e078b76c-0145-4054-96e6-0f30381bf74a/image.jpg

[^7]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/68662184-a017-4313-9258-e3919f38240b/requirements.txt

[^8]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/148640d3-4661-40a0-820f-d73094a16a36/image.jpg

[^9]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/48918449/b9f71f7d-91e0-4cc6-a900-90a569f71e2a/image.jpg

[^10]: https://arxiv.org/pdf/2211.12934.pdf

[^11]: https://arxiv.org/html/2411.13693v1

[^12]: https://arxiv.org/html/2405.03045v1

[^13]: https://arxiv.org/pdf/2204.13640.pdf

[^14]: http://arxiv.org/pdf/2101.09381.pdf

[^15]: https://arxiv.org/abs/2409.16530

[^16]: https://ssjournals.com/index.php/ijasr/article/download/2753/2193

[^17]: https://arxiv.org/pdf/2204.02464.pdf

[^18]: https://gist.github.com/peters/26315cd7a8a31e3d192ed05ef9a79ba7?permalink_comment_id=5074618

[^19]: https://forums.developer.nvidia.com/t/cant-connect-my-orin-nano-to-another-device-in-bluetooth/291616

[^20]: https://discourse.ubuntu.com/t/bluetooth-has-stopped-finding-devices-and-connecting-on-22-04/53345

[^21]: https://knowledgebase.frame.work/ubuntu-bluetooth-S1PGxfho

[^22]: https://dl.acm.org/doi/fullHtml/10.5555/1080072.1080075

[^23]: https://brokkr.net/2018/05/24/down-the-drain-the-elusive-default-pulseaudio-sink/

[^24]: https://stackoverflow.com/questions/67322499/ubuntu-20-04-2-bluetoothctl-scan-from-bash-script

[^25]: https://en.wikipedia.org/wiki/Advanced_Linux_Sound_Architecture

[^26]: https://www.reddit.com/r/i3wm/comments/czsl8b/i_wrote_a_script_for_switching_audio_sinks_in/

[^27]: https://stackoverflow.com/questions/38174727/modify-alsa-arecord-function-to-output-audio-levels-to-raspberry-pi-3-rgb-led

[^28]: https://bbs.archlinux.org/viewtopic.php?id=264337

[^29]: https://www.kernel.org/doc/html/v4.17/sound/soc/dapm.html

[^30]: https://manpages.ubuntu.com/manpages/trusty/en/man1/pactl.1.html

[^31]: https://sourceforge.net/p/alsa/discussion/86659/thread/1611c5ca/

[^32]: https://github.com/Alexays/Waybar/issues/3350

[^33]: https://www.shallowsky.com/linux/pulseaudio-command-line.html

[^34]: https://stackoverflow.com/questions/52311637/pulseaudio-setting-up-sinks-and-sources-for-a2dp-and-hfp-connections

