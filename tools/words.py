"""Print a clip's words with exact start times, to place cut points between words.

Usage: ./bts words <project> <clip> [from] [to]
"""
import sys

from common import project_dir, transcript

proj, clip = project_dir(sys.argv[1]), sys.argv[2]
a = float(sys.argv[3]) if len(sys.argv) > 3 else 0
b = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
t = transcript(proj, clip)
if t is None:
    sys.exit(f"{clip} is not transcribed")
for s in t["segments"]:
    ws = [w for w in s["words"] if a <= w["start"] <= b]
    if ws:
        print(f"{ws[0]['start']:6.2f}  " + " ".join(f"{w['word']}@{w['start']:.2f}" for w in ws) + f"  (ends {ws[-1]['end']:.2f})")
