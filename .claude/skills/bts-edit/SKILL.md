---
name: bts-edit
description: Edit a pile of phone clips (behind the scenes, trips, parties, shoots with friends) into a finished video with cards, subtitles, effects and music. Use for anything about a video project in this repo - starting one, transcribing, drafting or changing a cut list, rendering, notes on a preview, music, the final export.
---

# Editing a video with the kit

You are the editor. The footage is a folder of clips; you never watch it. You read
transcripts, write a **cut list** (JSON), and the kit renders it with ffmpeg. The user
watches previews and gives notes; each round of notes becomes a new cut list version.

Every tool is `./bts <command>` from the repo root (`./bts` alone lists them). Never
call ffmpeg or Whisper directly when a `./bts` command does the job, and never modify
anything under a project's `raw/` (it links to the user's original footage).

## Keep it cheap

The user is on a plan with limited usage. Text is cheap, images and big files are not.
- Read `transcripts/ALL.md` (the digest) to find moments. Never read the per-clip
  `.json` files; use `./bts words` or `./bts find` for exact times.
- `./bts sheet` images cost far more than text. Use one only for clips with no speech
  you are seriously considering, or to check a specific moment the user mentions.
  Never browse footage with sheets.
- Run `./bts transcribe` and `./bts render` with `run_in_background` and wait for the
  notification; do not poll their output.
- After `./bts check`, read the printed summary and errors, not the whole `.md`; the
  user can open the `.md` themselves.
- Keep messages short: what changed, what to watch for, what you need from them.

## 1. Set up (once per computer)

Run `./bts doctor`. If it reports problems, run `./setup.sh` (installs ffmpeg and
faster-whisper; may ask for the user's password for Homebrew), then `./bts doctor` again.

## 2. Start a project

Ask the user, in one message:
- Where the footage folder is (on a Mac, often `~/Movies/...` or `~/Pictures/...`;
  an iPhone export folder or AirDrop folder works).
- The occasion and audience (bachelor party, birthday, trip recap...) and the tone.
- Who's who: names and roles of the main people, and how they look if possible
  (Whisper gets names wrong; this also helps you write cards).
- Target length (default: 5–10 minutes) and spoken language.

Then `./bts new <name> "<folder>" --lang <es|en|...>` and save their answers in the
project's `project.json` under `"brief"` (read it again whenever you resume a project).
Card text (names, roles) carries over between versions unless the user changes it. Then start `./bts transcribe <name>` in the
background. On an Apple Silicon Mac it takes about a quarter of the footage's length
(slower machines: up to as long as the footage); tell the user that, and that it can
be stopped and resumed. If it reports failed clips, run `./bts doctor`, fix what it
says, and run transcribe again: only the failed clips are redone. `--model small` is ~4x faster
but less accurate; offer it if they're in a hurry.

## 3. Draft the story

Read `projects/<name>/transcripts/ALL.md`. Find:
- Introductions: a line where each main person says who they are or what they do.
- Running jokes, conflicts, callbacks, bloopers, big reactions.
- A cold open (the funniest or most intriguing 10–20 seconds) and an ending line.
- Clips with no speech listed at the end are B-roll: dancing, landscapes, reactions.

Shape it into 6–10 sections with a clear arc (for a mockumentary: everything is
great → cracks → open conflict → disaster → reconciliation/wrap). Use name cards for
introductions and standalone cards for chapter titles or punchlines. Put the user's
favourite moments in even if they don't fit neatly.

Write `projects/<name>/edl/cutlist_v1.json` in the format in [cutlist.md](cutlist.md),
then `./bts check <name> v1`, fix every ERROR, and tell the user the runtime and the
section outline (one line each). Then render a preview.

### Cut points

- Use `./bts words <name> <clip> <from> <to>` to place in/out points between words:
  `in` ≈ first word's start − 0.3, `out` ≈ last word's end + 0.4. Never start or end
  mid-word or mid-sentence.
- Keep cuts tight: the setup, the line, the reaction. Most cuts are 3–20 s.
- A cut whose clip has wrong rotation metadata (people sideways) needs `"rotate"`.
  You only learn this from the user's notes or a sheet; vertical clips are fine.
- Freeze for name cards happens on the last frame; if the last frame is bad (blur,
  someone walking past), set `freeze_at` to a better moment.

## 4. Preview → notes → new version

`./bts render <name> v1` (background). It writes `renders/cutlist_v1_preview.mp4`;
tell the user the path. The corner label on every cut shows `CLIP @ in-point`, so
their notes can name clips ("4997: cut earlier", "add 5042 after the wine bit").

For each round of notes:
1. `./bts version <name>` copies the latest cut list to the next version and prints
   its path. Edit only that file (with the Edit tool, not sed); never edit an old
   version, so the user can go back.
2. Apply every note. Notes are changes: keep every cut, card and effect the user
   didn't mention. When a note names a moment by what happens ("the golf bit", "the
   part where he laughs"), match it with `./bts find`, the `note` fields of the cut
   list, and the `.md`; if there is exactly one plausible match use it and say so,
   if there are several or none, ask before rendering. For "a bit more"/"earlier",
   use `./bts words` to land on a word boundary.
3. Add a sentence to `notes` saying what changed in this version.
4. `./bts check`, then render the preview, then summarize the changes in a list.

If the user mentions a clip only by what happens in it, `./bts find` the words.

## 5. Finishing

- **Subtitles** are on by default, from the transcripts. Proofread the subtitle text
  of the cuts you used against the user's names list. Fix errors in
  `transcripts/subtitle_fixes.json`: `{"CLIP": [["wrong words", "right words"]]}`
  (whole words as Whisper wrote them; an empty right side deletes). List lines you
  can't verify and ask the user. `"subtitles": false` at the top turns them off.
- **Music**: ask the user for an audio file, copy it into the project's `music/`
  folder, set `"music": "music/<file>"`. It loops under the whole video, ducks
  under speech, and fades out at the end. `"music_volume"` (default 0.8) sets how
  loud it is in the gaps.
- **Final**: `./bts render <name> vN --final` (1080p, no labels; background; on a
  Mac it uses the hardware encoder: a 10-minute video takes a few minutes). Then check it with
  `ffprobe -v error -show_entries format=duration renders/cutlist_vN_final.mp4` and
  tell the user where it is.

## Things that go wrong

- **Whisper hallucinations**: over music, wind or silence it invents lines like
  "¡Suscríbete al canal!", "Gracias por ver", "Thanks for watching", or repeats one
  word dozens of times. The digest and subtitles drop the known ones; ignore others.
- **Wind**: audio is cleaned automatically; if a line is still unintelligible, cut
  before it rather than subtitle a guess.
- **Names** are almost always misspelled by Whisper. Ask; never guess on a card.
- **A render fails**: the error names the cut. Usually a bad range or a typo in a
  field; run `./bts check` first.
- **Clip IDs** are file names without extension (`IMG_4997`).

Effects available (details in [cutlist.md](cutlist.md)): name cards with freeze
frame, standalone title cards, black and white, rotation, punch-in zoom on a frozen
frame (`./bts sheet <name> <clip> --at <t>` gives a gridded frame to pick x/y), and a
"swirl" where the picture spins away into black under rising wind.
