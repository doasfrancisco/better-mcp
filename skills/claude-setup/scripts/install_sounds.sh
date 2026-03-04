#!/bin/bash
# Install a sound theme into .claude/sounds/ as .wav files
# Usage: install_sounds.sh <skill-assets-path> <theme-name>

ASSETS_DIR="$1"
THEME="$2"
SOUNDS_SOURCE="$ASSETS_DIR/sounds"

if [ -z "$THEME" ]; then
  echo "Error: No theme name provided"
  echo "Usage: install_sounds.sh <skill-assets-path> <theme-name>"
  echo ""
  echo "Available themes:"
  ls "$SOUNDS_SOURCE" | grep -v '\.'
  exit 1
fi

SOURCE_DIR="$SOUNDS_SOURCE/$THEME"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: Theme '$THEME' not found at $SOURCE_DIR"
  echo ""
  echo "Available themes:"
  ls "$SOUNDS_SOURCE" | grep -v '\.'
  exit 1
fi

mkdir -p .claude/sounds

for f in "$SOURCE_DIR"/*; do
  [ -f "$f" ] || continue
  name=$(basename "$f")
  ext="${name##*.}"
  base="${name%.*}"

  if [ "$ext" = "wav" ]; then
    cp "$f" ".claude/sounds/${base}.wav"
  else
    ffmpeg -i "$f" ".claude/sounds/${base}.wav" -y 2>/dev/null
  fi
done

echo "Installed sounds from '$THEME':"
ls -1 .claude/sounds/*.wav 2>/dev/null
