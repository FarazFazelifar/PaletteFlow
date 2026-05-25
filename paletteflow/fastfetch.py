import json
import os
import sys
import tempfile

from paletteflow.color_utils import (
    blend,
    get_brightness,
    ROLES,
)


PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
PALETTE_JSON = os.path.expanduser("~/.cache/paletteflow.json")


def _write_atomic(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".",
                                prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.rename(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def hex_to_ansi(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return ""
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"\x1b[38;2;{r};{g};{b}m"


def strip_jsonc_comments(text):
    result = []
    in_string = False
    i = 0
    while i < len(text):
        if text[i] == '"' and (i == 0 or text[i - 1] != "\\"):
            in_string = not in_string
        elif text[i : i + 2] == "//" and not in_string:
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        elif text[i : i + 2] == "/*" and not in_string:
            i += 2
            while i < len(text) and text[i : i + 2] != "*/":
                i += 1
            i += 2
            continue
        result.append(text[i])
        i += 1
    return "".join(result)


def _resolve_palette(cli_colors):
    if cli_colors and len(cli_colors) >= 3:
        colors = cli_colors[:6]
    elif os.path.exists(PALETTE_JSON):
        with open(PALETTE_JSON) as f:
            data = json.load(f)
        keys = ROLES
        colors = [data.get(k) for k in keys if data.get(k)]
        if len(colors) < 3:
            colors = None
    else:
        colors = None

    if not colors and os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE) as f:
            colors = [line.strip() for line in f if line.strip()]
        colors = colors[:6]

    if not colors or len(colors) < 3:
        print("Error: Could not find 3 colors.", file=sys.stderr)
        sys.exit(1)

    return colors


def run(colors=None):
    palette = _resolve_palette(colors)

    bg = palette[0]
    surface = palette[1] if len(palette) > 1 else blend(bg, "#FFFFFF", 0.15)
    primary = palette[2] if len(palette) > 2 else bg
    secondary = palette[3] if len(palette) > 3 else primary
    accent = palette[4] if len(palette) > 4 else primary
    fg = palette[5] if len(palette) > 5 else "#FFFFFF"

    config_dir = os.path.expanduser("~/.config/fastfetch")
    config_path = os.path.join(config_dir, "config.jsonc")
    if not os.path.exists(config_path):
        config_path = os.path.join(config_dir, "config.json")
        if not os.path.exists(config_path):
            print("Error: Fastfetch config not found.", file=sys.stderr)
            sys.exit(1)

    with open(config_path) as f:
        raw = f.read()

    if config_path.endswith(".jsonc"):
        raw = strip_jsonc_comments(raw)

    config = json.loads(raw, strict=False)

    # Display colors
    if "display" not in config:
        config["display"] = {}
    # Use the lightest wallpaper colour for text so it's visible on any terminal bg
    lightest = max((bg, surface, primary, secondary, accent), key=get_brightness)
    config["display"]["color"] = hex_to_ansi(lightest)
    config["display"]["separator"] = " : "
    config["display"]["key"] = {"color": hex_to_ansi(accent)}

    # Logo colors — use palette
    config["logo"] = config.get("logo", {})
    config["logo"]["color"] = config["logo"].get("color", {})

    logo_colors = {
        "1": accent,
        "2": primary,
        "3": secondary,
        "4": surface,
        "5": lightest,
        "6": bg,
    }

    for key, val in logo_colors.items():
        config["logo"]["color"][key] = hex_to_ansi(val)

    _write_atomic(config_path, json.dumps(config, indent=2) + "\n")

    print("Updated fastfetch config with rich palette")
    print(f"  Text: {lightest}")
    print(f"  Logo colors: {len(logo_colors)} colors applied")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Update fastfetch ANSI colors from extracted palette."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors (primary secondary accent). Reads from cache if omitted.",
    )
    args = parser.parse_args()
    run(args.colors)


if __name__ == "__main__":
    main()
