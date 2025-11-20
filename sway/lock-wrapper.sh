#!/usr/bin/env bash
# ~/.config/sway/lock-wrapper.sh

# Exit if swaylock is already running

# Run swaylock with blur, clock, and indicator
swaylock \
    -f \
    --screenshots \
    --effect-blur 7x5 \
    --indicator \
    --clock \
    --timestr "%I:%M:%S" \
    -c 282828   # fallback background color

