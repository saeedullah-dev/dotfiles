#!/usr/bin/env bash
# ~/.config/sway/lock-wrapper.sh

# Exit if swaylock is already running
if pgrep -x "swaylock" > /dev/null; then
    exit 0
fi

# Paths for screenshots
IMAGE="/tmp/swaylock_screen.png"
BLURRED_IMAGE="/tmp/swaylock_blur.png"

# Take a screenshot of the current workspace
grim "$IMAGE"

# Fast and beautiful glassmorphic blur via ffmpeg (downscale, blur, upscale)
ffmpeg -y -i "$IMAGE" -vf "scale=iw/4:-1,gblur=sigma=5,scale=4*iw:-1" "$BLURRED_IMAGE" 2>/dev/null

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
    --indicator-thickness 7

# Clean up blurred image on unlock
rm -f "$BLURRED_IMAGE"


