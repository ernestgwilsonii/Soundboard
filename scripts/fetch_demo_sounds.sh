#!/bin/bash

# Directory to save sounds
TARGET_DIR="app/static/demo_sounds"
mkdir -p "$TARGET_DIR"

echo "Generating placeholder demo sounds in $TARGET_DIR using ffmpeg..."

# Function to generate a tone
gen_tone() {
    name=$1
    freq=$2
    duration=1
    
    echo "Generating $name.mp3 ($freq Hz)..."
    ffmpeg -y -f lavfi -i "sine=frequency=$freq:duration=$duration" -q:a 2 "$TARGET_DIR/$name.mp3" > /dev/null 2>&1
}

gen_tone "airhorn" 440
gen_tone "crickets" 800
gen_tone "sad_violin" 300
gen_tone "vine_boom" 100
gen_tone "wow" 600
gen_tone "bruh" 200

echo "Placeholder generation complete."
ls -lh "$TARGET_DIR"
