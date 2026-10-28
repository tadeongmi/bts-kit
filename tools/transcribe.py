"""Transcribe every clip of a project with word timings, then rebuild the digest.

Usage: ./bts transcribe <project> [--model large-v3-turbo]
Resumable: clips that already have transcripts/<clip>.json are skipped, so it can
be stopped and rerun. Smaller models (small, medium) are faster but make more mistakes.
Takes roughly as long as the footage on a recent laptop with the default model.
"""
import argparse
import json
import os
import sys
import time

from common import clips, project_dir, settings

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--model", default="large-v3-turbo")
a = ap.parse_args()

proj = project_dir(a.project)
lang = settings(proj).get("language")
out = os.path.join(proj, "transcripts")
todo = {c: p for c, p in clips(proj).items() if not os.path.exists(os.path.join(out, c + ".json"))}
print(f"{len(todo)} of {len(clips(proj))} clips to transcribe", flush=True)

if todo:
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    failed = []
    for i, (clip, path) in enumerate(todo.items(), 1):
        t0 = time.time()
        try:
            segs, info = model.transcribe(path, language=lang, word_timestamps=True, vad_filter=True,
                                          condition_on_previous_text=False)
            segs = [{"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                     "words": [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                               for w in s.words or []]} for s in segs]
            result = {"language": info.language, "segments": segs}
        except Exception as e:  # unreadable file, broken install: not saved, so a rerun retries it
            print(f"[{i}/{len(todo)}] {clip}: FAILED: {e}", flush=True)
            failed.append(clip)
            continue
        json.dump(result, open(os.path.join(out, clip + ".json"), "w"), ensure_ascii=False, indent=1)
        print(f"[{i}/{len(todo)}] {clip}: {len(result['segments'])} lines, {time.time() - t0:.0f}s", flush=True)

import digest  # noqa: E402  (rebuilds transcripts/ALL.md)
digest.build(proj)
if todo and failed:
    sys.exit(f"{len(failed)} clips failed: {', '.join(failed)}. Run ./bts doctor, then transcribe again to retry them.")
