#!/bin/bash

# Fetches the demo soundboard sounds (CC0 / public domain, sourced from freesound.org)
# and normalizes them for the homepage demo board.
#
# Sources (all Creative Commons 0):
#   airhorn        https://freesound.org/s/547020/  "DJ Airhorn"
#   vine_boom      https://freesound.org/s/802074/  "Drama Boom 02"
#   bruh           https://freesound.org/s/534387/  "Bruh Sound Effect #1"
#   sad_trombone   https://freesound.org/s/175409/  "wah wah sad trombone"
#   badum_tss      https://freesound.org/s/132418/  "Rimshot (sweet)"
#   record_scratch https://freesound.org/s/71853/   "record_scratch.wav"
#   dun_dun_dun    https://freesound.org/s/215558/  "Dun Dun Duuun v.01"
#   crickets       https://freesound.org/s/751468/  "Crickets chirping at Night 001"
#
# honey_badger.mp3 is NOT downloaded: no properly licensed recording of the meme
# exists, so it was synthesized locally with Piper TTS (MIT) using the CC BY 4.0
# en_US-libritts_r voice and committed to the repo:
#   echo "Honey badger don't care!" | piper -m en_US-libritts_r-medium.onnx \
#       -s 3 --length-scale 1.35 -f honey_badger.wav
# This script leaves the committed file untouched.
#
# If a download fails (e.g. no network), falls back to generating a placeholder tone.

set -u

# Directory to save sounds
TARGET_DIR="app/static/demo_sounds"
mkdir -p "$TARGET_DIR"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Fetching demo sounds into $TARGET_DIR..."

# Download a URL to a file with whichever tool is available (curl, wget, or python3)
download() {
    url=$1
    out=$2

    if command -v curl > /dev/null; then
        curl -fsSL --max-time 60 -A "Mozilla/5.0" -o "$out" "$url"
    elif command -v wget > /dev/null; then
        wget -q -T 60 -U "Mozilla/5.0" -O "$out" "$url"
    else
        python3 - "$url" "$out" <<'PYEOF'
import sys, urllib.request
req = urllib.request.Request(sys.argv[1], headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as r, open(sys.argv[2], "wb") as f:
    f.write(r.read())
PYEOF
    fi
}

# Fallback: generate a placeholder tone (offline mode)
gen_tone() {
    name=$1
    freq=$2

    echo "  WARNING: download failed for $name.mp3 - generating $freq Hz placeholder tone instead."
    ffmpeg -y -f lavfi -i "sine=frequency=$freq:duration=1" -q:a 2 "$TARGET_DIR/$name.mp3" > /dev/null 2>&1
}

# Download a sound and normalize it: optional trim/fade, loudness-normalize, 44.1 kHz mp3.
# Args: name, url, fallback_freq, [max_seconds]
fetch_sound() {
    name=$1
    url=$2
    fallback_freq=$3
    max_seconds=${4:-}

    echo "Fetching $name.mp3..."
    if ! download "$url" "$TMP_DIR/$name.src"; then
        gen_tone "$name" "$fallback_freq"
        return
    fi

    filters="loudnorm=I=-16:TP=-1.5:LRA=11"
    if [ -n "$max_seconds" ]; then
        fade_start=$((max_seconds - 1))
        filters="atrim=0:$max_seconds,afade=t=out:st=$fade_start:d=1,$filters"
    fi

    if ! ffmpeg -y -i "$TMP_DIR/$name.src" -af "$filters" -ar 44100 -q:a 2 \
            "$TARGET_DIR/$name.mp3" > /dev/null 2>&1; then
        gen_tone "$name" "$fallback_freq"
    fi
}

fetch_sound "airhorn"        "https://cdn.freesound.org/previews/547/547020_7295304-hq.mp3"   440
fetch_sound "vine_boom"      "https://cdn.freesound.org/previews/802/802074_15956618-hq.mp3"  100
fetch_sound "bruh"           "https://cdn.freesound.org/previews/534/534387_11868930-hq.mp3"  200
fetch_sound "sad_trombone"   "https://cdn.freesound.org/previews/175/175409_1326576-hq.mp3"   300
fetch_sound "badum_tss"      "https://cdn.freesound.org/previews/132/132418_2412414-hq.mp3"   500
fetch_sound "record_scratch" "https://cdn.freesound.org/previews/71/71853_1062668-hq.mp3"     700
fetch_sound "dun_dun_dun"    "https://cdn.freesound.org/previews/215/215558_4031177-hq.mp3"   150 5
fetch_sound "crickets"       "https://cdn.freesound.org/previews/751/751468_801011-hq.mp3"    800 5

echo "Demo sound fetch complete."
ls -lh "$TARGET_DIR"
