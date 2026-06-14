#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Target directory for backups
DOTFILES_DIR="$HOME/dotfiles"
BACKUP_CONFIG_DIR="$DOTFILES_DIR/config"

echo "=========================================="
echo " Starting Dotfiles Backup Script"
echo "=========================================="

# Create necessary directories
mkdir -p "$BACKUP_CONFIG_DIR"

# List of configuration directories to back up (from ~/.config)
CONFIG_DIRS=(
    "alacritty"
    "ghostty"
    "gtk-3.0"
    "gtk-4.0"
    "nwg-bar"
    "nwg-displays"
    "nwg-look"
    "rofi"
    "sway"
    "swayosd"
    "waybar"
    "xsettingsd"
)

# Backup each configuration directory if it exists
for dir in "${CONFIG_DIRS[@]}"; do
    SRC="$HOME/.config/$dir"
    DEST="$BACKUP_CONFIG_DIR/$dir"
    
    if [ -d "$SRC" ]; then
        echo "Backing up: ~/.config/$dir"
        rm -rf "$DEST"
        cp -r "$SRC" "$DEST"
    else
        echo "Warning: ~/.config/$dir does not exist, skipping."
    fi
done

# Backup specific configuration files in ~/.config
CONFIG_FILES=(
    "mimeapps.list"
    "pavucontrol.ini"
)

for file in "${CONFIG_FILES[@]}"; do
    SRC="$HOME/.config/$file"
    DEST="$BACKUP_CONFIG_DIR/$file"
    
    if [ -f "$SRC" ]; then
        echo "Backing up: ~/.config/$file"
        cp "$SRC" "$DEST"
    else
        echo "Warning: ~/.config/$file does not exist, skipping."
    fi
done

# Backup individual files from home directory
HOME_FILES=(
    ".gtkrc-2.0"
    ".xsettingsd"
    ".profile"
)

for file in "${HOME_FILES[@]}"; do
    SRC="$HOME/$file"
    # To keep files tidy, we'll store home files prefixed with dot_ in config root
    DEST="$BACKUP_CONFIG_DIR/dot${file}"
    
    if [ -f "$SRC" ]; then
        echo "Backing up: ~/$file"
        cp "$SRC" "$DEST"
    else
        echo "Warning: ~/$file does not exist, skipping."
    fi
done

# Backup wallpaper and make it self-contained
ENV_CONF_SRC="$HOME/.config/sway/config.d/00_env"
WALLPAPER_SRC=""
if [ -f "$ENV_CONF_SRC" ]; then
    RAW_PATH=$(grep -E '^\s*set\s+\$wallpaper\s+' "$ENV_CONF_SRC" | head -n 1 | awk '{print $3}')
    if [ ! -z "$RAW_PATH" ]; then
        WALLPAPER_SRC=$(eval echo "$RAW_PATH")
    fi
fi

WALLPAPER_DEST="$BACKUP_CONFIG_DIR/sway/wallpaper.png"

if [ -f "$WALLPAPER_SRC" ]; then
    echo "Backing up wallpaper: $WALLPAPER_SRC -> sway/wallpaper.png"
    cp "$WALLPAPER_SRC" "$WALLPAPER_DEST"
    
    # Update the wallpaper configuration path in the backed up config file
    ENV_CONF="$BACKUP_CONFIG_DIR/sway/config.d/00_env"
    if [ -f "$ENV_CONF" ]; then
        echo "Updating wallpaper path in backed up 00_env..."
        # Replace the hardcoded absolute path with a relative path
        sed -i "s|set \$wallpaper .*|set \$wallpaper ~/.config/sway/wallpaper.png|" "$ENV_CONF"
    fi
else
    echo "Warning: Wallpaper '$WALLPAPER_SRC' not found, skipping."
fi

# Backup swaylock PAM configuration
if [ -f "/etc/pam.d/swaylock" ]; then
    echo "Backing up swaylock PAM config..."
    cp "/etc/pam.d/swaylock" "$BACKUP_CONFIG_DIR/swaylock.pam"
else
    echo "Warning: /etc/pam.d/swaylock not found, skipping."
fi

# Backup modem steps file
if [ -f "$HOME/stepForModem.txt" ]; then
    echo "Backing up modem steps..."
    cp "$HOME/stepForModem.txt" "$DOTFILES_DIR/stepForModem.txt"
else
    echo "Warning: ~/stepForModem.txt not found, skipping."
fi

# Backup custom TrackPoint scroll/click mapper service
if [ -f "$HOME/trackpoint_space_scroll.py" ]; then
    echo "Backing up TrackPoint scroll/click script..."
    cp "$HOME/trackpoint_space_scroll.py" "$DOTFILES_DIR/trackpoint_space_scroll.py"
fi

if [ -f "/etc/systemd/system/trackpoint-scroll.service" ]; then
    echo "Backing up trackpoint-scroll systemd service..."
    cp "/etc/systemd/system/trackpoint-scroll.service" "$DOTFILES_DIR/trackpoint-scroll.service"
fi

# Backup modem sleep wakeup script (iosm-resume)
if [ -f "/lib/systemd/system-sleep/iosm-resume" ]; then
    echo "Backing up modem sleep/resume script..."
    cp "/lib/systemd/system-sleep/iosm-resume" "$DOTFILES_DIR/iosm-resume"
fi

# Export list of manually installed packages
if command -v apt-mark &>/dev/null; then
    echo "Exporting list of manually installed APT packages..."
    apt-mark showmanual > "$DOTFILES_DIR/apt_packages.txt"
fi

echo "=========================================="
echo " Backup Completed successfully!"
echo " Files saved to: $DOTFILES_DIR"
echo "=========================================="
