#!/bin/bash
# Automatically switch power profiles based on AC charger status

# Wait a split second for the kernel sysfs to update
sleep 0.5

STATUS=$(cat /sys/class/power_supply/AC/online)

if [ "$STATUS" = "1" ]; then
    /usr/bin/powerprofilesctl set performance
else
    /usr/bin/powerprofilesctl set balanced
fi
