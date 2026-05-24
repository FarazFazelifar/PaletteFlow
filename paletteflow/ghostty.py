import os
import re
import sys
import argparse


def get_brightness(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (r * 299 + g * 587 + b * 114) / 1000


def get_contrasting_text_color(hex_color):
    return "#000000" if get_brightness(hex_color) > 128 else "#ffffff"


def ensure_contrast(hex_color, bg_is_dark):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    brightness = get_brightness(hex_color)
    if bg_is_dark and brightness < 110:
        r = int(r + (255 - r) * 0.4)
        g = int(g + (255 - g) * 0.4)
        b = int(b + (255 - b) * 0.4)
    elif not bg_is_dark and brightness > 140:
        r = int(r * 0.6)
        g = int(g * 0.6)
        b = int(b * 0.6)
    return f"#{r:02x}{g:02x}{b:02x}"


def _resolve_colors(cli_colors):
    colors = [None] * 6
    if cli_colors and len(cli_colors) >= 3:
        for i in range(min(6, len(cli_colors))):
            colors[i] = cli_colors[i]
    else:
        cache_file = os.path.expanduser("~/.cache/paletteflow.txt")
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                extracted = [line.strip() for line in f if line.strip()]
                for i in range(min(6, len(extracted))):
                    colors[i] = extracted[i]

    if not all(colors[:3]):
        print("Error: Could not find enough colors. At least 3 are required.", file=sys.stderr)
        sys.exit(1)

    for i in range(6):
        if not colors[i]:
            colors[i] = colors[0]
        if not colors[i].startswith("#"):
            colors[i] = f"#{colors[i]}"
    return colors


def run(colors=None):
    primary, secondary, accent, tertiary, quaternary, quinary = _resolve_colors(colors)

    config_path = os.path.expanduser("~/.config/ghostty/config")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    if not os.path.exists(config_path):
        open(config_path, "a").close()

    bg_is_dark = get_brightness(primary) <= 128
    text_color = get_contrasting_text_color(primary)
    safe_secondary = ensure_contrast(secondary, bg_is_dark)
    safe_accent = ensure_contrast(accent, bg_is_dark)
    safe_tertiary = ensure_contrast(tertiary, bg_is_dark)
    safe_quaternary = ensure_contrast(quaternary, bg_is_dark)
    safe_quinary = ensure_contrast(quinary, bg_is_dark)

    color_mappings = {
        "background": primary,
        "foreground": text_color,
        "selection-background": safe_secondary,
        "cursor-color": safe_accent,
        "palette = 1": safe_secondary,
        "palette = 2": safe_tertiary,
        "palette = 3": safe_accent,
        "palette = 4": safe_quaternary,
        "palette = 5": safe_quinary,
        "palette = 6": safe_secondary,
    }

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


def main():
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
