"""Check a cut list against the footage and write a readable version of it.

Usage: ./bts check <project> <version>      e.g. ./bts check party v3
Validates every clip and range, then writes edl/cutlist_vN.md: a table per section
with the words said inside each cut, so the story can be read without watching.
Exits with an error listing every problem found.
"""
import json
import os
import sys

from common import clip_info, cutlist_path, project_dir, transcript

proj = project_dir(sys.argv[1])
src = cutlist_path(proj, sys.argv[2])
cl = json.load(open(src))
info = clip_info(proj)
KNOWN = {"clip", "in", "out", "card", "note", "rotate", "bw", "freeze_at", "subs", "zoom", "swirl", "dur"}


def words_in(clip, a, b):
    t = transcript(proj, clip) or {"segments": []}
    return " ".join(w["word"] for s in t["segments"] for w in s.get("words", [])
                    if "start" in w and w["start"] >= a and w["end"] <= b)


def fmt(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


errors, out, total = [], [f"# {cl.get('title', os.path.basename(src))}\n", f"{cl.get('notes', '')}\n"], 0.0
if cl.get("music") and not os.path.exists(os.path.join(proj, cl["music"])):
    errors.append(f"music file {cl['music']} not found (path is relative to the project folder)")
for sec in cl["sections"]:
    sec_start = total
    rows = []
    for c in sec["cuts"]:
        for k in set(c) - KNOWN:
            errors.append(f"{c.get('clip', 'card')}: unknown field '{k}'")
        if "clip" not in c:
            if "card" not in c or "dur" not in c:
                errors.append(f"standalone card needs 'card' and 'dur': {c}")
                continue
            rows.append(f"| {fmt(total)} | *card* | | {c['dur']:.1f}s | **{c['card'].replace(chr(10), ' / ')}** |")
            total += c["dur"]
            continue
        clip, a, b = c["clip"], c.get("in"), c.get("out")
        if clip not in info:
            errors.append(f"{clip}: no such clip")
            continue
        if a is None or b is None or not 0 <= a < b <= info[clip]["dur"] + 0.05:
            errors.append(f"{clip}: range {a}-{b} outside 0-{info[clip]['dur']:.1f}")
            continue
        for k in ("freeze_at", "swirl"):
            if k in c and not a <= c[k] <= b:
                errors.append(f"{clip}: {k} {c[k]} is outside the cut {a}-{b}")
        text = words_in(clip, a, b) or "*(no dialogue)*"
        extra = " · ".join(x for x in [f"**Card:** {c['card'].replace(chr(10), ' / ')}" if "card" in c else "",
                                       f"*{c['note']}*" if "note" in c else ""] if x)
        rows.append(f"| {fmt(total)} | {clip} | {a:.1f}–{b:.1f} | {b - a:.1f}s | {text}"
                    + (f"<br>{extra}" if extra else "") + " |")
        total += b - a + (1.5 if "card" in c else 0) + (2.0 if "zoom" in c else 0)
    out.append(f"\n## {sec['name']} ({fmt(total - sec_start)})\n")
    out.append("| At | Clip | In–out | Len | Dialogue / notes |\n|---|---|---|---|---|")
    out.extend(rows)

out.insert(2, f"**Runtime: {fmt(total)}** across {sum(len(s['cuts']) for s in cl['sections'])} cuts.\n")
dst = os.path.splitext(src)[0] + ".md"
open(dst, "w").write("\n".join(out) + "\n")
print(f"runtime {fmt(total)}, {len(cl['sections'])} sections -> {dst}")
for e in errors:
    print("ERROR", e)
sys.exit(1 if errors else 0)
