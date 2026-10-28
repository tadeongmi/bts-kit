"""Create a project from a folder of footage.

Usage: ./bts new <name> <footage folder> [--lang es]
Links the footage as projects/<name>/raw (nothing is copied or modified) and
records each clip's length, rotation and size in transcripts/clips.tsv.
--lang is the spoken language (es, en, pt, ...); leave it out to auto-detect per clip.
"""
import argparse
import json
import os
import subprocess
import sys

from common import KIT, clips

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("footage")
ap.add_argument("--lang", default=None)
a = ap.parse_args()

footage = os.path.abspath(os.path.expanduser(a.footage))
if not os.path.isdir(footage):
    sys.exit(f"Not a folder: {footage}")
proj = os.path.join(KIT, "projects", a.name)
if os.path.exists(os.path.join(proj, "project.json")):
    sys.exit(f"Project {a.name} already exists")
for d in ("transcripts", "edl", "renders", "music", "sheets"):
    os.makedirs(os.path.join(proj, d), exist_ok=True)
os.symlink(footage, os.path.join(proj, "raw"))
json.dump({"name": a.name, "language": a.lang, "footage": footage, "brief": ""},
          open(os.path.join(proj, "project.json"), "w"), indent=2, ensure_ascii=False)
json.dump({}, open(os.path.join(proj, "transcripts", "subtitle_fixes.json"), "w"))

rows, total = ["clip\tdur\trotation\tw\th"], 0.0
for clip, path in clips(proj).items():
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height:stream_side_data=rotation:format=duration", "-of", "json", path],
        capture_output=True, text=True).stdout or "{}")
    try:
        st = probe["streams"][0]
        dur = float(probe["format"]["duration"])
    except (KeyError, IndexError, ValueError):
        print(f"skipping {clip}: not a readable video")
        continue
    rot = int(next((sd["rotation"] for sd in st.get("side_data_list", []) if "rotation" in sd), 0))
    w, h = (st["height"], st["width"]) if rot % 180 else (st["width"], st["height"])  # as displayed
    rows.append(f"{clip}\t{dur:.2f}\t{rot}\t{w}\t{h}")
    total += dur
open(os.path.join(proj, "transcripts", "clips.tsv"), "w").write("\n".join(rows) + "\n")
print(f"Project {a.name}: {len(rows) - 1} clips, {total / 60:.1f} min of footage -> {proj}")
