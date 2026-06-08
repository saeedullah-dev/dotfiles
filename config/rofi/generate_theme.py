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
    
    # Accent colors selection using vibrancy = sat * (max_c / 255)
    colors_by_vibrancy = sorted(colors, key=lambda c: get_saturation(c) * (max(c) / 255.0), reverse=True)
    max_vibrancy = get_saturation(colors_by_vibrancy[0]) * (max(colors_by_vibrancy[0]) / 255.0)
    
    if max_vibrancy < 0.08:
        # Fallback to nice accents for monochrome images
        accent1_adjusted = (137, 180, 250) # Catppuccin mocha blue
        accent2_adjusted = (243, 139, 168) # Catppuccin mocha pink/red
    else:
        accent1 = colors_by_vibrancy[0]
        acc1_lum = get_luminance(accent1)
        if acc1_lum < 90:
            accent1_adjusted = adjust_luminance(accent1, 95)
        elif acc1_lum > 170:
            accent1_adjusted = adjust_luminance(accent1, 160)
        else:
            accent1_adjusted = accent1
            
        # Find accent2 that is distinct from accent1 if possible
        accent2 = colors_by_vibrancy[1] if len(colors_by_vibrancy) > 1 else accent1
        acc2_lum = get_luminance(accent2)
        if acc2_lum < 130:
            accent2_adjusted = adjust_luminance(accent2, 135)
        elif acc2_lum > 210:
            accent2_adjusted = adjust_luminance(accent2, 195)
        else:
            accent2_adjusted = accent2

    # Save wallpaper-colors.rasi
    rofi_dir = "/home/saeedul/.config/rofi"
    os.makedirs(rofi_dir, exist_ok=True)
    
    colors_file = os.path.join(rofi_dir, "wallpaper-colors.rasi")
    with open(colors_file, "w") as f:
        f.write("/* Dynamic wallpaper colors generated by generate_theme.py */\n")
        f.write("*\n")
        f.write("{\n")
        f.write(f"    bg-col:        {hex_color(bg)};\n")
        f.write(f"    bg-col-light:  {hex_color(bg_light)};\n")
        f.write(f"    selected-col:  {hex_color(selected)};\n")
        f.write(f"    border-col:    {hex_color(border)};\n")
        f.write(f"    blue:          {hex_color(accent1_adjusted)};\n")
        f.write(f"    fg-col2:       {hex_color(accent2_adjusted)};\n")
        f.write(f"    fg-col:        {hex_color(fg)};\n")
        f.write(f"    grey:          {hex_color(grey)};\n")
        f.write("}\n")
        
    print(f"Saved wallpaper colors to {colors_file}")

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

if __name__ == "__main__":
    main()
