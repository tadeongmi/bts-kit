"""Search all transcripts for words or a phrase (ignores case and accents).

Usage: ./bts find <project> <text>
"""
import sys
import unicodedata

from common import clips, project_dir, transcript


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


proj, q = project_dir(sys.argv[1]), norm(" ".join(sys.argv[2:]))
hits = 0
for clip in clips(proj):
    t = transcript(proj, clip) or {"segments": []}
    for s in t["segments"]:
        if q in norm(s["text"]):
            print(f"{clip} {s['start']:6.1f}–{s['end']:6.1f}  {s['text']}")
            hits += 1
print(f"{hits} matches")
