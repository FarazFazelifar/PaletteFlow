#!/usr/bin/env python3
"""Thin wrapper — execs watcher.sh to avoid keeping Python in memory."""

import os
import sys


def main():
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watcher.sh")
    if not os.path.exists(script):
        print(f"Error: {script} not found", file=sys.stderr)
        sys.exit(1)
    os.execvp("bash", ["bash", script])


if __name__ == "__main__":
    main()
