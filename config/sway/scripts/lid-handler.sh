#!/usr/bin/env bash
# ~/.config/sway/scripts/lid-handler.sh

# Lock command (using the configured lock script)
echo "$(date): lid-handler.sh called with arg: $1" >> /tmp/lid-handler.log
LOCK_CMD="$HOME/.config/sway/lock-wrapper.sh"
DELAY=15
PID_FILE="/tmp/lid_lock_timer.pid"

# If lid is closed (lid:on)
if [ "$1" = "close" ]; then
    # Kill any existing lid timer to prevent duplicates
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
        fi
        rm -f "$PID_FILE"
    fi

    # Start a background timer
    (
        sleep "$DELAY"
        # Check if the lid is still closed
        if grep -q "closed" /proc/acpi/button/lid/*/state; then
            # Lock the screen
            $LOCK_CMD
            # Optional: Uncomment the line below if you set HandleLidSwitch=ignore 
            # in /etc/systemd/logind.conf and want to suspend after locking.
            # systemctl suspend
        fi
    ) &
    # Save the PID of the timer so we can cancel it if the lid is opened early
    echo $! > "$PID_FILE"

elif [ "$1" = "open" ]; then
    # Lid is opened (lid:off)
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
        fi
        rm -f "$PID_FILE"
    fi
fi
