#!/usr/bin/env python3
"""GNOME wallpaper change watcher — auto-triggers PaletteFlow on wallpaper change."""

import sys
import time
import subprocess
import argparse

from paletteflow import extract, starship, fastfetch, ghostty, cava


def get_current_wallpaper():
    for key in ["picture-uri-dark", "picture-uri"]:
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.background", key],
                capture_output=True, text=True, check=True,
            )
            output = result.stdout.strip().strip("'")
            if output and output.startswith("file://"):
                return output
        except subprocess.CalledProcessError:
            continue
    return None


def run_pipeline():
    print("\n=== Wallpaper changed! Running PaletteFlow ===")
    try:
        extract.main()
        starship.main()
        fastfetch.main()
        ghostty.main()
        cava.main()
        print("Done!\n")
    except SystemExit:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


def watch():
    print("PaletteFlow watcher: monitoring GNOME wallpaper changes...")
    print("Press Ctrl+C to stop.\n")
    last = get_current_wallpaper()
    while True:
        time.sleep(5)
        current = get_current_wallpaper()
        if current and current != last:
            last = current
            run_pipeline()


def main():
    parser = argparse.ArgumentParser(
        description="Watch for GNOME wallpaper changes and auto-apply PaletteFlow."
    )
    parser.parse_args()

    try:
        watch()
    except KeyboardInterrupt:
        print("\nWatcher stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
