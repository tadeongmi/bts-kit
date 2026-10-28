#!/usr/bin/env bash
# Installs what the kit needs: ffmpeg and a Python environment with faster-whisper.
# Safe to run again. macOS (Homebrew) or Linux (apt); on Windows, run it inside WSL.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then
    brew install ffmpeg
  elif command -v apt-get >/dev/null; then
    sudo apt-get update && sudo apt-get install -y ffmpeg
  else
    echo "Install ffmpeg first (macOS: https://brew.sh, then brew install ffmpeg)"; exit 1
  fi
fi

if ! command -v uv >/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
[ -x .venv/bin/python ] || uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

chmod +x bts
if ! ./bts doctor && command -v brew >/dev/null; then
  # Homebrew's plain ffmpeg can lack the text and subtitle filters; ffmpeg-full has them
  brew install ffmpeg-full
  ./bts doctor
fi
