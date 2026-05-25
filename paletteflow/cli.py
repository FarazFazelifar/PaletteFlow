#!/usr/bin/env python3
"""PaletteFlow CLI — orchestrate the full wallpaper-to-theme pipeline."""

import argparse

from paletteflow import extract, starship, fastfetch, ghostty, cava, gnome_shell, service


def make_parser():
    parser = argparse.ArgumentParser(
        prog="paletteflow",
        description="Extract colors from your wallpaper and apply them across your Linux desktop.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Extract color palette from wallpaper")
    p_extract.add_argument(
        "image", nargs="?", default=None,
        help="Path to image. If omitted, uses current GNOME wallpaper.",
    )
    p_extract.add_argument(
        "-n", "--num-colors", type=int, default=8,
        choices=range(4, 13), metavar="[4-12]",
        help="Number of colors to extract (default: 8)",
    )

    p_starship = sub.add_parser("starship", help="Update starship prompt palette")
    p_starship.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )

    p_fastfetch = sub.add_parser("fastfetch", help="Update fastfetch ANSI colors")
    p_fastfetch.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors (primary secondary accent). Reads from cache if omitted.",
    )

    p_ghostty = sub.add_parser("ghostty", help="Update Ghostty terminal colors")
    p_ghostty.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )

    p_cava = sub.add_parser("cava", help="Update Cava audio visualizer gradient")
    p_cava.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )

    p_gnome = sub.add_parser("gnome-shell", help="Update GNOME Shell accent color")
    p_gnome.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )
    p_gnome.add_argument(
        "--mode", choices=["dark", "light"], default="dark",
        help="Base theme variant (default: dark)",
    )

    p_apply = sub.add_parser("apply", help="Run full pipeline (extract + all targets)")
    p_apply.add_argument(
        "-n", "--num-colors", type=int, default=8,
        choices=range(4, 13), metavar="[4-12]",
        help="Number of colors to extract (default: 8)",
    )

    p_service = sub.add_parser("service", help="Manage the paletteflow-watch systemd service")
    p_service.add_argument(
        "action", choices=["install", "uninstall", "status", "start", "stop", "logs"],
        help="Service action to perform",
    )

    return parser


def cmd_extract(args):
    extract.run(args.image, num_colors=args.num_colors)


def cmd_starship(args):
    starship.run(args.colors)


def cmd_fastfetch(args):
    fastfetch.run(args.colors)


def cmd_ghostty(args):
    ghostty.run(args.colors)


def cmd_cava(args):
    cava.run(args.colors)


def cmd_gnome_shell(args):
    gnome_shell.run(args.colors, mode=args.mode)


def cmd_apply(args):
    print("=== PaletteFlow ===")
    print("\n1. Extracting colors from wallpaper...")
    extract.run(num_colors=args.num_colors)
    print("\n2. Updating starship...")
    starship.run()
    print("\n3. Updating fastfetch...")
    fastfetch.run()
    print("\n4. Updating Ghostty...")
    ghostty.run()
    print("\n5. Updating Cava...")
    cava.run()
    print("\n6. Updating GNOME Shell accent color...")
    gnome_shell.run(mode="dark")
    print("\nDone! Your desktop theme now matches your wallpaper.")


def cmd_service(args):
    actions = {
        "install": service.install,
        "uninstall": service.uninstall,
        "status": service.status,
        "start": service.start,
        "stop": service.stop,
        "logs": service.logs,
    }
    actions[args.action]()


def main():
    parser = make_parser()
    args = parser.parse_args()

    dispatch = {
        "extract": cmd_extract,
        "starship": cmd_starship,
        "fastfetch": cmd_fastfetch,
        "ghostty": cmd_ghostty,
        "cava": cmd_cava,
        "gnome-shell": cmd_gnome_shell,
        "apply": cmd_apply,
        "service": cmd_service,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
