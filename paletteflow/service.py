#!/usr/bin/env python3
"""Manage the paletteflow-watch systemd user service."""

import os
import shutil
import subprocess
import sys

SERVICE_NAME = "paletteflow-watch"


def _resolve_paletteflow():
    """Return absolute path to the paletteflow command."""
    cmd = shutil.which("paletteflow")
    if cmd:
        return cmd
    return f"{sys.executable} -m paletteflow"


def _generate_service_file():
    script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "watcher.sh"
    )
    paletteflow = _resolve_paletteflow()
    return f"""[Unit]
Description=PaletteFlow — auto-apply wallpaper colors to your desktop

[Service]
Type=simple
ExecStart=/bin/bash {script} {paletteflow} apply
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""


def _service_path():
    return os.path.expanduser(f"~/.config/systemd/user/{SERVICE_NAME}.service")


def _run(*args, **kwargs):
    subprocess.run(["systemctl", "--user", *args], **kwargs)


def install():
    path = _service_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(_generate_service_file())

    _run("daemon-reload", check=True)
    _run("enable", "--now", SERVICE_NAME, check=True)
    print(f"Service '{SERVICE_NAME}' installed, enabled, and started.")
    print("It will now watch your wallpaper and auto-apply PaletteFlow.")


def uninstall():
    _run("disable", "--now", SERVICE_NAME, capture_output=True)
    path = _service_path()
    if os.path.exists(path):
        os.remove(path)
    _run("daemon-reload", check=True)
    print(f"Service '{SERVICE_NAME}' uninstalled.")


def status():
    result = _run("status", SERVICE_NAME)
    sys.exit(result.returncode)


def start():
    _run("start", SERVICE_NAME, check=True)
    print(f"Service '{SERVICE_NAME}' started.")


def stop():
    _run("stop", SERVICE_NAME, check=True)
    print(f"Service '{SERVICE_NAME}' stopped.")


def logs():
    subprocess.run(
        ["journalctl", "--user", "--unit", SERVICE_NAME, "--follow",
         "--output", "short"],
    )
