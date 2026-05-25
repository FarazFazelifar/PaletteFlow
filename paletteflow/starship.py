import os
import sys
import json
import tempfile
import itertools

import tomlkit

from paletteflow.color_utils import (
    contrast_ratio,
    ensure_contrast_multi,
    ROLES,
)


STARSHIP_CONFIG = os.path.expanduser("~/.config/starship.toml")
PALETTE_FILE = os.path.expanduser("~/.cache/paletteflow.txt")
PALETTE_JSON = os.path.expanduser("~/.cache/paletteflow.json")
PALETTE_NAME = "auto_theme"


def _write_atomic(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".",
                                prefix=".tmp-", suffix=".toml")
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


def _resolve_palette(cli_colors):
    if cli_colors and len(cli_colors) >= 5:
        return cli_colors[:6]
    if os.path.exists(PALETTE_JSON):
        with open(PALETTE_JSON) as f:
            data = json.load(f)
        keys = ROLES
        colors = [data.get(k) for k in keys if data.get(k)]
        if len(colors) >= 5:
            return colors
    if os.path.exists(PALETTE_FILE):
        with open(PALETTE_FILE) as f:
            colors = [line.strip() for line in f if line.strip().startswith("#")]
            if len(colors) >= 5:
                return colors[:6]
            print(f"Error: Not enough colors in {PALETTE_FILE}.", file=sys.stderr)
            sys.exit(1)
    print("Error: No colors found. Run 'paletteflow extract' first.", file=sys.stderr)
    sys.exit(1)


def run(colors=None):
    palette = _resolve_palette(colors)

    bg = palette[0]
    surface = palette[1]
    primary = palette[2]
    secondary = palette[3]
    accent = palette[4]
    fg = palette[5]

    if not os.path.exists(STARSHIP_CONFIG):
        print(f"Error: Starship config not found at {STARSHIP_CONFIG}", file=sys.stderr)
        sys.exit(1)

    with open(STARSHIP_CONFIG) as f:
        doc = tomlkit.parse(f.read())

    if "palettes" not in doc:
        doc["palettes"] = tomlkit.table()
    if PALETTE_NAME not in doc["palettes"]:
        doc["palettes"][PALETTE_NAME] = tomlkit.table()

    # ----- contrast-optimised mapping ----------------------------------------
    # The user's format uses these fg:bg pairs:
    PAIRS = [
        ("primary", "secondary"),
        ("primary", "tertiary"),
        ("primary", "quaternary"),
        ("secondary", "tertiary"),
        ("tertiary", "quaternary"),
    ]

    fixed = {"secondary": accent}          # user preference
    pool = [bg, surface, primary, secondary]  # remaining 4 → pick 3

    def _eval(s_p, s_t, s_q):
        """Score one assignment: (primary, tertiary, quaternary)."""
        vals = {**fixed, "primary": s_p, "tertiary": s_t, "quaternary": s_q}
        crs = [contrast_ratio(vals[a], vals[b]) for a, b in PAIRS]
        return min(crs), sum(crs)

    best_assign = max(
        ((p, t, q) for p, t, q in itertools.permutations(pool, 3)),
        key=lambda x: _eval(*x),
    )
    best_map = {
        **fixed,
        "primary": best_assign[0],
        "tertiary": best_assign[1],
        "quaternary": best_assign[2],
    }

    # Iterate until the palette stabilises (up to 10 passes). Each pass re-adjusts
    # every entry; if nothing changes we have converged.
    HARDCODED_ON_PRIMARY = ["#000000", "#090c0c"]  # directory & spacer
    for _ in range(10):
        prev = dict(best_map)
        for entry in ("tertiary", "secondary", "primary"):
            partners = [best_map[b] for a, b in PAIRS if a == entry]
            if entry == "primary":
                partners.extend(HARDCODED_ON_PRIMARY)
            if partners:
                best_map[entry] = ensure_contrast_multi(best_map[entry], partners, 3.0)
        q_partners = [best_map[a] for a, b in PAIRS if b == "quaternary"]
        if q_partners:
            best_map["quaternary"] = ensure_contrast_multi(best_map["quaternary"], q_partners, 3.0)
        if best_map == prev:
            break

    names = ["primary", "secondary", "accent", "tertiary", "quaternary", "quinary",
             "senary", "septenary"]
    values = [
        best_map["primary"],
        best_map["secondary"],
        best_map["secondary"],   # accent entry = secondary (unused in format)
        best_map["tertiary"],
        best_map["quaternary"],
        bg,
        bg,
        surface,
    ]
    for name, val in zip(names, values):
        doc["palettes"][PALETTE_NAME][name] = val

    _write_atomic(STARSHIP_CONFIG, tomlkit.dumps(doc))

    print(f"Updated starship palette '{PALETTE_NAME}'")
    for name, val in zip(names, values):
        print(f"  {name}: {val}")


def main():
    import argparse
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
