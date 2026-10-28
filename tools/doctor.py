"""Check that everything the kit needs is installed. Usage: ./bts doctor"""
import os
import shutil
import subprocess
import sys

from common import FONT

problems = []
for tool in ("ffmpeg", "ffprobe"):
    if not shutil.which(tool):
        problems.append(f"{tool} not found: run ./setup.sh")
if not problems:
    filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    names = {line.split()[1] for line in filters.splitlines() if len(line.split()) > 2}
    need = ["drawtext", "subtitles", "zoompan", "sidechaincompress", "loudnorm", "afftdn", "rotate", "boxblur"]
    missing = [f for f in need if f not in names]
    if missing:
        problems.append(f"ffmpeg is missing filters {', '.join(missing)}: on a Mac run `brew install ffmpeg-full`, "
                        "then ./setup.sh again")
    help_ = subprocess.run(["ffmpeg", "-hide_banner", "-h", "filter=drawtext"], capture_output=True, text=True).stdout
    if "drawtext" in names and "text_align" not in help_:
        problems.append("ffmpeg is too old (needs 6.1 or newer for centered cards)")
    encoders = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if "libx264" not in encoders:
        problems.append("ffmpeg has no libx264 encoder")
try:
    import faster_whisper.audio
    import numpy as np
    tone = os.path.join(os.path.dirname(FONT), "..", "..", ".doctor-tone.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=d=1", tone], check=True)
    if not isinstance(faster_whisper.audio.decode_audio(tone), np.ndarray):
        raise RuntimeError("no audio decoded")
    os.remove(tone)
except ImportError:
    problems.append("faster-whisper is not installed: run ./setup.sh")
except Exception as e:  # e.g. an incompatible PyAV version
    problems.append(f"faster-whisper can't read audio ({e}): run ./setup.sh again")
if not os.path.exists(FONT):
    problems.append(f"font missing: {FONT}")

if problems:
    print("\n".join("PROBLEM " + p for p in problems))
    sys.exit(1)
print(f"ok: {subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True).stdout.split()[2]} ffmpeg, "
      f"faster-whisper, python {sys.version.split()[0]}")
