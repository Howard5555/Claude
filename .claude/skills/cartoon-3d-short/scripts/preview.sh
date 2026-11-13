#!/usr/bin/env bash
# Render a handful of test frames and tile them into one image to check framing.
# Usage (from the project dir): scripts/preview.sh <out.jpg> <frame> [<frame> ...]
set -euo pipefail
OUT="$1"; shift
rm -rf frames; mkdir -p frames
for f in "$@"; do node render.mjs "$f" "$f" 2>&1 | grep -iv "^frame" || true; done
ffmpeg -v error -y -pattern_type glob -i 'frames/*.jpg' -vf "scale=270:480,tile=$#x1" -frames:v 1 "$OUT"
echo "$OUT"
