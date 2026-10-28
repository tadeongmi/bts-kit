"""Render a cut list to a single video: one ffmpeg encode per cut, then concat.

Usage:
  ./bts render <project> <version>            480p preview with clip labels in the corner
  ./bts render <project> <version> --final    1080p, no labels
Writes renders/cutlist_vN_preview.mp4 or _final.mp4 in the project.

Every segment is normalized to the same size/fps/audio so the concat is a plain
stream copy. Every cut gets leveled, wind-cleaned audio, a blurred background
behind vertical clips, and subtitles from the transcripts (see subs.py). The cut
list fields are documented in .claude/skills/bts-edit/cutlist.md.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import subs
from common import FONT, clip_path, cutlist_path, project_dir

FREEZE = 1.5  # seconds a name card holds on the last frame
ZOOM = 2.0    # seconds of a punch-in zoom

proj = project_dir(sys.argv[1])
src = cutlist_path(proj, sys.argv[2])
final = "--final" in sys.argv
W, H = (1920, 1080) if final else (854, 480)
os.chdir(proj)
name = os.path.splitext(os.path.basename(src))[0]
cl = json.load(open(src))
work = tempfile.mkdtemp(prefix=f"render-{name}-", dir="renders")
out = f"renders/{name}_{'final' if final else 'preview'}.mp4"

if final and sys.platform == "darwin":
    # The Mac's hardware encoder: many times faster than x264 at a similar size
    venc = ["-c:v", "h264_videotoolbox", "-b:v", "12M"]
elif final:
    venc = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]
else:
    venc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28"]
common = venc + ["-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k",
                 "-ar", "48000", "-ac", "2", "-video_track_timescale", "30000"]


def textfile(text):
    # drawtext reads from a file so card text needs no escaping
    fd, path = tempfile.mkstemp(suffix=".txt", dir=work)
    os.write(fd, text.encode())
    os.close(fd)
    return path


def drawtext(text, size, y, box=True):
    # Shrink long lines to fit 90% of the width (DejaVu Bold is ~0.62em per char)
    size = min(size, int(W * 0.9 / (0.62 * max(len(l) for l in text.split("\n")))))
    return (f"drawtext=fontfile={FONT}:textfile={textfile(text)}:fontsize={size}:fontcolor=white"
            f":text_align=C:line_spacing={size // 3}:x=(w-text_w)/2:y={y}"
            + (":box=1:boxcolor=black@0.6:boxborderw=12" if box else ""))


# Applied after ffmpeg's own autorotation, for clips whose rotation metadata is wrong
ROTATE = {"ccw": "transpose=2,", "cw": "transpose=1,", "180": "hflip,vflip,"}
# Cut wind rumble, soften steady noise, then level every cut to the same loudness
AUDIO = "highpass=f=90,afftdn=nr=10:nf=-40,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000"


def picture(src, tag, c):
    """Fit a clip into the frame over a blurred, zoomed copy of itself (fills
    the sides of vertical clips; fully covered on landscape ones)."""
    rot = ROTATE.get(c.get("rotate"), "")
    return (f"[{src}]{rot}split=2[{tag}a][{tag}b];"
            f"[{tag}a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=20:2,eq=brightness=-0.1[{tag}bg];"
            f"[{tag}b]scale={W}:{H}:force_original_aspect_ratio=decrease[{tag}fg];"
            f"[{tag}bg][{tag}fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30" + (",hue=s=0" if c.get("bw") else ""))


def subtitles(c):
    """Burned-in subtitles for this cut, or "" if nothing is said in it."""
    path = os.path.join(work, f"{len(segments):03d}.srt")
    end = min(c["out"], c.get("swirl", c["out"]))
    if not cl.get("subtitles", True) or c.get("subs") is False or not subs.write_srt(c["clip"], c["in"], end, path):
        return ""
    style = ("FontName=DejaVu Sans,Bold=1,FontSize=15,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00000000,BorderStyle=1,Outline=1.5,Shadow=0,MarginV=10")
    return f",subtitles=filename='{path}':fontsdir='{os.path.dirname(FONT)}':force_style='{style}'"


segments = []
cuts = [c for sec in cl["sections"] for c in sec["cuts"]]
for c in cuts:
    seg = os.path.join(work, f"{len(segments):03d}.mp4")
    if "clip" not in c:
        vf = f"color=black:s={W}x{H}:r=30:d={c['dur']}," + drawtext(c["card"], H // 12, "(h-text_h)/2", box=False)
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", vf,
               "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={c['dur']}",
               "-shortest", *common, seg]
    else:
        clip = clip_path(proj, c["clip"])
        dur = c["out"] - c["in"]
        inputs = ["-ss", str(c["in"]), "-t", str(dur), "-i", clip]
        af = AUDIO
        if "card" not in c:
            graph = picture("0:v", "m", c)
        elif "freeze_at" in c and "zoom" not in c:
            # Freeze on a chosen frame (clip time) instead of the last one
            inputs += ["-ss", str(c["freeze_at"]), "-i", clip]
            graph = (picture("0:v", "m", c) + "[m];" + picture("1:v", "f", c) + ",trim=end_frame=1,"
                     f"tpad=stop_mode=clone:stop_duration={FREEZE - 1 / 30}[f];[m][f]concat=n=2:v=1:a=0")
        else:
            graph = picture("0:v", "m", c) + f",tpad=stop_mode=clone:stop_duration={FREEZE}"
        if "swirl" in c:
            # Spin faster and faster while the picture is sucked into the dark, under rising wind
            T = c["swirl"] - c["in"]
            graph += (f",rotate=a='if(gte(t,{T}),pow(t-{T},2)*4,0)':fillcolor=black,"
                      f"eq=brightness='if(gte(t,{T}),-min((t-{T})/{dur - T},1)*0.8,0)':eval=frame")
            af = (f"volume=2[d];anoisesrc=color=brown:amplitude=0.8:r=48000:d={dur},lowpass=f=500,"
                  f"volume='if(gte(t,{T}),min((t-{T})/1.2,1)*3,0.3)':eval=frame[n];[d][n]amix=inputs=2:normalize=0,"
                  "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000")
        graph += subtitles(c)
        if "zoom" in c:
            # Freeze on the last frame and punch in on the chosen point
            z = c["zoom"]
            n = int(ZOOM * 30)
            inputs += ["-ss", str(max(c["out"] - 0.05, 0)), "-i", clip]
            graph += ("[m];" + picture("1:v", "f", c) + ",trim=end_frame=1,"
                      f"zoompan=z='min(1+({z.get('z', 3)}-1)*on/{n // 2},{z.get('z', 3)})'"
                      f":x='iw*{z['x']}-iw/zoom/2':y='ih*{z['y']}-ih/zoom/2'"
                      f":d={n}:s={W}x{H}:fps=30[f];[m][f]concat=n=2:v=1:a=0")
            af += f",apad=pad_dur={ZOOM}"
        if "card" in c:
            graph += "," + drawtext(c["card"], H // 18, "h*0.78") + f":enable='gte(t,{dur - 0.3})'"
            af += f",apad=pad_dur={FREEZE}"
        if not final:
            graph += "," + drawtext(f"{c['clip']} @ {c['in']:.1f}s", H // 30, "10", box=True).replace(
                ":x=(w-text_w)/2", ":x=10")
        cmd = ["ffmpeg", "-y", "-v", "error", *inputs,
               "-filter_complex", f"{graph}[v];[0:a]{af}[a]", "-map", "[v]", "-map", "[a]", *common, seg]
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit(f"ffmpeg failed on cut {len(segments) + 1} ({c.get('clip', 'card')}); the rest was not rendered")
    segments.append(seg)
    print(f"[{len(segments)}/{len(cuts)}] {c.get('clip', 'card')}", flush=True)

listfile = os.path.join(work, "list.txt")
with open(listfile, "w") as f:
    f.writelines(f"file '{os.path.abspath(s)}'\n" for s in segments)
music = cl.get("music")
joined = os.path.join(work, "joined.mp4") if music else out
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listfile,
                "-c", "copy", "-movflags", "+faststart", joined], check=True)
if music:
    # Loop the track under everything; dialogue pushes it down ~15 dB while anyone speaks
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  joined], capture_output=True, text=True, check=True).stdout)
    vol = cl.get("music_volume", 0.8)
    mix = (f"[0:a]asplit=2[dia][key];[1:a]aresample=48000,volume={vol},afade=t=out:st={max(total - 3, 0)}:d=3[mus];"
           "[mus][key]sidechaincompress=threshold=0.02:ratio=12:attack=30:release=600:makeup=1[duck];"
           "[dia][duck]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", joined, "-stream_loop", "-1", "-i", music,
                    "-filter_complex", mix, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
shutil.rmtree(work)
print(f"wrote {os.path.join(proj, out)}")
