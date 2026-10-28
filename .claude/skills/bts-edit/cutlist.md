# Cut list format

One JSON file per version: `projects/<name>/edl/cutlist_vN.json`. Times are seconds
within each clip (not within the final video). Cuts play in order, section by section.

```json
{
  "title": "Ana's 30th (v2)",
  "notes": "v1: first draft. v2: cold open shortened, Leo's intro moved earlier.",
  "music": "music/song.mp3",
  "sections": [
    {"name": "Cold open", "cuts": [
      {"clip": "IMG_4962", "in": 0.0, "out": 6.8, "note": "'This is going to go so wrong.'"},
      {"card": "The best birthday\nyou'll ever see", "dur": 4}
    ]},
    {"name": "Meet the crew", "cuts": [
      {"clip": "IMG_4949", "in": 0.0, "out": 1.2, "card": "ANA · The Star"},
      {"clip": "IMG_4997", "in": 0.8, "out": 4.3, "card": "The prettiest of them all", "freeze_at": 3.3}
    ]}
  ]
}
```

## Top-level fields

| Field | Meaning |
|---|---|
| `title`, `notes` | For people. Add a sentence to `notes` for every version. |
| `sections` | List of `{"name", "cuts"}`. Names are for people; they don't render. |
| `music` | Optional. Audio file, relative to the project folder. Loops, ducks under speech, fades out. |
| `music_volume` | Optional, default 0.8. Music level when nobody talks (0.5 quieter, 1.2 louder). |
| `subtitles` | Optional. `false` turns off burned-in subtitles. |

## Clip cuts

| Field | Meaning |
|---|---|
| `clip` | Clip ID: the file name without extension. |
| `in`, `out` | Start and end, seconds within the clip. |
| `note` | For people: what happens / the key line. Shown in the `.md`. |
| `card` | Lower-third text over a 1.5 s freeze at the end of the cut. `\n` for line breaks. For name cards use `NAME · Role`. |
| `freeze_at` | With `card`: clip time of the frame to freeze on, instead of the last frame. Must be inside the cut. |
| `rotate` | `"ccw"`, `"cw"` or `"180"`: fix clips whose picture is sideways. |
| `bw` | `true`: black and white (flashbacks, "the moment they realised..."). |
| `zoom` | `{"x": 0.59, "y": 0.68, "z": 4}`: after the cut, freeze the last frame and punch in `z` times on point x,y (fractions of the frame width/height from the top-left) over 2 s. Find x,y with `./bts sheet <name> <clip> --at <out>`. |
| `swirl` | Clip time from which the picture spins faster and faster into black while wind noise drowns the audio. Subtitles stop there. Good for an ending or a "blown away" gag. |
| `subs` | `false`: no subtitles on this cut. |

## Standalone cards

`{"card": "THE END", "dur": 3}`: white text on black, silent, `dur` seconds. Use for
the title, chapter titles, punchlines and the ending.

## The same moment twice

A clip can appear in several cuts (different ranges, or the same line as a quick
callback later). Two cameras on the same moment: cut from one clip to the other
at a line both recorded.
