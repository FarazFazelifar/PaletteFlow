import sys
import os
import argparse
import subprocess
import urllib.parse
import json

from paletteflow.color_utils import (
    get_saturation,
    contrast_ratio,
    is_dark,
    rgb_to_hsl,
    hsl_to_rgb,
    hex_to_rgb,
    rgb_to_hex,
    ROLES,
)


DEFAULT_NUM_COLORS = 8
RUST_MAX = 12


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


def _extract(image, num_colors):
    """Extract colours from image using the Rust extractor."""
    exe = _find_extractor()
    if not exe:
        print("Error: paletteflow-extract binary not found.", file=sys.stderr)
        sys.exit(1)

    # Rust supports 4–12; clamp to that range
    n = max(4, min(num_colors, RUST_MAX))

    try:
        result = subprocess.run(
            [exe, image, str(n)],
            capture_output=True, text=True, check=True, timeout=30,
        )
        colors = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not colors:
            print(f"Error: extractor returned no colours for {image}", file=sys.stderr)
            sys.exit(1)
        return colors
    except subprocess.CalledProcessError as e:
        print(f"Error: extractor failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: extractor binary not found at {exe}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError:
        print("Error: extractor timed out after 30 seconds", file=sys.stderr)
        sys.exit(1)


def _get_gnome_wallpaper():
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


def _build_palette(raw_colors):
    """Assign extracted colors to UI roles per Phase 2-4 of the extraction guide.

    raw_colors are dominance-sorted (highest first) from the Rust extractor.
    Returns [bg, surface, primary, secondary, accent, fg].
    """
    # Deduplicate while preserving dominance order
    seen = set()
    unique = []
    for c in raw_colors:
        cu = c.upper()
        if cu not in seen:
            seen.add(cu)
            unique.append(c)

    if not unique:
        palette = ["#161B22", "#24343C", "#3C444C", "#51565D", "#6C747C", "#A3A9AF"]
        return palette
    if len(unique) < 2:
        return [unique[0]] * 6

    # ---- Phase 3: Mapping ----

    # bg: highest dominance (first in list)
    bg = unique[0]

    # surface: second-highest dominance
    surface = unique[1]
    # Fallback: if too contrasty against bg, blend bg ±5%
    if contrast_ratio(surface, bg) > 8.0:
        r, g, b = hex_to_rgb(bg)
        h, s, lv = rgb_to_hsl(r, g, b)
        if is_dark(bg):
            lv = min(1.0, lv + 0.05)
        else:
            lv = max(0.0, lv - 0.05)
        nr, ng, nb = hsl_to_rgb(h, s, lv)
        surface = rgb_to_hex(nr, ng, nb)

    # Remaining for primary + secondary action colors
    remaining = [c for c in unique if c not in (bg, surface)]

    # Sort remaining by saturation descending
    remaining.sort(key=get_saturation, reverse=True)

    primary = remaining[0] if remaining else surface
    secondary = remaining[1] if len(remaining) > 1 else primary

    # accent: highest saturation across all unique colors
    used = {bg, surface, primary, secondary}
    accent_candidates = [c for c in unique if c not in used]
    if accent_candidates:
        accent_candidates.sort(key=get_saturation, reverse=True)
        accent = accent_candidates[0]
    else:
        accent = primary

    # ---- Phase 4: Text (Accessibility) ----
    # Use pure black or white for guaranteed readability against any background
    fg = "#FFFFFF" if is_dark(bg) else "#000000"

    palette = [bg, surface, primary, secondary, accent, fg]
    return palette


def run(image=None, num_colors=None):
    if num_colors is None:
        num_colors = DEFAULT_NUM_COLORS

    if not image:
        print("No image path provided. Detecting current GNOME background...")
        image = _get_gnome_wallpaper()
        if not image:
            print("Failed to detect background.", file=sys.stderr)
            sys.exit(1)

    hex_colors = _extract(image, num_colors)
    palette = _build_palette(hex_colors)

    print(f"--- Color Palette for {image} ---")
    for role, hex_val in zip(ROLES, palette):
        print(f"  {role}: {hex_val}")

    palette_file = os.path.expanduser("~/.cache/paletteflow.txt")
    os.makedirs(os.path.dirname(palette_file), exist_ok=True)
    with open(palette_file, "w") as f:
        for h in palette:
            f.write(f"{h}\n")
    print(f"\nPalette saved to {palette_file}")

    json_file = os.path.expanduser("~/.cache/paletteflow.json")
    with open(json_file, "w") as f:
        json.dump(dict(zip(ROLES, palette)), f, indent=2)
    print(f"Palette metadata saved to {json_file}")
    return palette


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
        help="Number of colors to extract (default: 8)",
    )
    args = parser.parse_args()
    run(args.image, num_colors=args.num_colors)


if __name__ == "__main__":
    main()
