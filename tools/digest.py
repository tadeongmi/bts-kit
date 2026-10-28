"""Write transcripts/ALL.md: every clip's lines with times, in one readable file.

This is the file to read when picking moments; it is much smaller than the JSON.
Usage: ./bts digest <project>   (transcribe runs this automatically)
"""
import os
import sys

from common import HALLUCINATIONS, clip_info, project_dir, transcript


def build(proj):
    info = clip_info(proj)
    out, broll, missing = ["# All transcripts\n",
                           "Times are seconds within each clip. Clips with no speech are listed at the end.\n"], [], []
    for clip, ci in info.items():
        t = transcript(proj, clip)
        if t is None:
            missing.append(clip)
            continue
        lines = [s for s in t["segments"] if not HALLUCINATIONS.search(s["text"])]
        shape = "vertical" if ci["h"] > ci["w"] else "horizontal"
        if not lines:
            broll.append(f"{clip} ({ci['dur']:.0f}s, {shape})")
            continue
        out.append(f"\n## {clip} ({ci['dur']:.0f}s, {shape})\n")
        out += [f"- `{s['start']:6.1f}–{s['end']:6.1f}` {s['text']}" for s in lines]
    out.append(f"\n## No speech ({len(broll)} clips, look at them with ./bts sheet)\n")
    out += [f"- {b}" for b in broll]
    if missing:
        out.append(f"\n## Not transcribed yet ({len(missing)})\n\n" + ", ".join(missing))
    path = os.path.join(proj, "transcripts", "ALL.md")
    open(path, "w").write("\n".join(out) + "\n")
    print(f"wrote {path}: {len(info) - len(broll) - len(missing)} clips with speech, "
          f"{len(broll)} without, {len(missing)} not transcribed")


if __name__ == "__main__":
    build(project_dir(sys.argv[1]))
