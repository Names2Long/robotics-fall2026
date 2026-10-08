"""Capture the course virtual desktop after a short delay."""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from PIL import ImageGrab


def main():
    parser = argparse.ArgumentParser(description="Capture RViz in the course desktop")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--delay", type=float, default=4.0)
    args = parser.parse_args()
    if not 0 <= args.delay <= 20:
        parser.error("delay must be from 0 to 20 seconds")
    print(f"Switch to RViz now. Capturing in {args.delay:g} seconds.", flush=True)
    time.sleep(args.delay)
    image = ImageGrab.grab()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
