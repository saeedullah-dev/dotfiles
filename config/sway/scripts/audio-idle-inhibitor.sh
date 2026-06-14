#!/bin/bash
# Prevent swayidle from locking the screen while audio is playing

# Kill other instances of this script, keeping only the current one
for pid in $(pgrep -f "audio-idle-inhibitor.sh"); do
    if [ "$pid" != "$$" ] && [ "$pid" != "$PPID" ]; then
        kill "$pid" 2>/dev/null
    fi
done

while true; do
    # Check if any audio card PCM subdevice is in RUNNING state
    if grep -q "RUNNING" /proc/asound/card*/pcm*/sub*/status 2>/dev/null; then
        # Simulate pressing left Shift key to reset idle timer
        /usr/bin/wtype -k Shift_L
    fi
    sleep 10
done
