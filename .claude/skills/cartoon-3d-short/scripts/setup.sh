#!/usr/bin/env bash
# One-time setup for a new cartoon-3d-short project.
# Usage: scripts/setup.sh <project-dir> [<tts-model-dir>]
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
PROJ="${1:?project dir}"; TTS="${2:-$PROJ/.tts}"
mkdir -p "$PROJ" "$TTS"
cp -n "$SKILL"/template/{index.html,render.mjs,voice.py,audio.py} "$PROJ"/
cd "$PROJ"
[ -f package.json ] || npm init -y >/dev/null
npm i -s three@0.170.0 @fontsource/nunito@5.1.0 >/dev/null
printf "node_modules/\nframes/\n*.wav\n*.log\n.tts/\n" > .gitignore
python3 -c "import kokoro_onnx, soundfile, numpy" 2>/dev/null || pip install -q kokoro-onnx soundfile numpy
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s "$TTS/$f" ] || curl -sSL -o "$TTS/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
done
echo "ready: $PROJ  (voice models in $TTS)"
