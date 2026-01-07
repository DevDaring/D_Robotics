import subprocess
from pathlib import Path

WAV = Path("test.wav")

# From your arecord/aplay -l: Jabra is card 1, device 0
JABRA_CAPTURE_DEV = "hw:1,0"
JABRA_PLAYBACK_DEV = "plughw:1,0"   # works for mono playback on your Jabra setup

# From your: pactl list short sinks
BOSE_SINK = "bluez_sink.78_2B_64_DD_68_CF.a2dp_sink"

def run(cmd):
    subprocess.run(cmd, check=True)

# 1) Record 5 seconds from Jabra mic
run([
    "arecord",
    "-D", JABRA_CAPTURE_DEV,
    "-f", "S16_LE",
    "-r", "16000",
    "-c", "1",
    "-d", "5",
    str(WAV),
])

# 2) Play to Jabra headset
run(["aplay", "-D", JABRA_PLAYBACK_DEV, str(WAV)])

# 3) Play to Bose Bluetooth speaker (PulseAudio sink)
run(["paplay", "-d", BOSE_SINK, str(WAV)])

print("Done:", WAV)
