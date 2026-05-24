import sys
import os
import argparse
import subprocess
import urllib.parse


DEFAULT_NUM_COLORS = 6


def _find_extractor():
    bin_name = "paletteflow-extract"
    ext = ".exe" if sys.platform == "win32" else ""

    env = os.environ.get("PALETTEFLOW_EXTRACTOR")
    if env and os.path.isfile(env):
        return env

    dev = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "extractor", "target", "release", bin_name + ext,
    )
    if os.path.isfile(dev):
        return dev

    sibling = os.path.join(os.path.dirname(sys.executable), bin_name + ext)
    if os.path.isfile(sibling):
        return sibling

    for d in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(d, bin_name + ext)
        if os.path.isfile(candidate):
            return candidate

    return None


def _extract_rust(image, num_colors):
    exe = _find_extractor()
    if not exe:
        return None
    try:
        result = subprocess.run(
            [exe, image, str(num_colors)],
            capture_output=True, text=True, check=True, timeout=30,
        )
        colors = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if len(colors) >= num_colors:
            return colors[:num_colors]
    except (subprocess.CalledProcessError, FileNotFoundError, TimeoutError):
        pass
    return None


def _extract_python(image, num_colors):
    from colorthief import ColorThief

    thief = ColorThief(image)
    primary = list(thief.get_color(quality=1))
    palette = thief.get_palette(color_count=num_colors + 2, quality=1)

    colors_rgb = [primary]
    for i in range(1, num_colors):
        colors_rgb.append(list(palette[i]) if len(palette) > i else primary)

    return [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in colors_rgb]


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


def run(image=None, num_colors=None):
    if num_colors is None:
        num_colors = DEFAULT_NUM_COLORS

    if not image:
        print("No image path provided. Detecting current GNOME background...")
        image = get_gnome_wallpaper()
        if not image:
            print("Failed to detect background.", file=sys.stderr)
            sys.exit(1)

    hex_colors = _extract_rust(image, num_colors)
    if hex_colors is None:
        hex_colors = _extract_python(image, num_colors)

    print(f"--- Color Palette for {image} ---")
    for i, hex_val in enumerate(hex_colors):
        label = "Accent" if i == 2 else f"Color {i+1}"
        print(f"  {label}: {hex_val}")

    palette_file = os.path.expanduser("~/.cache/paletteflow.txt")
    os.makedirs(os.path.dirname(palette_file), exist_ok=True)
    with open(palette_file, "w") as f:
        for h in hex_colors:
            f.write(f"{h}\n")
    print(f"\nPalette saved to {palette_file}")
    return hex_colors


def main():
    parser = argparse.ArgumentParser(
        description="Extract a color palette from an image (or current GNOME wallpaper)."
    )
    parser.add_argument(
        "image", nargs="?", default=None,
        help="Path to image. If omitted, uses current GNOME wallpaper.",
    )
    parser.add_argument(
        "-n", "--num-colors", type=int, default=DEFAULT_NUM_COLORS,
        choices=range(4, 13), metavar="[4-12]",
        help="Number of colors to extract (default: 6)",
    )
    args = parser.parse_args()
    run(args.image, num_colors=args.num_colors)


if __name__ == "__main__":
    main()
