import os
import sys
import time
import re
import subprocess
import tempfile
from collections import Counter


THEME_DIR = os.path.expanduser("~/.local/share/themes/paletteflow/gnome-shell")
CSS_PATH = os.path.join(THEME_DIR, "gnome-shell.css")
PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
YARU_BASE = "/usr/share/gnome-shell/theme/Yaru/gnome-shell.css"
YARU_DARK_BASE = "/usr/share/gnome-shell/theme/Yaru-dark/gnome-shell.css"


def get_brightness(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (r * 299 + g * 587 + b * 114) / 1000


def _saturation(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) / mx if mx else 0


def get_contrasting_text_color(hex_color):
    return "#000000" if get_brightness(hex_color) > 128 else "#ffffff"


def _pick_accent(colors):
    scored = [(c, get_brightness(c), _saturation(c)) for c in colors]
    candidates = [(c, b, s) for (c, b, s) in scored if 40 <= b <= 200]
    if not candidates:
        candidates = sorted(scored, key=lambda x: x[1], reverse=True)[:3]
    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[0][0]


def _resolve_colors(cli_colors):
    if cli_colors and len(cli_colors) >= 3:
        colors = [c if c.startswith("#") else f"#{c}" for c in cli_colors]
        return colors

    if os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE) as f:
            colors = [line.strip() for line in f if line.strip()]
        if len(colors) >= 3:
            return colors

    print("Error: Need at least 3 colors. Run 'paletteflow extract' first.", file=sys.stderr)
    sys.exit(1)


def _base_css_path(mode):
    return YARU_DARK_BASE if mode == "dark" else YARU_BASE


def _build_bg_map(css, palette, accent_color):
    bg_colors = re.findall(r"(?<=background-color:)\s*#[0-9A-Fa-f]{6}", css)
    bg_colors = [c.strip() for c in bg_colors]
    if not bg_colors:
        return {}

    freq = Counter(bg_colors)
    ranked_bg = sorted(freq.keys(), key=lambda c: freq[c], reverse=True)

    bg_palette = [c for c in palette if c != accent_color]
    bg_palette.sort(key=get_brightness)

    top_bg = sorted(ranked_bg[:len(bg_palette)], key=get_brightness)

    return dict(zip(top_bg, bg_palette))


def _generate_css(palette, accent_color, fg_color, mode):
    src = _base_css_path(mode)
    if not os.path.exists(src):
        print(f"Error: Theme CSS not found at {src}", file=sys.stderr)
        sys.exit(1)

    with open(src) as f:
        css = f.read()

    for yaru_color, pal_color in _build_bg_map(css, palette, accent_color).items():
        css = css.replace(yaru_color, pal_color)

    css = css.replace("-st-accent-color", accent_color)
    css = css.replace("-st-accent-fg-color", fg_color)

    return css


def _write_atomic(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-", suffix=".css")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.rename(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _reload_theme():
    key = "/org/gnome/shell/extensions/user-theme/name"
    try:
        result = subprocess.run(
            ["dconf", "read", key],
            capture_output=True, text=True, timeout=5,
        )
        current = result.stdout.strip()
        if not current:
            return

        subprocess.run(
            ["dconf", "write", key, "''"],
            check=True, capture_output=True, timeout=5,
        )
        time.sleep(0.1)
        subprocess.run(
            ["dconf", "write", key, current],
            check=True, capture_output=True, timeout=5,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            "Warning: Could not reload GNOME Shell theme automatically.",
            file=sys.stderr,
        )


def run(colors=None, mode="dark"):
    extracted = _resolve_colors(colors)
    accent = _pick_accent(extracted)
    fg = get_contrasting_text_color(accent)

    new_css = _generate_css(extracted, accent, fg, mode)

    if os.path.exists(CSS_PATH):
        with open(CSS_PATH) as f:
            existing = f.read()
    else:
        existing = ""

    if new_css != existing:
        _write_atomic(CSS_PATH, new_css)
        _reload_theme()
    else:
        print("GNOME Shell theme already up to date.")

    mode_label = "dark" if mode == "dark" else "light"
    print(f"Updated GNOME Shell theme ({mode_label} mode)")
    print(f"  Accent: {accent}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Update GNOME Shell theme from extracted wallpaper palette."
    )
    parser.add_argument(
        "colors", nargs="*", default=None,
        help="Hex colors from palette. Reads from cache if omitted.",
    )
    parser.add_argument(
        "--mode", choices=["dark", "light"], default="dark",
        help="Base theme variant (default: dark)",
    )
    args = parser.parse_args()
    run(args.colors, mode=args.mode)


if __name__ == "__main__":
    main()
