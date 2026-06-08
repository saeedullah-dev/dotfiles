#!/usr/bin/env bash

# Sleep briefly to ensure Sway has initialized its sockets
sleep 1

# Export the current desktop environment
export XDG_CURRENT_DESKTOP=sway

# Stop any running portals from the previous session to force them to restart with the new env
systemctl --user stop xdg-desktop-portal xdg-desktop-portal-wlr xdg-desktop-portal-gtk 2>/dev/null || true

# Import variables to systemd/dbus
systemctl --user import-environment DISPLAY WAYLAND_DISPLAY SWAYSOCK XDG_CURRENT_DESKTOP
dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY SWAYSOCK XDG_CURRENT_DESKTOP

# Start them up again
systemctl --user start xdg-desktop-portal xdg-desktop-portal-wlr xdg-desktop-portal-gtk 2>/dev/null || true
