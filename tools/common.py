"""Shared helpers: where projects live, how clips are found, and project settings."""
import json
import os
import re
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(KIT, "tools", "fonts", "DejaVuSans-Bold.ttf")
VIDEO_EXT = (".mov", ".mp4", ".m4v", ".mkv", ".avi", ".mts")

# Lines Whisper makes up over music, wind or silence (YouTube outros, caption credits)
HALLUCINATIONS = re.compile(
    r"suscr[ií]b|gracias por ver|subt[ií]tulos (realizados )?por|amara\.org|"
    r"thanks? (you )?for watching|subscribe|legendas pela|obrigad[oa] por assistir", re.I)


def project_dir(arg):
    """A project is given by name (projects/<name>) or by path."""
    for p in (arg, os.path.join(KIT, "projects", arg)):
        if os.path.isfile(os.path.join(p, "project.json")):
            return os.path.abspath(p)
    sys.exit(f"No project '{arg}'. Create one with: ./bts new <name> <footage folder>")


def settings(proj):
    return json.load(open(os.path.join(proj, "project.json")))


def clips(proj):
    """{clip id: path} for every video in raw/, id = file name without extension."""
    raw = os.path.join(proj, "raw")
    out = {}
    for root, _, files in os.walk(raw, followlinks=True):
        for f in sorted(files):
            if f.lower().endswith(VIDEO_EXT) and not f.startswith("."):
                out.setdefault(os.path.splitext(f)[0], os.path.join(root, f))
    return dict(sorted(out.items()))


def clip_path(proj, clip):
    path = clips(proj).get(clip)
    if not path:
        sys.exit(f"No clip {clip} in {proj}/raw")
    return path


def clip_info(proj):
    """{clip id: {"dur", "rotation", "w", "h"}} from transcripts/clips.tsv (written by ./bts new)."""
    info = {}
    path = os.path.join(proj, "transcripts", "clips.tsv")
    for line in open(path).read().splitlines()[1:]:
        c, dur, rot, w, h = line.split("\t")
        info[c] = {"dur": float(dur), "rotation": int(rot), "w": int(w), "h": int(h)}
    return info


def transcript(proj, clip):
    path = os.path.join(proj, "transcripts", clip + ".json")
    return json.load(open(path)) if os.path.exists(path) else None


def cutlist_path(proj, arg):
    """A cut list by version ("v3" or "3") or by path."""
    if arg.endswith(".json"):
        return os.path.abspath(arg if os.path.exists(arg) else os.path.join(proj, "edl", os.path.basename(arg)))
    return os.path.join(proj, "edl", f"cutlist_v{arg.lstrip('v')}.json")
