#!/usr/bin/env bash
# ~/.config/sway/lock-wrapper.sh

# Exit if swaylock is already running
if pgrep -x "swaylock" > /dev/null; then
    exit 0
fi

LOG_FILE="/tmp/swaylock.log"
echo "=== Lock attempt at $(date) ===" > "$LOG_FILE"

IMAGE="/tmp/swaylock_screen.png"
BLURRED_IMAGE="/tmp/swaylock_blur.png"

# Take screenshot in PNG format (since JPEG is disabled in your grim build)
grim "$IMAGE" >> "$LOG_FILE" 2>&1
echo "grim exit code: $?" >> "$LOG_FILE"

# Super-fast smooth blur using downscaling, boxblur, and zero PNG compression (takes ~0.4s)
ffmpeg -y -i "$IMAGE" -vf "scale=iw/8:-1,boxblur=5:2,scale=8*iw:-1" -compression_level 0 "$BLURRED_IMAGE" >> "$LOG_FILE" 2>&1
echo "ffmpeg exit code: $?" >> "$LOG_FILE"

# Clean up raw screenshot immediately
rm -f "$IMAGE"

# Run swaylock with Gruvbox themed color scheme
swaylock \
    -f \
    -i "$BLURRED_IMAGE" \
    --scaling fill \
    --show-failed-attempts \
    --inside-color 282828c0 \
    --inside-ver-color 458588c0 \
    --inside-wrong-color cc241dc0 \
    --inside-clear-color 689d6ac0 \
    --ring-color a89984 \
    --ring-ver-color 458588 \
    --ring-wrong-color cc241d \
    --ring-clear-color 689d6a \
    --line-color 00000000 \
    --key-hl-color ebdbb2 \
    --bs-hl-color cc241d \
    --text-color ebdbb2 \
    --text-ver-color ebdbb2 \
    --text-wrong-color ebdbb2 \
    --text-clear-color ebdbb2 \
    --indicator-radius 100 \
    --indicator-thickness 7 >> "$LOG_FILE" 2>&1

echo "swaylock exit code: $?" >> "$LOG_FILE"

# Clean up blurred image on unlock
rm -f "$BLURRED_IMAGE"
