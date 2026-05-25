<div align="center">

# PaletteFlow

Your wallpaper's colors, flowing across your entire desktop.

<br>

<table>
  <tr>
    <td><img src="screenshot-1.png" width="400" alt="Starship prompt with wallpaper-derived colors"></td>
    <td><img src="screenshot-3.png" width="400" alt="GNOME Shell and Ghostty with themed colors"></td>
  </tr>
</table>

</div>

Extract colors from your wallpaper and apply them across your tools — the prompt, the terminal, the shell, the system info, even the audio visualizer. Everything picks up from the same palette automatically.

---

### What it touches

- **GNOME Shell** — accent color, surface backgrounds, text
- **[Starship](https://starship.rs)** — prompt palette
- **[Ghostty](https://ghostty.org)** — terminal background, foreground, cursor, selection, ANSI 1–15
- **[Fastfetch](https://github.com/fastfetch-cli/fastfetch)** — display key color, logo palette
- **[Cava](https://github.com/karlstav/cava)** — audio visualizer gradient

---

## Getting started

### Install

```bash
git clone https://github.com/FarazFazelifar/paletteflow.git
cd paletteflow
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

For faster extraction (≈53 ms instead of ≈2 s), build the Rust extractor:

```bash
./build_extractor.sh
```

### What you need

| Dependency | Why |
|---|---|
| [User Themes](https://extensions.gnome.org/extension/19/user-themes/) GNOME extension | Required for GNOME Shell theming |
| Python 3.10+ | Runtime |
| [tomlkit](https://github.com/sdispater/tomlkit) | TOML edit without breaking comments |
| Rust toolchain | Optional — ~40× faster extraction |

---

## Usage

### One command

```bash
paletteflow apply
```

Pulls your current GNOME wallpaper, extracts 6 colors, and updates every target. Add `-n 10` for a richer palette.

### Step by step

```bash
paletteflow extract          # read wallpaper → cache palette
paletteflow starship         # patch starship prompt colors
paletteflow gnome-shell      # set accent + surface colors
paletteflow ghostty          # terminal colors + ANSI palette
paletteflow fastfetch        # system info colors
paletteflow cava             # audio visualizer gradient
```

Pass colors directly if you want to skip the cache:

```bash
paletteflow starship #1A1A2E #16213E #0F3460 #E94560 #533483 #F5F5F5
```

### Watch for changes

Install a systemd user service that re-applies whenever the wallpaper changes:

```bash
paletteflow service install
```

It listens for GNOME's D-Bus signal directly via `gsettings monitor` — zero polling, ≤1 MB RSS idle.

```bash
paletteflow service status   # is it running?
paletteflow service logs     # tail live output
paletteflow service uninstall
```

### GNOME Shell theme mode

```bash
paletteflow gnome-shell --mode light
```

Defaults to dark.

---

## How it works

1. **Extract** — The Rust binary (or Python `colorthief` fallback) runs K-Means in LAB space (K=10), snaps centroids to real pixels, filters near-duplicates, and returns 6–10 diverse colors sorted by dominance.

2. **Map** — Colors are assigned to six roles: `bg` (most dominant), `surface` (second-most), `primary` / `secondary` (highest saturation), `accent` (absolute highest saturation), and `fg` (pure black or white).

3. **Apply** — Each target reads the palette from `~/.cache/paletteflow.json`, applies contrast checks (≥3:1 WCAG), and writes its config atomically via `tempfile.mkstemp` + `os.rename`. No config is ever left half-written.

4. **Contrast guarantee** — Every text/background pair across every target meets at least 3:1. Hardcoded user values (like `#000000` in starship format strings) are included as contrast constraints. When a wallpaper's colors make 3:1 impossible, the algorithm finds the best trade-off.

---

## Uninstall

```bash
paletteflow service uninstall
rm -rf ~/.local/share/themes/paletteflow
rm -f ~/.cache/paletteflow.txt ~/.cache/paletteflow.json
dconf reset /org/gnome/shell/extensions/user-theme/name
pip uninstall paletteflow -y
```

---

MIT
