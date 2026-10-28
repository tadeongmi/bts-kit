"""Build per-cut subtitles from Whisper word timings. Paths are relative to the project folder.

Words that fall inside a cut are grouped into phrases (split on pauses and
sentence ends); long phrases are broken into one-line cues of similar length,
with times relative to the cut. Corrections must match whole words as Whisper wrote them.
Known Whisper errors and hand corrections live in transcripts/subtitle_fixes.json:
  {"IMG_1234": [["Anna", "Ana"]], ...}   # per clip: [wrong, right] text replacements
An empty "right" deletes the words (for a half word clipped at a cut's edge).
Whisper's made-up lines over music (see common.HALLUCINATIONS) are dropped, and runaway word loops are capped.
"""
import json
import os
import re

from common import HALLUCINATIONS

MAX_CHARS = 42   # one line at the burned-in font size
MAX_DUR = 3.2    # seconds a cue may stay up
GAP = 0.6        # pause that always starts a new cue

_fixes = None


def fixes(clip):
    global _fixes
    if _fixes is None:
        path = "transcripts/subtitle_fixes.json"
        _fixes = json.load(open(path)) if os.path.exists(path) else {}
    return _fixes.get(clip, [])


def words(clip, a, b):
    out = []
    for seg in json.load(open(f"transcripts/{clip}.json"))["segments"]:
        if HALLUCINATIONS.search(seg["text"]):
            continue
        ws = seg.get("words", [])
        for i, w in enumerate(ws):
            # Numbers often come back without times: borrow from neighbours
            start = w.get("start", ws[i - 1].get("end") if i else seg["start"])
            end = w.get("end", ws[i + 1].get("start") if i + 1 < len(ws) else seg["end"])
            if start is not None and end is not None and start >= a - 0.05 and end <= b + 0.1:
                out.append((start, end, w["word"]))
    # Cap loops like "no, no, no, no, ..." at three repeats
    capped = []
    for w in out:
        norm = lambda s: re.sub(r"\W", "", s.lower())
        if len(capped) >= 3 and all(norm(x[2]) == norm(w[2]) for x in capped[-3:]):
            continue
        capped.append(w)
    return capped


def fixed_words(clip, a, b):
    """Words in the cut with the clip's corrections applied, spreading the
    replaced span's time evenly over the new words."""
    norm = lambda s: re.sub(r"[^\w]", "", s.lower())
    ws = words(clip, a, b)
    for wrong, right in fixes(clip):
        # The correction stays one unit (non-breaking spaces) so a line break can't split it
        old, new = wrong.split(), [right.replace(" ", " ")]
        for i in range(len(ws) - len(old) + 1):
            span = ws[i:i + len(old)]
            if [norm(w[2]) for w in span] == [norm(t) for t in old]:
                # Keep Whisper's punctuation around the replaced words (¿¡ before, ,.?! after)
                lead = re.match(r"^[^\w]*", span[0][2]).group()
                trail = re.search(r"[^\w]*$", span[-1][2]).group()
                if re.search(r"[^\w]$", right):  # the correction brings its own punctuation
                    trail = ""
                new = [lead + new[0]] + new[1:-1] + [new[-1] + trail] if len(new) > 1 else [lead + new[0] + trail]
                if not right:
                    del ws[i:i + len(old)]
                    break
                s, e = span[0][0], span[-1][1]
                step = (e - s) / len(new)
                ws[i:i + len(old)] = [(s + k * step, s + (k + 1) * step, t) for k, t in enumerate(new)]
                break
    return ws


def _length(ws):
    return len(" ".join(w[2] for w in ws))


def _split(phrase):
    """Break a long phrase into lines of similar length, preferring breaks after commas."""
    n = -(-_length(phrase) // MAX_CHARS)
    n = max(n, -(-int((phrase[-1][1] - phrase[0][0]) * 10) // int(MAX_DUR * 10)))
    if n <= 1:
        return [phrase]
    target = _length(phrase) / n
    lines, cur = [], []
    for i, w in enumerate(phrase):
        cur.append(w)
        rest = phrase[i + 1:]
        if rest and len(lines) < n - 1:
            over = _length(cur) >= target
            comma_near = w[2].endswith(",") and _length(cur) >= target * 0.6
            if (over or comma_near) and _length(rest) >= 10:
                lines.append(cur)
                cur = []
    lines.append(cur)
    return lines


def cues(clip, a, b):
    # Phrases end at pauses and sentence ends; long ones are split evenly
    phrases, cur = [], []
    for w in fixed_words(clip, a, b):
        if cur and (w[0] - cur[-1][1] > GAP or cur[-1][2][-1] in ".?!"):
            phrases.append(cur)
            cur = []
        cur.append(w)
    if cur:
        phrases.append(cur)
    groups = [line for p in phrases for line in _split(p)]
    # Merge one- or two-word stubs into the previous line when they fit
    merged = []
    for g in groups:
        if merged and _length(g) < 10 and _length(merged[-1] + g) <= MAX_CHARS and g[0][0] - merged[-1][-1][1] < GAP:
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
    result = []
    for i, g in enumerate(merged):
        start = max(g[0][0] - a, 0)
        end = g[-1][1] + 0.25
        if i + 1 < len(merged):
            end = min(end, merged[i + 1][0][0])
        end = min(end - a, b - a)
        if end - start >= 0.3:  # drop slivers of a word clipped at the cut's edge
            result.append((start, end, " ".join(w[2] for w in g)))
    return result


def _ts(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(clip, a, b, path):
    cs = cues(clip, a, b)
    if not cs:
        return False
    with open(path, "w") as f:
        for i, (s, e, text) in enumerate(cs, 1):
            f.write(f"{i}\n{_ts(s)} --> {_ts(e)}\n{text}\n\n")
    return True
