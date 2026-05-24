# PaletteFlow

> Extract colors from your wallpaper and watch them flow across your entire Linux desktop.

PaletteFlow reads your current GNOME wallpaper (or any image), extracts a 6-color palette, and applies it to:

- **Starship** — prompt color palette
- **Fastfetch** — system info ANSI colors
- **Ghostty** — terminal background, foreground, cursor, and ANSI palette
- **Cava** — audio visualizer gradient

## Installation

```bash
git clone https://github.com/YOUR_USER/paletteflow.git
cd paletteflow

# Create a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .
```

## Usage

### One-shot: apply from current wallpaper

```bash
paletteflow apply
```

Or step by step:

```bash
paletteflow extract          # extract 6 colors from GNOME wallpaper
paletteflow starship         # update starship palette
paletteflow fastfetch        # update fastfetch colors
paletteflow ghostty          # update Ghostty terminal
paletteflow cava             # update Cava gradient
```

### Auto-watch wallpaper changes

```bash
paletteflow-watch
```

This runs in the foreground and automatically re-applies your theme whenever GNOME's wallpaper changes.

### Provide a custom image

```bash
paletteflow extract ~/Pictures/wallpaper.jpg
paletteflow starship #1A1A2E #16213E #0F3460 #E94560 #533483 #F5F5F5
```

## How it works

1. **`extract`** uses `ColorThief` to pull a dominant 6-color palette from your wallpaper and saves it to `~/.cache/paletteflow.txt`.
2. Each `update_*` module reads from that cache and patches the respective app's config file, preserving existing formatting.
3. Ghostty updates include automatic contrast-checking: text colors invert for light/dark backgrounds, and palette colors are shifted to ensure readability.
4. Fastfetch updates handle JSONC (strips comments before parsing), so your `config.jsonc` stays valid.

## Supported targets

| Target | Config file | What gets updated |
|--------|-------------|-------------------|
| Starship | `~/.config/starship.toml` | `[palettes.auto_theme]` (6 colors) |
| Fastfetch | `~/.config/fastfetch/config.jsonc` | Display color + logo ANSI colors |
| Ghostty | `~/.config/ghostty/config` | Background, foreground, cursor, selection, palette[1-6] |
| Cava | `~/.config/cava/config` | 6-color gradient under `[color]` |

## Requirements

- Linux with GNOME (or manually provide an image path)
- Python 3.10+
- [colorthief](https://github.com/fengsp/color-thief-py) — color extraction
- [tomlkit](https://github.com/sdispater/tomlkit) — TOML editing with comment preservation

## Roadmap

- [ ] Plasma/KDE wallpaper support
- [ ] Hyprland wallpaper detection (hyprctl)
- [ ] Waybar / Hyprland bar color themes
- [ ] Rofi theme colors
- [ ] Kitty / Alacritty terminal support
- [ ] systemd user service for wallpaper watching
- [ ] Preview mode (show colors before applying)

## License

MIT
