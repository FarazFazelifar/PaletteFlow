import os
import sys
import time
import re
import subprocess
import tempfile
import json

from paletteflow.color_utils import (
    get_brightness,
    contrast_ratio,
    ensure_contrast,
    ensure_contrast_multi,
    blend,
    is_dark,
    ROLES,
)


THEME_DIR = os.path.expanduser("~/.local/share/themes/paletteflow/gnome-shell")
CSS_PATH = os.path.join(THEME_DIR, "gnome-shell.css")
PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
PALETTE_JSON = os.path.expanduser("~/.cache/paletteflow.json")
YARU_DARK_BASE = "/usr/share/gnome-shell/theme/Yaru-dark/gnome-shell.css"
YARU_BASE = "/usr/share/gnome-shell/theme/Yaru/gnome-shell.css"


CSS_COLOR_RE = re.compile(
    r"([a-zA-Z-]+)\s*:\s*(#[0-9A-Fa-f]{6})",
)


def _resolve_palette(cli_colors):
    if cli_colors and len(cli_colors) >= 3:
        return _parse_cli_colors(cli_colors)
    if os.path.exists(PALETTE_JSON):
        with open(PALETTE_JSON) as f:
            data = json.load(f)
        if all(k in data for k in ("bg", "surface", "fg", "accent")):
            return data
    if os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE) as f:
            colors = [line.strip() for line in f if line.strip()]
        if len(colors) >= 6:
            return dict(zip(ROLES[:len(colors)], colors))
        if len(colors) >= 3:
            keys = ROLES[:len(colors)]
            return dict(zip(keys, colors))

    print("Error: Need at least 3 colors. Run 'paletteflow extract' first.", file=sys.stderr)
    sys.exit(1)


def _parse_cli_colors(colors):
    colors = [c if c.startswith("#") else f"#{c}" for c in colors]
    keys = ROLES[:len(colors)]
    return dict(zip(keys, colors))


def _base_css_path(mode):
    return YARU_DARK_BASE if mode == "dark" else YARU_BASE


def _classify_property(prop):
    prop = prop.strip().lower()
    if prop.startswith("background") or prop == "bg":
        return "bg"
    if prop == "color" and not prop.startswith("background"):
        return "fg"
    if "border" in prop:
        return "border"
    if "selection" in prop:
        return "selection"
    if prop in ("caret-color", "outline-color"):
        return "fg"
    return "other"


def _is_interactive_context(css, pos):
    ctx_start = max(0, pos - 120)
    ctx = css[ctx_start:pos]
    keywords = [":hover", ":active", ":checked", ":focus", ":insensitive",
                "selected", "highlighted", "activatable"]
    return any(kw in ctx for kw in keywords)


def _generate_css(palette, mode):
    src = _base_css_path(mode)
    if not os.path.exists(src):
        print(f"Error: Theme CSS not found at {src}", file=sys.stderr)
        sys.exit(1)

    with open(src) as f:
        css = f.read()

    # Normalize all hex colors to uppercase for consistent matching
    css = re.sub(r"#[0-9A-Fa-f]{6}", lambda m: m.group(0).upper(), css)

    bg = palette.get("bg", "#2E2E2E")
    surface = palette.get("surface", "#3C3C3C")
    fg = palette.get("fg", "#FFFFFF")
    accent = palette.get("accent", "#4A90D9")
    primary = palette.get("primary", accent)
    secondary = palette.get("secondary", blend(accent, surface, 0.5))

    fg_subtle = ensure_contrast_multi(accent, [bg, surface], 3.0)
    accent_2 = secondary

    bg_is_dark = is_dark(bg)
    applied_accent = ensure_contrast(accent, bg, 3.0) if bg_is_dark else accent

    # Step 1: Build replacement map based on property context
    replacements = {}
    already_replaced = set()

    for match in CSS_COLOR_RE.finditer(css):
        prop, color_val = match.group(1), match.group(2)
        color_upper = color_val.upper()
        if color_upper in already_replaced:
            continue

        prop_type = _classify_property(prop)
        br = get_brightness(color_val)
        pos = match.start()
        is_interactive = _is_interactive_context(css, pos)

        if is_interactive:
            if prop_type in ("bg", "border"):
                new_color = applied_accent
            elif prop_type == "fg":
                new_color = fg
            else:
                new_color = applied_accent
        elif prop_type == "bg":
            if br < 50:
                new_color = bg
            else:
                new_color = surface
        elif prop_type == "fg":
            new_color = fg
        elif prop_type == "border":
            if br < 80:
                new_color = surface
            else:
                new_color = fg_subtle
        elif prop_type == "selection":
            new_color = applied_accent
        else:
            if br < 50:
                new_color = bg
            elif br < 110:
                new_color = surface
            elif br >= 200:
                new_color = fg
            else:
                new_color = fg_subtle

        if color_upper not in replacements:
            replacements[color_upper] = new_color
            already_replaced.add(color_upper)

    # Step 2: Catch remaining colors not matched by property regex
    all_colors = set(re.findall(r"#[0-9A-Fa-f]{6}", css))
    for c in all_colors:
        cu = c.upper()
        if cu not in replacements:
            br = get_brightness(c)
            if br < 50:
                replacements[cu] = bg
            elif br < 110:
                replacements[cu] = surface
            elif br >= 200:
                replacements[cu] = fg
            else:
                replacements[cu] = fg_subtle

    # Step 3: Force all text-color properties to fg BEFORE general hex replacement
    css = re.sub(
        r"((?<![a-zA-Z-])color:\s*)#[0-9A-Fa-f]{6}",
        lambda m: f"{m.group(1)}{fg}",
        css,
    )

    # Step 4: Apply background/border replacements to remaining hex values
    def _replace_color(match):
        c = match.group(0).upper()
        return replacements.get(c, match.group(0))

    css = re.sub(r"#[0-9A-Fa-f]{6}", _replace_color, css)

    # Step 5: Apply accent-specific replacements
    css = css.replace("-st-accent-color", applied_accent)
    css = css.replace("-st-accent-fg-color", fg)

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
    palette = _resolve_palette(colors)
    accent = palette.get("accent", "#4A90D9")

    new_css = _generate_css(palette, mode)

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
    print(f"  Background: {palette.get('bg', '?')}, Surface: {palette.get('surface', '?')}")
    print(f"  Foreground: {palette.get('fg', '?')}, Accent: {accent}")


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
