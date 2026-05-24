import os
import sys
import argparse
import tomlkit

STARSHIP_CONFIG = os.path.expanduser("~/.config/starship.toml")
PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
PALETTE_NAME = "auto_theme"


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
    primary, secondary, accent, tertiary, quaternary, quinary = _resolve_colors(colors)

    if not os.path.exists(STARSHIP_CONFIG):
        print(f"Error: Starship config not found at {STARSHIP_CONFIG}", file=sys.stderr)
        sys.exit(1)

    with open(STARSHIP_CONFIG) as f:
        doc = tomlkit.parse(f.read())

    if "palettes" not in doc:
        doc["palettes"] = tomlkit.table()
    if PALETTE_NAME not in doc["palettes"]:
        doc["palettes"][PALETTE_NAME] = tomlkit.table()

    doc["palettes"][PALETTE_NAME]["primary"] = primary
    doc["palettes"][PALETTE_NAME]["secondary"] = secondary
    doc["palettes"][PALETTE_NAME]["accent"] = accent
    doc["palettes"][PALETTE_NAME]["tertiary"] = tertiary
    doc["palettes"][PALETTE_NAME]["quaternary"] = quaternary
    doc["palettes"][PALETTE_NAME]["quinary"] = quinary

    with open(STARSHIP_CONFIG, "w") as f:
        f.write(tomlkit.dumps(doc))

    print(f"Updated starship palette '{PALETTE_NAME}'")
    for name, val in zip(
        ["Primary", "Secondary", "Accent", "Tertiary", "Quaternary", "Quinary"],
        [primary, secondary, accent, tertiary, quaternary, quinary],
    ):
        print(f"  {name}: {val}")


def main():
    parser = argparse.ArgumentParser(
        description="Update starship prompt palette from extracted colors."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Six hex colors. Reads from cache if omitted.",
    )
    args = parser.parse_args()
    run(args.colors)


if __name__ == "__main__":
    main()
