# bts-kit

A kit for turning a folder of phone clips into an edited video, driven by Claude.
For anything about a video project, follow the `bts-edit` skill
(`.claude/skills/bts-edit/SKILL.md`).

- Every tool runs as `./bts <command>`; `./bts` alone lists them.
- Projects live in `projects/<name>/`. `raw/` inside a project links to the user's
  original footage: never write there.
- The user may not be technical: explain in plain words, don't show code unless asked,
  and ask before installing anything.
