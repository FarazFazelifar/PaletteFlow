import os
import re
import sys
import json

from paletteflow.color_utils import (
    get_brightness,
    hex_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
    hsl_to_rgb,
    contrast_ratio,
    ensure_contrast,
    is_dark,
    ROLES,
)


PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
PALETTE_JSON = os.path.expanduser("~/.cache/paletteflow.json")


def _resolve_palette(cli_colors):
    if cli_colors and len(cli_colors) >= 3:
        return _parse_cli_colors(cli_colors)
    if os.path.exists(PALETTE_JSON):
        with open(PALETTE_JSON) as f:
            data = json.load(f)
        if "bg" in data and "fg" in data and "accent" in data:
            return data
    if os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE) as f:
            colors = [line.strip() for line in f if line.strip()]
        keys = ROLES
        palette = {}
        for i, c in enumerate(colors):
            if i < len(keys):
                palette[keys[i]] = c
        return palette
    print("Error: Could not find palette. Run 'paletteflow extract' first.", file=sys.stderr)
    sys.exit(1)


def _parse_cli_colors(colors):
    colors = [c if c.startswith("#") else f"#{c}" for c in colors]
    keys = ROLES
    palette = {}
    for i, c in enumerate(colors):
        if i < len(keys):
            palette[keys[i]] = c
    return palette


def _ansi_from_accent(accent, bg, fg, surface):
    """Build ANSI 0-15 using the wallpaper's accent hue family."""
    r, g, b = hex_to_rgb(accent)
    accent_h, accent_s, _ = rgb_to_hsl(r, g, b)
    s = min(accent_s * 1.0, 0.75)
    bg_is_dark = is_dark(bg)

    def make(hue, sat, light):
        nr, ng, nb = hsl_to_rgb(hue, sat, light)
        return rgb_to_hex(nr, ng, nb)

    offsets = [0, 100, 50, -130, 110, -70]
    if bg_is_dark:
        bright_l = [0.38, 0.38, 0.42, 0.38, 0.38, 0.38]
        bright_br_l = [0.55, 0.55, 0.58, 0.55, 0.55, 0.55]
    else:
        bright_l = [0.50, 0.50, 0.55, 0.50, 0.50, 0.50]
        bright_br_l = [0.65, 0.65, 0.70, 0.65, 0.65, 0.65]

    ansi = {}

    # ANSI 0 = bg, ANSI 8 = slightly lighter bg
    ansi[0] = bg
    ansi[8] = surface

    # ANSI 1-6: darkened accent hues
    for idx, (off, l) in enumerate(zip(offsets, bright_l), start=1):
        hue = (accent_h + off) % 360
        ansi[idx] = make(hue, s, l)

    # ANSI 7 = mid-point blend of bg and fg
    ansi[7] = rgb_to_hex(
        *[int((a + b) / 2) for a, b in zip(hex_to_rgb(bg), hex_to_rgb(fg))]
    )

    # ANSI 9-14: brighter versions of 1-6
    for idx, (off, l) in enumerate(zip(offsets, bright_br_l), start=9):
        hue = (accent_h + off) % 360
        ansi[idx] = make(hue, s, l)

    # ANSI 15 = fg
    ansi[15] = fg

    return ansi


def run(colors=None):
    palette = _resolve_palette(colors)

    bg = palette.get("bg", "#1A1A1A")
    fg = palette.get("fg", "#FFFFFF")
    surface = palette.get("surface", "#2E2E2E")
    accent = palette.get("accent", "#4A90D9")

    # Build ANSI from the wallpaper's accent
    ansi = _ansi_from_accent(accent, bg, fg, surface)

    # Ensure every ANSI colour used as text is readable against the background
    for i in range(1, 16):
        ansi[i] = ensure_contrast(ansi[i], ansi[0], 3.0)

    # Ensure foreground and cursor are readable
    fg_safe = ensure_contrast(fg, bg, 7.0)
    sel_fg = ensure_contrast(fg_safe, surface, 4.5)
    cursor = ensure_contrast(accent, bg, 4.5)

    config_path = os.path.expanduser("~/.config/ghostty/config")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    color_mappings = {
        "background": bg,
        "foreground": fg_safe,
        "selection-background": surface,
        "selection-foreground": sel_fg,
        "cursor-color": cursor,
        "cursor-text": bg,
    }

    ansi_keys = [
        "palette = 0", "palette = 1", "palette = 2", "palette = 3",
        "palette = 4", "palette = 5", "palette = 6", "palette = 7",
        "palette = 8", "palette = 9", "palette = 10", "palette = 11",
        "palette = 12", "palette = 13", "palette = 14", "palette = 15",
    ]
    for key, idx in zip(ansi_keys, range(16)):
        color_mappings[key] = ansi[idx]

    lines = []
    if os.path.exists(config_path):
        with open(config_path) as f:
            lines = f.readlines()

    for key, value in color_mappings.items():
        key_found = False
        pattern = re.compile(rf"^{re.escape(key)}\s*=.*$")
        for i, line in enumerate(lines):
            if pattern.match(line.strip()):
                lines[i] = f"{key} = {value}\n"
                key_found = True
                break
        if not key_found:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(f"{key} = {value}\n")

    with open(config_path, "w") as f:
        f.writelines(lines)

    print("Updated Ghostty terminal config")
    print(f"  Background: {bg}, Foreground: {fg_safe}")
    print(f"  Cursor: {cursor}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Update Ghostty terminal colors from extracted palette."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )
    args = parser.parse_args()
    run(args.colors)


if __name__ == "__main__":
    main()
