#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SOURCE_DIR="$SCRIPT_DIR/config"
TEMP_DIR="/tmp/dotfiles_install_$$"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Functions for formatted logs
msg() { echo -e "${CYAN}[*] $*${NC}"; }
warn() { echo -e "${YELLOW}[!] WARNING: $*${NC}" >&2; }
error() { echo -e "${RED}[X] ERROR: $*${NC}" >&2; exit 1; }
success() { echo -e "${GREEN}[✓] $*${NC}"; }

trap "rm -rf $TEMP_DIR" EXIT

# Ensure we're not running as root, but can use sudo
if [ "$EUID" -eq 0 ]; then
    error "Do not run this script as root/sudo directly. Run it as a normal user. The script will ask for sudo when installing packages."
fi

clear
echo -e "${BLUE}"
echo "============================================================"
echo "    Sway WM Setup Restoration & Installer Script"
echo "============================================================"
echo -e "${NC}"

read -p "Begin restoration of your desktop setup? (y/n): " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && { msg "Installation cancelled."; exit 0; }

# 1. Add ButterRepo (Required for swayosd, autotiling, etc.)
msg "Adding ButterRepo APT repository..."
sudo apt-get update
sudo apt-get install -y curl gnupg wget

if [ ! -f /etc/apt/sources.list.d/butterrepo.list ] || [ ! -f /usr/share/keyrings/butterrepo.gpg ]; then
    curl -fsSL https://justaguylinux.codeberg.page/butterrepo/key.asc | sudo gpg --dearmor -o /usr/share/keyrings/butterrepo.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/butterrepo.gpg] https://justaguylinux.codeberg.page/butterrepo stable main" | sudo tee /etc/apt/sources.list.d/butterrepo.list
    sudo apt-get update
    success "ButterRepo added successfully."
else
    msg "ButterRepo is already configured."
fi

# 2. Package list compilation
PACKAGES=(
    # Core Window Manager & Display
    sway
    swaybg
    swayidle
    swaylock
    gtklock
    waybar
    xwayland
    build-essential
    lxpolkit
    
    # Sway Utilities & Services
    foot
    sway-notification-center
    autotiling
    grim
    slurp
    wl-clipboard
    cliphist
    brightnessctl
    playerctl
    wlr-randr
    xdg-desktop-portal-wlr
    swappy
    wtype
    wf-recorder
    wlsunset
    jq
    ffmpeg
    
    # Python support for custom scripts (autonaming, weather, etc.)
    python3
    python3-i3ipc
    python3-requests
    python3-pil
    python3-evdev
    
    # UI Customizations
    nwg-look
    xsettingsd
    network-manager-gnome
    kanshi
    eog
    nwg-displays
    rofi
    ghostty
    
    # File Manager
    thunar
    thunar-archive-plugin
    thunar-volman
    gvfs-backends
    dialog
    mtools
    smbclient
    cifs-utils
    unzip
    
    # Audio Controller
    pavucontrol
    pulsemixer
    pamixer
    pipewire-audio
    
    # Base Fonts
    fonts-recommended
    fonts-font-awesome
    fonts-noto-color-emoji
    fonts-symbola
    fonts-dejavu-core
    fonts-liberation
    fonts-material-design-icons-iconfont
    
    # Theme Compiling Engines
    cmake
    meson
    ninja-build
    pkg-config
    sassc
    gtk2-engines-murrine
    gtk2-engines-pixbuf
    gnome-themes-extra
    
    # General Utilities
    htop
    fastfetch
    vlc
    git
)

msg "Installing system packages (this might take a few minutes)..."
sudo apt-get install -y "${PACKAGES[@]}"

