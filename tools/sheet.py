"""See what happens in a clip without watching it.

Usage:
  ./bts sheet <project> <clip> [from] [to]   grid of 20 timestamped frames
  ./bts sheet <project> <clip> --at <time>   one big frame with a 10x10 grid, to read
                                             positions (for zoom x/y) as fractions
Writes a .jpg into the project's sheets/ folder and prints its path.
Each image costs a lot more than reading text: use it for clips with no speech, or
to check a specific moment, not to browse.
"""
import os
import subprocess
import sys

from common import FONT, clip_info, clip_path, project_dir

proj, clip = project_dir(sys.argv[1]), sys.argv[2]
args = sys.argv[3:]
src = clip_path(proj, clip)
dur = clip_info(proj)[clip]["dur"]
os.makedirs(os.path.join(proj, "sheets"), exist_ok=True)

if args[:1] == ["--at"]:
    t = float(args[1])
    out = os.path.join(proj, "sheets", f"{clip}_at{t:.1f}.jpg")
    vf = ("scale=960:-2,drawgrid=w=iw/10:h=ih/10:color=red@0.6,"
          f"drawtext=fontfile={FONT}:text='{clip} @ {t:.1f}s  (grid lines every 0.1)':fontsize=20:fontcolor=yellow:box=1:boxcolor=black")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", vf, out]
else:
    a = float(args[0]) if args else 0.0
    b = min(float(args[1]) if len(args) > 1 else dur, dur)
    fps = 20 / max(b - a, 0.5)
    out = os.path.join(proj, "sheets", f"{clip}_{a:.0f}-{b:.0f}.jpg")
    vf = (f"fps={fps:.4f},scale=320:-2,drawtext=fontfile={FONT}:text='%{{pts\\:hms\\:{a}}}':"
          "fontsize=22:fontcolor=yellow:box=1:boxcolor=black,tile=5x4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", src, "-vf", vf, "-frames:v", "1", out]
subprocess.run(cmd, check=True)
print(out)
