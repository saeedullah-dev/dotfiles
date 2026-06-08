# Saeedul's Sway Dotfiles & Setup

This repository contains my personal configurations for a beautiful, Gruvbox-themed Sway Window Manager environment, along with scripts to backup and restore the setup from scratch.

## 🌟 Features Included
*   **Window Manager**: Sway (Wayland tiling WM)
*   **Bar**: Waybar (customized status bar with system modules)
*   **Terminals**: Alacritty & Ghostty (fully styled)
*   **Launcher**: Rofi (application launcher & menus)
*   **Theme & Icons**: Orchis GTK Theme & Colloid Icon Theme
*   **Utilities**: SwayOSD (brightness/volume OSD), Kanshi (display profiles), Mako/SwayNC (notifications), Cliphist (clipboard manager), and custom script helpers.
*   **Fonts**: JetBrainsMono Nerd Font, FontAwesome, etc.
*   **Custom scripts**: Night light (`sunset.sh`), blur lockscreen (`lock-wrapper.sh`), autonaming workspaces, and system bar components.

---

## 💾 How to Backup Changes
If you modify any configurations on your system (e.g. keybindings, waybar colors, terminal themes), you can update this dotfiles folder by running the backup script:

```bash
cd ~/dotfiles
./backup.sh
```

This will copy all the active system configurations from `~/.config` and `~/` back into the `config/` directory here.

---

## 🚀 How to Restore on a Clean OS
To replicate this exact environment on a fresh installation of Ubuntu (or other Debian-based distributions):

1.  **Clone this repository** (or copy this folder to the new system):
    ```bash
    git clone https://github.com/saeedullah-dev/dotfiles.git ~/dotfiles
    ```
2.  **Run the restore script**:
    ```bash
    cd ~/dotfiles
    chmod +x install.sh
    ./install.sh
    ```

### What the installer does:
1.  Adds the **ButterRepo** APT repository (for swayosd, rofi-wayland, ghostty, etc.).
2.  Installs all required **Apt Packages** (WM core, audio controllers, python binders, build tools).
3.  Downloads and installs **JetBrainsMono** and other **Nerd Fonts** into `~/.local/share/fonts`.
4.  Clones and compiles the **Orchis Theme** and **Colloid Icons**.
5.  **Copies configurations** into `~/.config` and `~` (backing up any pre-existing configs to `.bak.<timestamp>`).
6.  Sets up standard **Symlinks** and background services.