# Restore additional manually installed packages if apt_packages.txt exists
if [ -f "$SCRIPT_DIR/apt_packages.txt" ]; then
    msg "Found apt_packages.txt. Restoring additional manual packages..."
    EXTRA_PACKAGES=()
    while IFS= read -r pkg || [ -n "$pkg" ]; do
        # Ignore comments or empty lines
        [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue
        # Avoid installing duplicates
        if [[ ! " ${PACKAGES[@]} " =~ " ${pkg} " ]]; then
            EXTRA_PACKAGES+=("$pkg")
        fi
    done < "$SCRIPT_DIR/apt_packages.txt"
    
    if [ ${#EXTRA_PACKAGES[@]} -gt 0 ]; then
        msg "Attempting to install all additional packages at once..."
        if ! sudo apt-get install -y "${EXTRA_PACKAGES[@]}"; then
            warn "Bulk installation of additional packages failed. Retrying packages individually..."
            for pkg in "${EXTRA_PACKAGES[@]}"; do
                msg "Installing $pkg..."
                sudo apt-get install -y "$pkg" || warn "Could not install package: $pkg"
            done
        fi
    fi
fi

success "All system packages installed successfully."

# 3. Download & Install Nerd Fonts (referenced by ghostty/sway/waybar configs)
msg "Downloading and installing Nerd Fonts..."
mkdir -p "$TEMP_DIR"
FONT_VERSION="v3.4.0"
FONTS=(
    "JetBrainsMono"
    "SourceCodePro"
    "Lilex"
    "NerdFontsSymbolsOnly"
)
FONTS_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONTS_DIR"

for font in "${FONTS[@]}"; do
    if [ -d "$FONTS_DIR/$font" ] && [ -n "$(ls -A "$FONTS_DIR/$font" 2>/dev/null)" ]; then
        msg "  Nerd Font $font is already installed. Skipping."
    else
        msg "  Downloading $font Nerd Font..."
        if wget -q --timeout=30 "https://github.com/ryanoasis/nerd-fonts/releases/download/${FONT_VERSION}/${font}.zip" -P "$TEMP_DIR"; then
            mkdir -p "$FONTS_DIR/$font"
            unzip -q "$TEMP_DIR/${font}.zip" -d "$FONTS_DIR/$font/"
            msg "  Successfully installed $font."
            rm -f "$TEMP_DIR/${font}.zip"
        else
            warn "  Failed to download $font. You can install it manually later."
        fi
    fi
done

if command -v fc-cache &>/dev/null; then
    msg "Updating font cache..."
    fc-cache -f >/dev/null
fi
success "Fonts configuration complete."

# 4. Clone and install GTK Theme (Orchis)
msg "Checking Orchis GTK Theme..."
if [ ! -d "$HOME/.themes/Orchis-Orange-Dark" ]; then
    msg "Cloning and installing Orchis GTK Theme..."
    git clone --depth 1 https://github.com/vinceliuice/Orchis-theme.git "$TEMP_DIR/Orchis-theme"
    cd "$TEMP_DIR/Orchis-theme"
    ./install.sh -c dark -t orange -t grey -t green -t purple -t default --tweaks black nord dracula
    cd "$SCRIPT_DIR"
    success "Orchis theme installed."
else
    msg "Orchis theme is already installed."
fi

# 5. Clone and install Icon Theme (Colloid Icons)
msg "Checking Colloid Icon Theme..."
if [ ! -d "$HOME/.local/share/icons/Colloid-Dracula-Dark" ]; then
    msg "Cloning and installing Colloid Icon Theme..."
    git clone --depth 1 https://github.com/vinceliuice/Colloid-icon-theme.git "$TEMP_DIR/Colloid-icon-theme"
    cd "$TEMP_DIR/Colloid-icon-theme"
    ./install.sh -s dracula -t grey -t orange
    cd "$SCRIPT_DIR"
    success "Colloid icons installed."
else
    msg "Colloid icons are already installed."
fi

# 6. Apply configurations (with backing up existing ones)
msg "Restoring configuration files..."
TIMESTAMP=$(date +%s)

# Config directories to restore
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

mkdir -p "$HOME/.config"

for dir in "${CONFIG_DIRS[@]}"; do
    SRC="$CONFIG_SOURCE_DIR/$dir"
    DEST="$HOME/.config/$dir"
    
    if [ -d "$SRC" ]; then
        if [ -d "$DEST" ]; then
            msg "Backing up existing ~/.config/$dir to ~/.config/${dir}.bak.$TIMESTAMP"
            mv "$DEST" "${DEST}.bak.$TIMESTAMP"
        fi
        msg "Restoring config: ~/.config/$dir"
        cp -r "$SRC" "$DEST"
    fi
done

# Config files in ~/.config to restore
CONFIG_FILES=(
    "mimeapps.list"
    "pavucontrol.ini"
)

for file in "${CONFIG_FILES[@]}"; do
    SRC="$CONFIG_SOURCE_DIR/$file"
    DEST="$HOME/.config/$file"
    
    if [ -f "$SRC" ]; then
        if [ -f "$DEST" ]; then
            msg "Backing up existing ~/.config/$file to ~/.config/${file}.bak.$TIMESTAMP"
            mv "$DEST" "${DEST}.bak.$TIMESTAMP"
        fi
        msg "Restoring config file: ~/.config/$file"
        cp "$SRC" "$DEST"
    fi
done

# Home files to restore
HOME_FILES=(
    ".gtkrc-2.0"
    ".xsettingsd"
    ".profile"
)

for file in "${HOME_FILES[@]}"; do
    SRC="$CONFIG_SOURCE_DIR/dot${file}"
    DEST="$HOME/$file"
    
    if [ -f "$SRC" ]; then
        if [ -f "$DEST" ]; then
            msg "Backing up existing ~/$file to ~/${file}.bak.$TIMESTAMP"
            mv "$DEST" "${DEST}.bak.$TIMESTAMP"
        fi
        msg "Restoring home file: ~/$file"
        cp "$SRC" "$DEST"
    fi
done

# Restore swaylock PAM configuration
PAM_SRC="$CONFIG_SOURCE_DIR/swaylock.pam"
if [ -f "$PAM_SRC" ]; then
    msg "Restoring swaylock PAM config..."
    sudo cp "$PAM_SRC" /etc/pam.d/swaylock
    sudo chmod 644 /etc/pam.d/swaylock
fi

# Restore modem steps file
MODEM_SRC="$SCRIPT_DIR/stepForModem.txt"
if [ -f "$MODEM_SRC" ]; then
    msg "Restoring ~/stepForModem.txt..."
    cp "$MODEM_SRC" "$HOME/stepForModem.txt"
fi

# 7. Symlink setup for apps requiring default configurations
msg "Creating application symlinks..."
ln -sf ~/.config/sway/gtklock ~/.config/gtklock
ln -sf ~/.config/sway/foot ~/.config/foot
success "Symlinks created."

# 8. Create user directories
msg "Setting up user directories..."
xdg-user-dirs-update
mkdir -p "$HOME/Pictures/screenshots"
mkdir -p "$HOME/Videos"
success "User directories set up."

# 9. Restore custom TrackPoint scroll/click mapper service
TRACKPOINT_SERVICE_SRC="$SCRIPT_DIR/trackpoint-scroll.service"
if [ -f "$TRACKPOINT_SERVICE_SRC" ] && [ -f "$SCRIPT_DIR/trackpoint_space_scroll.py" ]; then
    msg "Restoring TrackPoint scroll/click service..."
    # Copy script to $HOME
    cp "$SCRIPT_DIR/trackpoint_space_scroll.py" "$HOME/trackpoint_space_scroll.py"
    chmod +x "$HOME/trackpoint_space_scroll.py"
    
    # Copy service file to a temporary location, update path if username/home is different, and copy to /etc/systemd/system/
    # We replace /home/saeedul with actual $HOME path
    sed "s|/home/saeedul|$HOME|g" "$TRACKPOINT_SERVICE_SRC" > "$TEMP_DIR/trackpoint-scroll.service"
    sudo cp "$TEMP_DIR/trackpoint-scroll.service" /etc/systemd/system/trackpoint-scroll.service
    sudo chmod 644 /etc/systemd/system/trackpoint-scroll.service
    
    # Disable keyd service if running to avoid conflicts
    if systemctl is-active --quiet keyd 2>/dev/null || systemctl is-enabled --quiet keyd 2>/dev/null; then
        msg "Disabling conflicting keyd service..."
        sudo systemctl stop keyd || true
        sudo systemctl disable keyd || true
    fi
    
    # Enable and start trackpoint-scroll service
    msg "Enabling and starting trackpoint-scroll service..."
    sudo systemctl daemon-reload
    sudo systemctl enable trackpoint-scroll.service
    sudo systemctl start trackpoint-scroll.service
    success "TrackPoint scroll/click mapper service setup complete."
else
    warn "TrackPoint scroll/click mapper service files not found, skipping."
fi

# Enable core system services
msg "Enabling background services..."
sudo systemctl enable avahi-daemon acpid || true
sudo systemctl start avahi-daemon acpid || true

echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}    Restoration complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo "Please log out of your current session and choose 'Sway' in your display manager."
echo "If you have an NVIDIA GPU, you may need to run setup scripts for hardware acceleration."
echo "Your wallpaper has been restored as self-contained in ~/.config/sway/wallpaper.png"
echo "Enjoy your setup!"
echo "============================================================"
