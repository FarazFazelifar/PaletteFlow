import os
import re
import sys
import argparse


def _resolve_colors(cli_colors):
    colors = [None] * 6
    cache_file = os.path.expanduser("~/.cache/paletteflow.txt")

    if cli_colors and len(cli_colors) >= 3:
        for i in range(min(6, len(cli_colors))):
            colors[i] = cli_colors[i]
    elif os.path.exists(cache_file):
        with open(cache_file) as f:
            extracted = [line.strip() for line in f if line.strip()]
            for i in range(min(6, len(extracted))):
                colors[i] = extracted[i]

    if not all(colors[:3]):
        print("Error: Not enough colors.", file=sys.stderr)
        sys.exit(1)

    for i in range(6):
        if not colors[i]:
            colors[i] = colors[0]
        if not colors[i].startswith("#"):
            colors[i] = f"#{colors[i]}"
    return colors


def run(colors=None):
    primary, secondary, accent, tertiary, quaternary, quinary = _resolve_colors(colors)

    config_path = os.path.expanduser("~/.config/cava/config")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    if not os.path.exists(config_path):
        open(config_path, "a").close()

    with open(config_path) as f:
        lines = f.readlines()

    settings = {
        "gradient": "1",
        "gradient_color_1": secondary,
        "gradient_color_2": accent,
        "gradient_color_3": tertiary,
        "gradient_color_4": quaternary,
        "gradient_color_5": quinary,
        "gradient_color_6": secondary,
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


def main():
    parser = argparse.ArgumentParser(
        description="Update Cava gradient colors from extracted palette."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Six hex colors. Reads from cache if omitted.",
    )
    args = parser.parse_args()
    run(args.colors)


if __name__ == "__main__":
    main()
