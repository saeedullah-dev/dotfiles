#!/usr/bin/env python3
import sys
import os
import re
from PIL import Image

def hex_color(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def get_luminance(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]

def get_saturation(rgb):
    r, g, b = rgb
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    if max_c == 0:
        return 0
    return (max_c - min_c) / max_c

def adjust_luminance(rgb, target_lum):
    L = get_luminance(rgb)
    if L == 0:
        val = int(target_lum)
        return (val, val, val)
        
    scale = target_lum / L
    if max(rgb) * scale <= 255:
        r = int(rgb[0] * scale)
        g = int(rgb[1] * scale)
        b = int(rgb[2] * scale)
        return (r, g, b)
    else:
        # Mix with white to avoid clipping/raw primary colors
        t = (target_lum - L) / (255.0 - L)
        r = int(rgb[0] * (1 - t) + 255 * t)
        g = int(rgb[1] * (1 - t) + 255 * t)
        b = int(rgb[2] * (1 - t) + 255 * t)
        return (r, g, b)

def desaturate_and_brighten(rgb, target_lum):
    r, g, b = rgb
    # Mix with white to desaturate (85% white)
    r = int(r * 0.15 + 255 * 0.85)
    g = int(g * 0.15 + 255 * 0.85)
    b = int(b * 0.15 + 255 * 0.85)
    return adjust_luminance((r, g, b), target_lum)

def get_wallpaper_path():
    # 1. Check command line arguments
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            return path

    # 2. Check sway env config
    sway_env_path = "/home/saeedul/.config/sway/config.d/00_env"
    if os.path.exists(sway_env_path):
        try:
            with open(sway_env_path, "r") as f:
                content = f.read()
            # Match set $wallpaper <path>
            match = re.search(r"^\s*set\s+\$wallpaper\s+(\S+)", content, re.MULTILINE)
            if match:
                path = match.group(1).replace("~", "/home/saeedul")
                if os.path.exists(path):
                    return path
        except Exception as e:
            print(f"Warning reading sway env: {e}", file=sys.stderr)

    # 3. Fallbacks
    fallbacks = [
        "/home/saeedul/.config/sway/wallpaper.png",
        "/home/saeedul/.config/sway/hong5.png",
        "/home/saeedul/.config/sway/hong3.png",
        "/home/saeedul/.config/sway/hong4.png"
    ]
    for p in fallbacks:
        if os.path.exists(p):
            return p

    return None

def main():
    image_path = get_wallpaper_path()
    if not image_path:
        print("Error: Could not find any wallpaper image.", file=sys.stderr)
        sys.exit(1)

    print(f"Using wallpaper: {image_path}")

    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Resize to speed up quantization
    img = img.resize((150, 150))
    img = img.convert("RGB")
    
    # Quantize to 16 colors
    quantized = img.quantize(colors=16, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette()
    
    color_counts = quantized.getcolors()
    total_pixels = 150 * 150
    index_to_count = {index: count for count, index in color_counts}
    
    colors = []
    for i in range(16):
        r = palette[i*3]
        g = palette[i*3+1]
        b = palette[i*3+2]
        colors.append((r, g, b))
        
    # Sort by luminance to find darkest color
    colors_by_lum = sorted(colors, key=get_luminance)
    darkest = colors_by_lum[0]
    
    # Background color generation
    bg_lum = get_luminance(darkest)
    if bg_lum > 20:
        bg = adjust_luminance(darkest, 16)
    else:
        bg = adjust_luminance(darkest, max(10, bg_lum))
        
    bg_light = adjust_luminance(bg, get_luminance(bg) + 10)
    selected = adjust_luminance(bg, get_luminance(bg) + 20)
    border = adjust_luminance(bg, get_luminance(bg) + 32)
    
    # Text colors
    fg = desaturate_and_brighten(darkest, 225)
    grey = desaturate_and_brighten(darkest, 120)
    
    # Filter colors that represent a meaningful part of the image to avoid tiny accent details
    # like a small trackpoint dot or status bar icon.
    frequent_colors = []
    for threshold in [0.01, 0.005, 0.002, 0.001]:
        frequent_colors = [colors[i] for i in range(16) if index_to_count.get(i, 0) >= total_pixels * threshold]
        if len(frequent_colors) >= 3:
            break
            
    if not frequent_colors:
        frequent_colors = colors
        
    # Accent colors selection using vibrancy = sat * (max_c / 255)
    frequent_by_vibrancy = sorted(frequent_colors, key=lambda c: get_saturation(c) * (max(c) / 255.0), reverse=True)
    max_vibrancy = get_saturation(frequent_by_vibrancy[0]) * (max(frequent_by_vibrancy[0]) / 255.0)
    
    if max_vibrancy < 0.08:
        # Fallback to nice accents for monochrome/dark classic images (grey theme)
        accent1_adjusted = (152, 155, 162) # Premium cool slate grey accent
        accent2_adjusted = (209, 210, 213) # Premium silver/light-grey accent
    else:
        accent1 = frequent_by_vibrancy[0]
        acc1_lum = get_luminance(accent1)
        if acc1_lum < 90:
            accent1_adjusted = adjust_luminance(accent1, 95)
        elif acc1_lum > 170:
            accent1_adjusted = adjust_luminance(accent1, 160)
        else:
            accent1_adjusted = accent1
            
        # Find accent2 that is distinct from accent1 if possible
        accent2 = frequent_by_vibrancy[1] if len(frequent_by_vibrancy) > 1 else accent1
        acc2_lum = get_luminance(accent2)
        if acc2_lum < 130:
            accent2_adjusted = adjust_luminance(accent2, 135)
        elif acc2_lum > 210:
            accent2_adjusted = adjust_luminance(accent2, 195)
        else:
            accent2_adjusted = accent2

    # Prepare contents for the color files
    # 1. Rofi colors
    rofi_colors = f"""/* Dynamic wallpaper colors generated by generate_theme.py */
*
{{
    bg-col:        {hex_color(bg)};
    bg-col-light:  {hex_color(bg_light)};
    selected-col:  {hex_color(selected)};
    border-col:    {hex_color(border)};
    blue:          {hex_color(accent1_adjusted)};
    fg-col2:       {hex_color(accent2_adjusted)};
    fg-col:        {hex_color(fg)};
    grey:          {hex_color(grey)};
}}
"""

    # 2. Sway colors
    sway_colors = f"""# Dynamic wallpaper colors generated by generate_theme.py
set $bg      {hex_color(bg)}
set $fg      {hex_color(fg)}
set $black   {hex_color(bg_light)}
set $red     #e74c3c
set $green   #2ecc71
set $yellow  {hex_color(accent2_adjusted)}
set $blue    {hex_color(accent1_adjusted)}
set $purple  #b16286
set $aqua    {hex_color(grey)}
set $gray    {hex_color(grey)}
"""

    # 3. Waybar colors
    waybar_colors = f"""/* Dynamic wallpaper colors generated by generate_theme.py */
@define-color bg_col rgba({bg[0]}, {bg[1]}, {bg[2]}, 0.55);
@define-color fg_col {hex_color(fg)};
@define-color selected_col {hex_color(accent1_adjusted)};
@define-color alt_col {hex_color(accent2_adjusted)};
@define-color urgent_col #e74c3c;
@define-color green_col #2ecc71;
"""

    # File paths
    rofi_dir = "/home/saeedul/.config/rofi"
    os.makedirs(rofi_dir, exist_ok=True)
    colors_file = os.path.join(rofi_dir, "wallpaper-colors.rasi")

    sway_dir = "/home/saeedul/.config/sway/config.d"
    os.makedirs(sway_dir, exist_ok=True)
    sway_colors_file = os.path.join(sway_dir, "01_colors")

    waybar_dir = "/home/saeedul/.config/waybar"
    os.makedirs(waybar_dir, exist_ok=True)
    waybar_colors_file = os.path.join(waybar_dir, "colors.css")

    # Helper function to read file content
    def read_file(path):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return f.read()
            except:
                pass
        return ""

    # Check if any file needs updating
    updated = False
    if read_file(colors_file) != rofi_colors:
        with open(colors_file, "w") as f:
            f.write(rofi_colors)
        print(f"Saved wallpaper colors to {colors_file}")
        updated = True

    if read_file(sway_colors_file) != sway_colors:
        with open(sway_colors_file, "w") as f:
            f.write(sway_colors)
        print(f"Saved sway colors to {sway_colors_file}")
        updated = True

    if read_file(waybar_colors_file) != waybar_colors:
        with open(waybar_colors_file, "w") as f:
            f.write(waybar_colors)
        print(f"Saved waybar colors to {waybar_colors_file}")
        updated = True
    # Generate wallpaper.rasi (layout file that imports colors)
    layout_file = os.path.join(rofi_dir, "wallpaper.rasi")
    layout_content = """@import "/home/saeedul/.config/rofi/wallpaper-colors.rasi"

* {
    width: 750;
    font: "JetBrainsMono Nerd Font 16";
}

element-text, element-icon , mode-switcher {
    background-color: inherit;
    text-color:       inherit;
}

window {
    height: 440px;
    border: 0px;
    border-color: @border-col;
    background-color: @bg-col;
    border-radius: 12px;
}

mainbox {
    background-color: @bg-col;
}

inputbar {
    children: [prompt,entry];
    background-color: @bg-col;
    border-radius: 5px;
    padding: 2px;
}

prompt {
    background-color: @blue;
    padding: 6px;
    text-color: @bg-col;
    border-radius: 3px;
    margin: 20px 0px 0px 20px;
}

textbox-prompt-colon {
    expand: false;
    str: ":";
}

entry {
    padding: 6px;
    margin: 20px 0px 0px 10px;
    text-color: @fg-col;
    background-color: @bg-col;
}

listview {
    border: 0px 0px 0px;
    padding: 6px 0px 0px;
    margin: 10px 0px 0px 20px;
    columns: 2;
    lines: 7;
    background-color: @bg-col;
}

element {
    padding: 5px;
    background-color: @bg-col;
    text-color: @fg-col  ;
    border-radius: 6px;
}

element-icon {
    size: 25px;
}

element selected {
    background-color:  @selected-col ;
    text-color: @fg-col2  ;
}

mode-switcher {
    spacing: 0;
}

button {
    padding: 10px;
    background-color: @bg-col-light;
    text-color: @grey;
    vertical-align: 0.5; 
    horizontal-align: 0.5;
}

button selected {
    background-color: @bg-col;
    text-color: @blue;
}

message {
    background-color: @bg-col-light;
    margin: 2px;
    padding: 2px;
    border-radius: 5px;
}

textbox {
    padding: 6px;
    margin: 20px 0px 0px 20px;
    text-color: @blue;
    background-color: @bg-col-light;
}
"""
    with open(layout_file, "w") as f:
        f.write(layout_content)
        
    print(f"Saved layout to {layout_file}")

    # Update config.rasi to point to wallpaper.rasi
    config_file = os.path.join(rofi_dir, "config.rasi")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        theme_replaced = False
        for line in lines:
            if line.strip().startswith("@theme"):
                new_lines.append('@theme "/home/saeedul/.config/rofi/wallpaper.rasi"\n')
                theme_replaced = True
            else:
                new_lines.append(line)
        
        if not theme_replaced:
            new_lines.append('\n@theme "/home/saeedul/.config/rofi/wallpaper.rasi"\n')
            
        with open(config_file, "w") as f:
            f.writelines(new_lines)
            
        print(f"Updated {config_file} to point to wallpaper.rasi")
    else:
        # Create a new config.rasi if it doesn't exist
        with open(config_file, "w") as f:
            f.write("""configuration {
    modi: "run,window,combi";
    icon-theme: "Oranchelo";
    show-icons: true;
    terminal: "alacritty";
    drun-display-format: "{icon} {name}";
    location: 0;
    disable-history: false;
    hide-scrollbar: true;
    display-combi: " 🖥️  All ";
    display-run: " 🏃  Run ";
    display-window: " 🪟  Window";
    sidebar-mode: true;
}

@theme "/home/saeedul/.config/rofi/wallpaper.rasi"
""")
        print(f"Created new {config_file}")

    # If anything was updated, trigger Sway reload and signal Waybar to reload its styles
    if updated:
        print("Colors updated. Reloading Sway and signaling Waybar...")
        import subprocess
        # Signal Waybar to reload its stylesheet
        try:
            subprocess.run(["pkill", "-USR2", "waybar"], check=False)
        except Exception as e:
            print(f"Failed to signal waybar: {e}", file=sys.stderr)
        # Reload Sway config
        try:
            subprocess.run(["swaymsg", "reload"], check=False)
        except Exception as e:
            print(f"Failed to reload sway: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
