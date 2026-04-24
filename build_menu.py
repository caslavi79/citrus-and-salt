#!/usr/bin/env python3
"""
Build menu.pdf from menu.html.

Pipeline:
    HTML → Chrome headless screenshot (3x DPI) → JPEG → single-page PDF

Why the screenshot step?  Chrome's --print-to-pdf keeps CSS box-shadow
and text-shadow as live vector effects, which iOS Safari's PDF viewer
renders as solid rectangles instead of soft halos.  Flattening to a
raster image first means every PDF viewer renders the menu identically.

Usage:
    python3 build_menu.py

Requires Google Chrome in /Applications (also tries Brave/Chromium).
No pip installs beyond Pillow + reportlab (standard on macOS setups
that have ever used these).  If they're missing:
    pip3 install pillow reportlab
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
HTML = HERE / "menu.html"
PDF  = HERE / "menu.pdf"
PNG_TMP  = HERE / "_build_menu_tmp.png"
JPEG_TMP = HERE / "_build_menu_tmp.jpg"

# Render width in CSS px — matches the @page width in menu.html (430pt).
# At 1pt = 1px this keeps the PDF page size identical to the source.
WIDTH = 430

# Height must be at least as tall as content; excess is trimmed.
# Bump this if you add sections and the bottom gets cut off.
HEIGHT = 3600

# Higher = sharper text at the cost of file size. 3 is Vice's setting.
SCALE = 3

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
    sys.exit("ERROR: no Chrome/Brave/Chromium in /Applications")


def screenshot(chrome):
    """Use headless Chrome to capture HTML as a PNG."""
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--force-color-profile=srgb",
        f"--force-device-scale-factor={SCALE}",
        f"--window-size={WIDTH},{HEIGHT}",
        "--virtual-time-budget=8000",
        "--run-all-compositor-stages-before-draw",
        f"--screenshot={PNG_TMP}",
        f"file://{HTML}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"Chrome exited {result.returncode}")
    if not PNG_TMP.exists():
        sys.exit("ERROR: screenshot not produced")


def trim_and_pack():
    """Trim trailing whitespace, flatten to JPEG, wrap as single-page PDF."""
    from PIL import Image
    import numpy as np
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    img = Image.open(PNG_TMP).convert("RGB")
    w, h = img.size
    print(f"  Screenshot: {w}x{h}")

    # Trim all-background rows at the bottom so the PDF fits tight.
    # Threshold tuned so real text (including the dim "list rotates" note
    # in the footer) is detected, but soft pink/mustard text-shadow halos
    # from the wordmark glow below the footer are not.
    arr = np.array(img)
    brightness = arr.max(axis=2)
    content_rows = np.where(brightness.max(axis=1) > 90)[0]
    if len(content_rows):
        last = content_rows[-1]
        # add 36pt breathing room × SCALE
        trim_h = min(h, last + 36 * SCALE)
        if trim_h < h:
            img = img.crop((0, 0, w, trim_h))
            print(f"  Trimmed to {w}x{trim_h}")

    # Flatten to JPEG — smaller and removes alpha channel issues
    img.save(JPEG_TMP, "JPEG", quality=92, optimize=True)

    # Wrap in PDF.  PDF page is in points; we scaled HTML 3x so divide back.
    pdf_w = img.size[0] / SCALE
    pdf_h = img.size[1] / SCALE
    c = canvas.Canvas(str(PDF), pagesize=(pdf_w, pdf_h))
    c.setTitle("Citrus & Salt — Tequila & Mezcal List")
    c.setAuthor("Citrus & Salt")
    c.drawImage(ImageReader(str(JPEG_TMP)), 0, 0, width=pdf_w, height=pdf_h)
    c.save()


def main():
    if not HTML.exists():
        sys.exit(f"ERROR: {HTML} not found")

    chrome = find_chrome()
    print(f"Using:  {chrome}")
    print(f"Input:  {HTML}")
    print(f"Output: {PDF}")

    try:
        screenshot(chrome)
        trim_and_pack()
    finally:
        for f in (PNG_TMP, JPEG_TMP):
            if f.exists():
                f.unlink()

    size_kb = PDF.stat().st_size / 1024
    print(f"Wrote {PDF} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
