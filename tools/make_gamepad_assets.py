"""Regenerate assets/gamepad/*.png from the Xbox One template of e7d/gamepad-viewer (MIT License).

Usage, from the repository root:
    py -m pip install pymupdf pillow
    py tools/make_gamepad_assets.py

The SVGs are downloaded from a pinned upstream commit, rendered at 2x, then cut into the
same sprites the upstream CSS uses (background-position offsets, in CSS pixels).
"""
import urllib.request
from io import BytesIO
from pathlib import Path

import pymupdf as fitz
from PIL import Image

REV = "563552931253a2e558cf6fd5fc7fd254eefd9b2f"
URL = "https://raw.githubusercontent.com/e7d/gamepad-viewer/{rev}/templates/xbox-one/{name}.svg"
LICENSE_URL = f"https://raw.githubusercontent.com/e7d/gamepad-viewer/{REV}/LICENSE"
OUT = Path(__file__).resolve().parent.parent / "assets" / "gamepad"
SCALE = 2

# sprite: (svg, (x, y, width, height) in the SVG, None = whole image)
SPRITES = {
    "base_white": ("base-white", None),
    "base_black": ("base-black", None),
    "trigger": ("trigger", None),
    "bumper": ("bumper", None),
    "stick": ("stick", (85, 0, 83, 83)),
    "stick_pressed": ("stick", (0, 0, 83, 83)),
    "dpad_up": ("dpad", (35.66, 0, 34, 56)),
    "dpad_down": ("dpad", (0, 0, 34, 56)),
    "dpad_left": ("dpad", (0, 93, 56, 34)),
    "dpad_right": ("dpad", (0, 57, 56, 34)),
    "back": ("start-select", (0, 0, 33, 33)),
    "start": ("start-select", (34.4, 0, 33, 33)),
}
for i, face in enumerate("abxy"):
    SPRITES[f"button_{face}"] = ("buttons", (53 * i, 0, 53, 53))
    SPRITES[f"button_{face}_pressed"] = ("buttons", (53 * i, 53, 53, 53))


def render(name, cache={}):
    if name not in cache:
        svg = urllib.request.urlopen(URL.format(rev=REV, name=name)).read()
        page = fitz.open(stream=svg, filetype="svg")[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=True)
        cache[name] = Image.open(BytesIO(pix.tobytes("png"))).convert("RGBA")
    return cache[name]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for sprite, (svg, rect) in SPRITES.items():
        img = render(svg)
        if rect:
            x, y, w, h = (round(v * SCALE) for v in rect)
            img = img.crop((x, y, x + w, y + h))
        img.save(OUT / f"{sprite}.png", optimize=True)
        print(f"{sprite}.png {img.size}")
    license_text = urllib.request.urlopen(LICENSE_URL).read().decode("utf-8")
    (OUT / "LICENSE").write_text(
        "The images in this folder are derived from the Xbox One template of Gamepad Viewer\n"
        f"(https://github.com/e7d/gamepad-viewer, commit {REV}),\n"
        "rendered to PNG by tools/make_gamepad_assets.py. Original license:\n\n" + license_text,
        encoding="utf-8")


if __name__ == "__main__":
    main()
