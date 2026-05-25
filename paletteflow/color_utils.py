import colorsys
import math


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{max(0, min(255, int(r))):02X}{max(0, min(255, int(g))):02X}{max(0, min(255, int(b))):02X}"


def rgb_to_hsl(r, g, b):
    nr, ng, nb = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(nr, ng, nb)
    return h * 360, s, l


def hsl_to_rgb(h, s, l):
    h = h / 360
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def get_brightness(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return (r * 299 + g * 587 + b * 114) / 1000


def get_saturation(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) / mx if mx else 0


def relative_luminance(hex_color):
    r, g, b = [c / 255 for c in hex_to_rgb(hex_color)]
    def linearize(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(c1, c2):
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def ensure_brightness(hex_color, target):
    r, g, b = hex_to_rgb(hex_color)
    nr, ng, nb = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(nr, ng, nb)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        nr2, ng2, nb2 = colorsys.hls_to_rgb(h, mid, s)
        br = (nr2 * 299 + ng2 * 587 + nb2 * 114) / 1000 * 255
        if abs(br - target) < 0.5:
            return rgb_to_hex(nr2 * 255, ng2 * 255, nb2 * 255)
        if br < target:
            lo = mid
        else:
            hi = mid
    nr2, ng2, nb2 = colorsys.hls_to_rgb(h, (lo + hi) / 2, s)
    return rgb_to_hex(nr2 * 255, ng2 * 255, nb2 * 255)


def blend(hex1, hex2, t):
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    return rgb_to_hex(
        r1 + (r2 - r1) * t,
        g1 + (g2 - g1) * t,
        b1 + (b2 - b1) * t,
    )


def pick_contrasting(hex_color):
    return "#000000" if relative_luminance(hex_color) > 0.179 else "#ffffff"


def is_dark(hex_color):
    return get_brightness(hex_color) <= 128


def ensure_contrast(hex_color, bg_color, min_ratio=4.5):
    cr = contrast_ratio(hex_color, bg_color)
    if cr >= min_ratio:
        return hex_color

    bg_is_dark = is_dark(bg_color)
    r, g, b = hex_to_rgb(hex_color)
    nr, ng, nb = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(nr, ng, nb)

    if bg_is_dark:
        target = l
        for _ in range(30):
            target = min(1.0, target + 0.02)
            nr2, ng2, nb2 = colorsys.hls_to_rgb(h, target, s)
            test = rgb_to_hex(nr2 * 255, ng2 * 255, nb2 * 255)
            if contrast_ratio(test, bg_color) >= min_ratio:
                return test
        return "#FFFFFF"
    else:
        target = l
        for _ in range(30):
            target = max(0.0, target - 0.02)
            nr2, ng2, nb2 = colorsys.hls_to_rgb(h, target, s)
            test = rgb_to_hex(nr2 * 255, ng2 * 255, nb2 * 255)
            if contrast_ratio(test, bg_color) >= min_ratio:
                return test
        return "#000000"


def _adjust_lightness(hex_color, backgrounds, min_ratio, direction, l, h, s):
    """Helper: step lightness in ±direction until min_ratio is met.
    Returns (candidate, lightness_change) for the first that passes, or
    (None, None)."""
    step = 0.005 * direction  # fine step (≈1.3 sRGB) to catch narrow windows
    for i in range(1, 50):
        l_step = l + i * step
        if l_step < 0.0 or l_step > 1.0:
            break
        nr2, ng2, nb2 = colorsys.hls_to_rgb(h, l_step, s)
        cand = rgb_to_hex(int(nr2 * 255), int(ng2 * 255), int(nb2 * 255))
        min_cr = min(contrast_ratio(cand, bg) for bg in backgrounds)
        if min_cr >= min_ratio:
            return cand, abs(l_step - l)
    return None, None


def ensure_contrast_multi(hex_color, backgrounds, min_ratio=3.0):
    """Lighten/darken hex_color to achieve min_ratio against ALL backgrounds.
    Tries both directions and returns the result closest to the original.
    If impossible, returns the best-effort colour."""
    r, g, b = hex_to_rgb(hex_color)
    nr, ng, nb = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(nr, ng, nb)

    best = hex_color
    best_min = min(contrast_ratio(hex_color, bg) for bg in backgrounds)
    if best_min >= min_ratio:
        return hex_color

    cand_a, da = _adjust_lightness(hex_color, backgrounds, min_ratio, +1, l, h, s)
    cand_b, db = _adjust_lightness(hex_color, backgrounds, min_ratio, -1, l, h, s)

    # Pick the passing candidate with the smallest lightness change
    if cand_a is not None and cand_b is not None:
        return cand_a if da <= db else cand_b
    if cand_a is not None:
        return cand_a
    if cand_b is not None:
        return cand_b

    # Neither direction reached min_ratio — return best-effort
    for direction in (+1, -1):
        step = 0.02 * direction
        for i in range(1, 50):
            l_step = l + i * step
            if l_step < 0.0 or l_step > 1.0:
                break
            nr2, ng2, nb2 = colorsys.hls_to_rgb(h, l_step, s)
            cand = rgb_to_hex(int(nr2 * 255), int(ng2 * 255), int(nb2 * 255))
            min_cr = min(contrast_ratio(cand, bg) for bg in backgrounds)
            if min_cr > best_min:
                best_min = min_cr
                best = cand

    return best


def color_distance(hex1, hex2):
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    h1, s1, l1 = rgb_to_hsl(r1, g1, b1)
    h2, s2, l2 = rgb_to_hsl(r2, g2, b2)
    dh = min(abs(h1 - h2), 360 - abs(h1 - h2)) / 180
    ds = abs(s1 - s2)
    dl = abs(l1 - l2)
    return math.sqrt(dh * dh + ds * ds + dl * dl)


ROLES = [
    "bg", "surface", "primary", "secondary", "accent", "fg",
]
