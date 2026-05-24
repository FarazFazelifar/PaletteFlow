#!/usr/bin/env python3
"""PaletteFlow CLI — orchestrate the full wallpaper-to-theme pipeline."""

import sys
import argparse

from paletteflow import extract, starship, fastfetch, ghostty, cava


def make_parser():
    parser = argparse.ArgumentParser(
        prog="paletteflow",
        description="Extract colors from your wallpaper and apply them across your Linux desktop.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Extract 6-color palette from wallpaper")
    p_extract.add_argument(
        "image", nargs="?", default=None,
        help="Path to image. If omitted, uses current GNOME wallpaper.",
    )

    p_starship = sub.add_parser("starship", help="Update starship prompt palette")
    p_starship.add_argument(
        "colors", nargs="*", default=None,
        help="Six hex colors. Reads from cache if omitted.",
    )

    p_fastfetch = sub.add_parser("fastfetch", help="Update fastfetch ANSI colors")
    p_fastfetch.add_argument(
        "colors", nargs="*", default=None,
        help="Three hex colors (primary secondary accent). Reads from cache if omitted.",
    )

    p_ghostty = sub.add_parser("ghostty", help="Update Ghostty terminal colors")
    p_ghostty.add_argument(
        "colors", nargs="*", default=None,
        help="Six hex colors. Reads from cache if omitted.",
    )

    p_cava = sub.add_parser("cava", help="Update Cava audio visualizer gradient")
    p_cava.add_argument(
        "colors", nargs="*", default=None,
        help="Six hex colors. Reads from cache if omitted.",
    )

    sub.add_parser("apply", help="Run full pipeline (extract + all targets)")

    return parser


def cmd_extract(args):
    extract.run(args.image)


def cmd_starship(args):
    starship.run(args.colors)


def cmd_fastfetch(args):
    fastfetch.run(args.colors)


def cmd_ghostty(args):
    ghostty.run(args.colors)


def cmd_cava(args):
    cava.run(args.colors)


def cmd_apply(args):
    print("=== PaletteFlow ===")
    print("\n1. Extracting colors from wallpaper...")
    extract.run()
    print("\n2. Updating starship...")
    starship.run()
    print("\n3. Updating fastfetch...")
    fastfetch.run()
    print("\n4. Updating Ghostty...")
    ghostty.run()
    print("\n5. Updating Cava...")
    cava.run()
    print("\nDone! Your desktop theme now matches your wallpaper.")


def main():
    parser = make_parser()
    args = parser.parse_args()

    dispatch = {
        "extract": cmd_extract,
        "starship": cmd_starship,
        "fastfetch": cmd_fastfetch,
        "ghostty": cmd_ghostty,
        "cava": cmd_cava,
        "apply": cmd_apply,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
