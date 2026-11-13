#!/usr/bin/env bash
# Render every frame in parallel, mix audio, encode the final MP4.
# Usage (from the project dir): scripts/render_all.sh [jobs=3] [out=short.mp4]
set -euo pipefail
JOBS="${1:-3}"; OUT="${2:-short.mp4}"
N=$(python3 -c "import json;print(round(json.load(open('timings.json'))['duration']*30))")
rm -rf frames; mkdir -p frames
Q=$(( (N + JOBS - 1) / JOBS ))
for k in $(seq 0 $((JOBS - 1))); do
  a=$((k * Q)); b=$(( (k + 1) * Q - 1 )); [ $b -ge $N ] && b=$((N - 1))
  node render.mjs $a $b > r$k.log 2>&1 &
done
wait
[ "$(ls frames | wc -l)" -eq "$N" ] || { echo "missing frames"; grep -i error r*.log; exit 1; }
python3 audio.py
ffmpeg -v error -y -framerate 30 -i frames/%04d.jpg -i audio.wav -af "loudnorm=I=-14:TP=-1.5:LRA=7" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -of compact "$OUT"
