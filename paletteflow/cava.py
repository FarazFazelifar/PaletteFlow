import os
import re
import sys
import json

from paletteflow.color_utils import (
    get_brightness,
    is_dark,
    ensure_contrast,
    blend,
    ROLES,
)


PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
PALETTE_JSON = os.path.expanduser("~/.cache/paletteflow.json")


def _resolve_palette(cli_colors):
    if cli_colors and len(cli_colors) >= 3:
        return cli_colors[:6]
    if os.path.exists(PALETTE_JSON):
        with open(PALETTE_JSON) as f:
            data = json.load(f)
        keys = ROLES
        colors = [data.get(k) for k in keys if data.get(k)]
        if len(colors) >= 3:
            return colors
    if os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE) as f:
            colors = [line.strip() for line in f if line.strip()]
            if len(colors) >= 3:
                return colors[:6]
    print("Error: Not enough colors.", file=sys.stderr)
    sys.exit(1)


def run(colors=None):
    palette = _resolve_palette(colors)

    bg = palette[0]
    surface = palette[1]
    primary = palette[2]
    secondary = palette[3]
    accent = palette[4]
    fg = palette[5]

    # Cava gradient: dark to bright
    gradient = [
        surface,
        blend(secondary, bg, 0.5),
        blend(primary, bg, 0.3),
        primary,
        accent,
        fg,
    ]

    config_path = os.path.expanduser("~/.config/cava/config")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    if not os.path.exists(config_path):
        open(config_path, "a").close()

    with open(config_path) as f:
        lines = f.readlines()

    settings = {
        "gradient": "1",
        "gradient_color_1": gradient[0],
        "gradient_color_2": gradient[1],
        "gradient_color_3": gradient[2],
        "gradient_color_4": gradient[3],
        "gradient_color_5": gradient[4],
        "gradient_color_6": gradient[5],
    }

    if not any("[color]" in line for line in lines):
        lines.append("\n[color]\n")

    in_color_section = False
    for key, value in settings.items():
        key_found = False
        pattern = re.compile(rf"^\s*;?\s*{re.escape(key)}\s*=.*$")
        for i, line in enumerate(lines):
            if line.strip() == "[color]":
                in_color_section = True
            elif line.startswith("[") and line.strip() != "[color]":
                in_color_section = False
            if in_color_section and pattern.match(line):
                lines[i] = f"{key} = '{value}'\n"
                key_found = True
                break
        if not key_found:
            for i, line in enumerate(lines):
                if line.strip() == "[color]":
                    lines.insert(i + 1, f"{key} = '{value}'\n")
                    break

    with open(config_path, "w") as f:
        f.writelines(lines)

    print("Updated Cava audio visualizer gradient")
    print(f"  Gradient: {' → '.join(gradient)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Update Cava gradient colors from extracted palette."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )
    args = parser.parse_args()
    run(args.colors)


if __name__ == "__main__":
    main()
