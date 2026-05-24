import json
import os
import re
import sys
import argparse


def hex_to_ansi(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return ""
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"\x1b[38;2;{r};{g};{b}m"


def strip_jsonc_comments(text):
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _resolve_colors(cli_colors):
    if cli_colors and len(cli_colors) >= 3:
        return cli_colors[:3]
    cache_file = os.path.expanduser("~/.cache/paletteflow.txt")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            colors = [line.strip() for line in f if line.strip()]
            if len(colors) >= 3:
                return colors[:3]
    print("Error: Could not find 3 colors.", file=sys.stderr)
    sys.exit(1)


def run(colors=None):
    primary, secondary, accent = _resolve_colors(colors)

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

    config = json.loads(raw)

    if "display" not in config:
        config["display"] = {}
    config["display"]["color"] = hex_to_ansi(accent)

    if "logo" not in config:
        config["logo"] = {}
    if "color" not in config["logo"]:
        config["logo"]["color"] = {}
    config["logo"]["color"]["1"] = hex_to_ansi(secondary)
    config["logo"]["color"]["2"] = hex_to_ansi(accent)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print("Updated fastfetch config")


def main():
    parser = argparse.ArgumentParser(
        description="Update fastfetch ANSI colors from extracted palette."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Three hex colors (primary secondary accent). Reads from cache if omitted.",
    )
    args = parser.parse_args()
    run(args.colors)


if __name__ == "__main__":
    main()
