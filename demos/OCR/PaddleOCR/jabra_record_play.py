import subprocess
from pathlib import Path

WAV = Path("test.wav")

CAPTURE_DEV = "hw:1,0"       # Jabra mic (card 1, device 0 from your arecord -l)
PLAYBACK_DEV = "plughw:1,0"  # Jabra speaker with conversion (fixes mono->stereo issue)

# Record 5 seconds (16kHz mono, 16-bit)
subprocess.run(
    ["arecord", "-D", CAPTURE_DEV, "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", "5", str(WAV)],
    check=True
)

# Play it back
subprocess.run(
    ["aplay", "-D", PLAYBACK_DEV, str(WAV)],
    check=True
)

print("Done:", WAV)
