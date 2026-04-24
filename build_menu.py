#!/usr/bin/env python3
"""
Build menu.pdf from menu.html using headless Google Chrome.

Usage:
    python3 build_menu.py

Edit menu.html, then re-run this script. The PDF replaces website/menu.pdf
and is what's linked from the Carta section of the home page.

Requires only Google Chrome (already installed on macOS if you've ever
opened chrome://). No pip installs.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
HTML = HERE / "menu.html"
PDF  = HERE / "menu.pdf"

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

def find_chrome():
    for p in CHROME_PATHS:
        if os.path.isfile(p):
            return p
    sys.exit("ERROR: no Chrome/Brave/Chromium found in /Applications")

def main():
    if not HTML.exists():
        sys.exit(f"ERROR: {HTML} not found")

    chrome = find_chrome()
    print(f"Using: {chrome}")
    print(f"Input:  {HTML}")
    print(f"Output: {PDF}")

    # Chrome's --print-to-pdf honours @page rules in the HTML.
    # --virtual-time-budget lets Google Fonts load before the snapshot.
    # --no-pdf-header-footer strips the default date/URL band.
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--virtual-time-budget=8000",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF}",
        f"file://{HTML}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"Chrome exited {result.returncode}")

    size_kb = PDF.stat().st_size / 1024
    print(f"Wrote {PDF} ({size_kb:.0f} KB)")

if __name__ == "__main__":
    main()
