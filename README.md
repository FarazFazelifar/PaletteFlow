# PaletteFlow

> Extract colors from your wallpaper and watch them flow across your entire Linux desktop.

PaletteFlow reads your current GNOME wallpaper (or any image), extracts a color palette, and applies it to:

- **GNOME Shell** — system accent color and surface backgrounds
- **Starship** — prompt color palette
- **Ghostty** — terminal background, foreground, cursor, and ANSI palette
- **Fastfetch** — system info ANSI colors
- **Cava** — audio visualizer gradient

## Installation

```bash
git clone https://github.com/FarazFazelifar/paletteflow.git
cd paletteflow

# Create a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install Python package
pip install -e .

# (Optional) Build the Rust color extractor for ~40x faster extraction
./build_extractor.sh
```

### Dependencies

- **User Themes** GNOME extension — required for GNOME Shell theming.  
  [Install from extensions.gnome.org](https://extensions.gnome.org/extension/19/user-themes/)  
  (Pre-installed on Ubuntu — enable it in Extensions or GNOME Settings.)

## Usage

### One-shot: apply from current wallpaper

```bash
paletteflow apply
```

Extract 6 colors by default. Use `-n` for more (up to 12):

```bash
paletteflow apply -n 10     # 10-color palette
```

### Step by step

```bash
paletteflow extract          # extract 6 colors (or: -n 12)
paletteflow starship         # update starship palette
paletteflow fastfetch        # update fastfetch colors
paletteflow ghostty          # update Ghostty terminal
paletteflow cava             # update Cava gradient
paletteflow gnome-shell      # update GNOME Shell accent + backgrounds
```

Pass colors directly (skips cache):

```bash
paletteflow starship #1A1A2E #16213E #0F3460 #E94560 #533483 #F5F5F5
```

### Theme mode

GNOME Shell defaults to dark mode. Switch with `--mode`:

```bash
paletteflow gnome-shell --mode light
```

### Auto-watch wallpaper changes

Install a background systemd service that re-applies whenever the wallpaper changes:

```bash
paletteflow service install
```

Manage the service:

```bash
paletteflow service status   # check if running
paletteflow service logs     # tail live logs
paletteflow service stop     # stop watching
paletteflow service start    # resume watching
paletteflow service uninstall
```

Run in the foreground for testing:

```bash
paletteflow-watch
```

The service uses zero-polling — it listens for GNOME's D-Bus signal directly via `gsettings monitor`. The watcher is a 26-line bash script with no Python overhead (~1 MB RSS idle).

## Uninstallation

### Remove the systemd service

```bash
paletteflow service uninstall
```

### Remove generated files

```bash
rm -rf ~/.local/share/themes/paletteflow      # GNOME Shell theme
rm -f ~/.cache/paletteflow.txt                # extracted palette cache
```

### Uninstall the package

```bash
pip uninstall paletteflow -y
```

Or if you used a virtual environment, just delete it:

```bash
rm -rf .venv
```

### Restore original GNOME Shell theme

Set the User Themes extension back to the default:

```bash
dconf write /org/gnome/shell/extensions/user-theme/name "''"
```

## How it works

1. **`extract`** uses the Rust `paletteflow-extract` binary (or Python `ColorThief` as fallback) to pull a configurable 4–12 color palette from your wallpaper. The Rust version downscales images to 300px and runs median-cut quantization in native code — ~53 ms vs ~2 s for high-res wallpapers. The palette is saved to `~/.cache/paletteflow.txt`.

2. **`gnome-shell`** copies Yaru's full theme CSS and replaces all 200+ `-st-accent-color` references with the best accent candidate from your palette (picked by saturation). The remaining palette colors replace Yaru's surface background colors, matched by brightness. Theme changes apply live via the User Themes extension.

3. **`starship`** reads from cache and patches `[palettes.auto_theme]` in your Starship config. The terminal background color is excluded to prevent prompt sections from visually merging with the terminal.

4. **`ghostty`** sets the terminal background to the dominant palette color, then applies contrast-checked ANSI colors. Text colors invert for light/dark backgrounds, and palette colors are shifted to ensure readability.

5. **`fastfetch`** updates its JSONC config for display and logo ANSI colors. Handles JSONC comments and literal control characters.

6. **`cava`** updates the 6-color gradient in `~/.config/cava/config`.

## Supported targets

| Target | Config file | What gets updated |
|--------|-------------|-------------------|
| GNOME Shell | `~/.local/share/themes/paletteflow/gnome-shell/gnome-shell.css` | Accent color + surface backgrounds |
| Starship | `~/.config/starship.toml` | `[palettes.auto_theme]` (6 colors) |
| Fastfetch | `~/.config/fastfetch/config.jsonc` | Display color + logo ANSI colors |
| Ghostty | `~/.config/ghostty/config` | Background, foreground, cursor, selection, palette[1-6] |
| Cava | `~/.config/cava/config` | 6-color gradient under `[color]` |

## Requirements

- Linux with GNOME (or manually provide an image path)
- Python 3.10+
- [colorthief](https://github.com/fengsp/color-thief-py) — Python color extraction (fallback)
- [tomlkit](https://github.com/sdispater/tomlkit) — TOML editing with comment preservation
- [User Themes](https://extensions.gnome.org/extension/19/user-themes/) GNOME extension — for shell theming
- Rust toolchain (optional, for ~40x faster extraction via `./build_extractor.sh`)

## Publishing plans

PaletteFlow is planned to be published as:

- **GNOME Shell extension** — a one-click install from [extensions.gnome.org](https://extensions.gnome.org) with a settings panel for color count, theme mode, and target toggles.
- **PyPI package** — `pip install paletteflow` for the CLI tools, no cloning needed.

Both would share the same backend — the extension would call the Python CLI under the hood.

## License

MIT
