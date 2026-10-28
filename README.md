# bts-kit

Turn a folder of phone clips into an edited video by chatting with Claude.
You describe the video; Claude reads what everyone says in the clips, writes the
edit, and renders previews. You watch and give notes ("cut 4997 earlier", "add
the part where Leo dances") until it's right. You get name cards, title cards,
subtitles, music that drops under speech, and a few effects (freeze-frame zoom,
black and white, a spin-into-black ending).

Made for a behind-the-scenes video of a shoot with friends; works for any pile of clips
with people talking: trips, birthdays, bachelor parties, shoots.

## What you need

- A Mac (Apple Silicon or Intel) or Linux. On Windows, use WSL.
- [Claude Code](https://claude.com/claude-code) with any paid Claude plan. Pro is
  enough (see "Keeping usage low").
- About 3 GB of free disk for the tools and speech model, plus room for renders
  (a 10-minute 1080p video is 1–2 GB). Your footage is not copied.

## Install (once)

In Terminal:

```bash
git clone https://github.com/tadeongmi/bts-kit.git
```

```bash
cd bts-kit && ./setup.sh
```

`setup.sh` installs ffmpeg (with Homebrew on a Mac; install it from
[brew.sh](https://brew.sh) first if you don't have it) and a private Python
environment with the speech-to-text model. If Homebrew's standard ffmpeg lacks the
text and subtitle filters, it also installs `ffmpeg-full` (the kit uses it
automatically). It ends with `ok: ...` when everything works. The first
transcription downloads the speech model (1.5 GB).

## Make a video

```bash
cd bts-kit && claude
```

Then just talk, for example:

> I want to make a 6-minute behind the scenes of our music video shoot. The
> footage is in ~/Movies/Shoot BTS. It's in Spanish. Main people: Ana (the
> star), Leo (director), Sofi (choreographer).

Claude will:
1. Set up a project and transcribe every clip on your computer. On an Apple
   Silicon Mac that takes about a quarter of the footage's length (an hour of clips
   ≈ 15 minutes); older or Intel machines can take as long as the footage runs.
2. Read the transcripts and propose a story in sections, then render a 480p preview
   into `projects/<name>/renders/`.
3. Take your notes. Every preview shows `CLIP @ time` in the corner so you can
   point at exact clips. Each round becomes a new version (v1, v2, ...); old
   versions stay, so you can always go back.
4. Ask you for music (any mp3/m4a), fix subtitle typos, and render the 1080p final.

Your footage never leaves your computer: transcription and rendering run locally.
Claude only sees the transcripts and, now and then, a sheet of still frames.

## Keeping usage low

- Use Sonnet (`/model sonnet`); it handles this well. Opus is better at story
  ideas but uses your limit much faster.
- Transcription and rendering run locally and cost nothing; the costly part is
  Claude reading transcripts. Long projects (over an hour of footage) take a big
  chunk of a Pro session's limit on the first draft; notes rounds are cheap.
- Give notes in batches, one message per preview, rather than one note at a time.
- Start a fresh conversation (`/clear`) between projects. To continue a project
  later, say "continue project <name>, latest version is v4".

## Commands (if you want to poke around)

`./bts` lists everything. The main ones: `./bts new`, `./bts transcribe`,
`./bts find <project> <words>`, `./bts render <project> v3 [--final]`.
The cut list format is in `.claude/skills/bts-edit/cutlist.md`.

## Files

```
projects/<name>/
  raw/            link to your footage folder (never modified)
  transcripts/    what everyone says, with times; ALL.md is the readable version
  edl/            cut lists: cutlist_v1.json (the edit) + .md (readable)
  renders/        previews and finals
  music/          your music files
```

Font: DejaVu Sans Bold (license in `tools/fonts/LICENSE`).
