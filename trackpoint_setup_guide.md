# TrackPoint Scroll Emulation & Key Mapper Setup Guide

This guide shows you how to back up your current setup and restore it on a clean Linux installation in the future.

---

## Part 1: Files to Back Up
To keep your configuration, you need to back up **two files**:
1. Your Python script: `~/dotfiles/trackpoint_space_scroll.py`
2. This guide: `~/dotfiles/trackpoint_setup_guide.md`

Since they are both in your `~/dotfiles` directory, copying or backing up your `dotfiles` folder will automatically back them up.

---

## Part 2: Restoring on a Clean Linux Installation

Follow these steps on your new Linux system to set everything up:

### Step 1: Install Python and evdev Dependency
Open your terminal and run:
```bash
sudo apt update
sudo apt install -y python3 python3-evdev
```

### Step 2: Identify Your Keyboard & TrackPoint Names
The script identifies your devices by their names:
* `AT Translated Set 2 keyboard`
* `TPPS/2 Elan TrackPoint`

If you are using the same laptop, these names will be identical. If you are on a different laptop:
1. Run this command to list your input devices:
   ```bash
   cat /proc/bus/input/devices | grep Name
   ```
2. Open `trackpoint_space_scroll.py` and verify/update the target names near the top of the file:
   ```python
   KEYBOARD_NAME = "Your Keyboard Name Here"
   TRACKPOINT_NAME = "Your TrackPoint Name Here"
   ```

### Step 3: Create the Systemd Service
To make the script run in the background automatically on startup:
1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/trackpoint-scroll.service
   ```
2. Paste the following configuration inside the file:
   ```ini
   [Unit]
   Description=Trackpoint Scroll Emulation and Key Mapper
   After=multi-user.target

   [Service]
   Type=simple
   ExecStart=/usr/bin/python3 -u /home/saeedul/dotfiles/trackpoint_space_scroll.py
   Restart=always
   RestartSec=2
   User=root

   [Install]
   WantedBy=multi-user.target
   ```
   *(Note: Make sure the `ExecStart` path matches the location where you put your script, e.g., `/home/saeedul/dotfiles/trackpoint_space_scroll.py`)*

### Step 4: Enable and Start the Service
Enable the service so it runs on boot, and start it immediately:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trackpoint-scroll.service
sudo systemctl start trackpoint-scroll.service
```

### Step 5: Verify it is Running
To verify the service is running and has successfully grabbed your keyboard and trackpoint:
```bash
sudo systemctl status trackpoint-scroll.service
```
You should see `Active: active (running)` and logs showing it successfully found both devices.
