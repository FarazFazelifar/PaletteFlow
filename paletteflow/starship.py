import os
import sys
import argparse
import tomlkit

STARSHIP_CONFIG = os.path.expanduser("~/.config/starship.toml")
PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
PALETTE_NAME = "auto_theme"


def _brightness(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (r * 299 + g * 587 + b * 114) / 1000


def _resolve_colors(cli_colors):
    if cli_colors and len(cli_colors) >= 6:
        return cli_colors[:6]
    if os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE) as f:
            colors = [line.strip() for line in f if line.strip().startswith("#")]
            if len(colors) >= 6:
                return colors[:6]
            print(f"Error: Not enough colors in {PALETTE_FILE}.", file=sys.stderr)
            sys.exit(1)
    print("Error: No colors found. Run 'paletteflow extract' first.", file=sys.stderr)
    sys.exit(1)


def run(colors=None):
    extracted = _resolve_colors(colors)

    if not os.path.exists(STARSHIP_CONFIG):
        print(f"Error: Starship config not found at {STARSHIP_CONFIG}", file=sys.stderr)
        sys.exit(1)

    with open(STARSHIP_CONFIG) as f:
        doc = tomlkit.parse(f.read())

    if "palettes" not in doc:
        doc["palettes"] = tomlkit.table()
    if PALETTE_NAME not in doc["palettes"]:
        doc["palettes"][PALETTE_NAME] = tomlkit.table()

    # Ghostty uses extracted[0] (primary) as terminal background.
    # Starship must not re-use that same color — it would merge.
    # Use the remaining 5 colors, sorted by brightness descending,
    # so the brightest lands on "primary" (commonly used for text).
    pool = sorted(extracted[1:], key=_brightness, reverse=True)
    pool.append(pool[-1])

    names = ["primary", "secondary", "accent", "tertiary", "quaternary", "quinary"]
    for name, val in zip(names, pool):
        doc["palettes"][PALETTE_NAME][name] = val

    with open(STARSHIP_CONFIG, "w") as f:
        f.write(tomlkit.dumps(doc))

    print(f"Updated starship palette '{PALETTE_NAME}'")
    for name, val in zip(
        ["Primary", "Secondary", "Accent", "Tertiary", "Quaternary", "Quinary"],
        pool,
    ):
        print(f"  {name}: {val}")


def main():
    parser = argparse.ArgumentParser(
        description="Update starship prompt palette from extracted colors."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )
    args = parser.parse_args()
    run(args.colors)


if __name__ == "__main__":
    main()
