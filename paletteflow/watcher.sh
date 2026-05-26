#!/bin/bash
# Minimal GNOME wallpaper watcher — triggers $@ on change.
# No polling, no Python overhead — just gsettings monitor.

get_wallpaper() {
    local val
    val=$(gsettings get org.gnome.desktop.background picture-uri-dark 2>/dev/null)
    if [[ -z "$val" || "$val" == "''" ]]; then
        val=$(gsettings get org.gnome.desktop.background picture-uri 2>/dev/null)
    fi
    printf '%s' "$val"
}

last=$(get_wallpaper)

# Apply immediately on startup (ensures theme is applied after reboot)
"$@"

while IFS= read -r line; do
    case "$line" in
        picture-uri*)
            current=$(get_wallpaper)
            if [[ "$current" != "$last" ]]; then
                last="$current"
                "$@"
            fi
            ;;
    esac
done < <(gsettings monitor org.gnome.desktop.background)
