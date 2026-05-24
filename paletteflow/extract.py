import sys
import os
import argparse
import subprocess
import urllib.parse
from colorthief import ColorThief


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2]).upper()


def get_gnome_wallpaper():
    for key in ["picture-uri-dark", "picture-uri"]:
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.background", key],
                capture_output=True, text=True, check=True,
            )
            output = result.stdout.strip().strip("'")
            if output and output.startswith("file://"):
                return urllib.parse.unquote(output[7:])
        except subprocess.CalledProcessError:
            continue
        except Exception as e:
            print(f"Error retrieving GNOME background: {e}", file=sys.stderr)
            return None
    return None


def run(image=None):
    if not image:
        print("No image path provided. Detecting current GNOME background...")
        image = get_gnome_wallpaper()
        if not image:
            print("Failed to detect background.", file=sys.stderr)
            sys.exit(1)

    color_thief = ColorThief(image)
    primary_rgb = color_thief.get_color(quality=1)
    palette = color_thief.get_palette(color_count=8, quality=1)

    colors_rgb = [
        primary_rgb,
        palette[1] if len(palette) > 1 else primary_rgb,
        palette[2] if len(palette) > 2 else primary_rgb,
        palette[3] if len(palette) > 3 else primary_rgb,
        palette[4] if len(palette) > 4 else primary_rgb,
        palette[5] if len(palette) > 5 else primary_rgb,
    ]

    color_names = ["Primary", "Secondary", "Accent", "Tertiary", "Quaternary", "Quinary"]
    print(f"--- Color Palette for {image} ---")

    hex_colors = []
    for i, rgb in enumerate(colors_rgb):
        hex_val = rgb_to_hex(rgb)
        hex_colors.append(hex_val)
        print(f"\n{i+1}. {color_names[i]} Color:  {hex_val}")

    palette_file = os.path.expanduser("~/.cache/paletteflow.txt")
    os.makedirs(os.path.dirname(palette_file), exist_ok=True)
    with open(palette_file, "w") as f:
        for h in hex_colors:
            f.write(f"{h}\n")
    print(f"\nPalette saved to {palette_file}")
    return hex_colors


def main():
    parser = argparse.ArgumentParser(
        description="Extract a 6-color palette from an image (or current GNOME wallpaper)."
    )
    parser.add_argument(
        "image", nargs="?", default=None,
        help="Path to image. If omitted, uses current GNOME wallpaper.",
    )
    args = parser.parse_args()
    run(args.image)


if __name__ == "__main__":
    main()
