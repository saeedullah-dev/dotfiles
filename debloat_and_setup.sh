#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

msg() { echo -e "${CYAN}[*] $*${NC}"; }
warn() { echo -e "${YELLOW}[!] WARNING: $*${NC}" >&2; }
error() { echo -e "${RED}[X] ERROR: $*${NC}" >&2; exit 1; }
success() { echo -e "${GREEN}[✓] $*${NC}"; }

# Ensure we're not running as root, but can use sudo
if [ "$EUID" -eq 0 ]; then
    error "Do not run this script as root/sudo directly. Run it as a normal user. The script will ask for sudo when needed."
fi

clear || true
echo -e "${BLUE}"
echo "============================================================"
echo "    Ubuntu Debloat: GNOME & Snap Removal + Sway Setup"
echo "============================================================"
echo -e "${NC}"

warn "This script will completely remove the GNOME desktop environment, GDM3 login manager, and Snap package manager. They will be replaced by a minimal LightDM login manager and your Sway setup."
read -p "Are you absolutely sure you want to proceed? (y/n): " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && { msg "Aborted."; exit 0; }

# 1. Fully remove Snap and block it
if command -v snap &>/dev/null; then
    msg "Removing active Snaps..."
    # Uninstall all snaps in order
    for snap in $(snap list | awk 'NR>1 {print $1}'); do
        sudo snap remove --purge "$snap" || true
    done
fi

if systemctl is-active --quiet snapd || systemctl is-enabled --quiet snapd; then
    msg "Stopping and disabling snapd services..."
    sudo systemctl stop snapd.socket snapd.service snapd.seeded.service || true
    sudo systemctl disable snapd.socket snapd.service snapd.seeded.service || true
fi

msg "Purging snapd packages..."
sudo apt-get purge -y snapd || true
sudo rm -rf /var/lib/snapd /var/snap ~/snap || true

msg "Blocking snapd from being reinstalled..."
sudo tee /etc/apt/preferences.d/nosnap.pref >/dev/null <<EOF
# To prevent repository packages from triggering the installation of snapd
Package: snapd
Pin: release a=*
Pin-Priority: -10
EOF
success "Snap fully removed and blocked."

# 2. Remove GNOME Desktop Environment and GDM3
msg "Purging GNOME desktop environment and GDM3 display manager..."
sudo apt-get purge -y ubuntu-desktop \
                     ubuntu-desktop-minimal \
                     gnome-shell \
                     gdm3 \
                     gnome-session \
                     gnome-control-center \
                     gnome-terminal \
                     yelp \
                     evolution \
                     seahorse || true

msg "Running autoremove to clean up unused GNOME packages..."
sudo apt-get autoremove --purge -y
success "GNOME desktop environment removed."

# 3. Configure console-only boot (TTY login)
msg "Configuring system to boot directly to command-line console (TTY)..."
sudo systemctl set-default multi-user.target
# Disable any existing display manager service to ensure it boots to console
sudo systemctl disable display-manager.service || true
success "Console-only boot (TTY login) configured successfully."

# 4. Trigger the Sway dotfiles installer
msg "Running your Sway and dotfiles installation script..."
cd "$(dirname "$0")"
./install.sh

success "Debloating and Sway setup complete! Please reboot your computer. After rebooting, log in via the TTY console and run 'sway' to start your desktop."
