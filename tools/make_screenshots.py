"""Regenerate the README screenshots (docs/screenshots/*.png) from a demo profile.

Usage, from the repository root (Windows, dependencies installed):
    py tools/make_screenshots.py

A fake HOTAS state is fed to the real engine; key presses and the virtual gamepad are
stubbed out, so nothing is sent to your system. The window is captured on screen, so leave
it in front while the script runs (about 20 seconds).
"""
import ctypes
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import tkinter as tk
import traceback
from ctypes import wintypes
from pathlib import Path

from PIL import Image, ImageDraw, ImageGrab

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
TMP = Path(tempfile.mkdtemp(prefix="gimbal_shots_"))
(TMP / "profiles" / "images").mkdir(parents=True)

loader = importlib.machinery.SourceFileLoader("gimbal", str(ROOT / "gimbal.pyw"))
spec = importlib.util.spec_from_loader("gimbal", loader)
gm = importlib.util.module_from_spec(spec)
loader.exec_module(gm)


def draw_demo_hotas(path):
    """Two stylised sticks, drawn at 2x then downscaled (no third-party artwork in the screenshots)."""
    k, w, h = 2, 1600, 700
    img = Image.new("RGB", (w * k, h * k))
    d = ImageDraw.Draw(img)
    for y in range(h * k):
        t = y / (h * k)
        d.line((0, y, w * k, y), fill=tuple(int(a + (b - a) * t) for a, b in zip((242, 244, 247), (226, 229, 234))))

    def stick(cx, mirror):
        def x_(v):
            return (cx - v if mirror else cx + v) * k

        def box(x1, y1, x2, y2):
            a, b = sorted((x_(x1), x_(x2)))
            return (a, y1 * k, b, y2 * k)

        d.ellipse(box(-230, 628, 230, 672), fill="#cfd3da")
        d.rounded_rectangle(box(-210, 545, 210, 650), 34 * k, fill="#2b2f36")
        d.rounded_rectangle(box(-200, 550, 200, 572), 11 * k, fill="#3a3f48")
        for bx in (-150, -105, -60):
            d.ellipse(box(bx - 13, 592, bx + 13, 618), fill="#4b5563")
        d.rounded_rectangle(box(-30, 455, 30, 560), 10 * k, fill="#3f4550")
        d.rounded_rectangle(box(-62, 175, 62, 480), 52 * k, fill="#23272e")
        d.rounded_rectangle(box(-70, 70, 100, 215), 58 * k, fill="#2a2f37")
        d.rounded_rectangle(box(-60, 78, 90, 120), 30 * k, fill="#323844")
        d.rounded_rectangle(box(88, 200, 128, 280), 18 * k, fill="#b91c1c")
        d.ellipse(box(-50, 96, -4, 142), fill="#a1a7b0")
        d.ellipse(box(-38, 108, -16, 130), fill="#4b5563")
        d.ellipse(box(18, 98, 58, 138), fill="#dc2626")
        d.ellipse(box(-22, 168, 14, 204), fill="#6b7280")
        for gy in range(300, 450, 26):
            d.rounded_rectangle(box(-50, gy, 50, gy + 8), 4 * k, fill="#2c3139")

    stick(480, True)
    stick(1120, False)
    img.resize((w, h), Image.LANCZOS).save(path)


L, R = "VKBsim Gladiator EVO L", "VKBsim Gladiator EVO R"


def axis(dev, idx, target, name=None, invert=False, dz=0.05):
    b = {"src": {"dev": dev, "type": "axis", "idx": idx, "dir": 1, "centered": True},
         "out": {"type": "pad_axis", "target": target}, "invert": invert, "deadzone": dz}
    return dict(b, name=name) if name else b


def button(dev, idx):
    return {"dev": dev, "type": "button", "idx": idx}


def digital(src, kind, target, name=None, mode="hold", extra=None, combo=None):
    b = {"src": src, "out": {"type": kind, "target": target}, "mode": mode}
    for key, value in (("name", name), ("extra", extra), ("with", combo)):
        if value:
            b[key] = value
    return b


BINDINGS = [
    axis(L, 0, "LX", "Strafe"), axis(L, 1, "LY", "Throttle", dz=0.1), axis(R, 0, "RX", "Look"),
    axis(R, 1, "RY", "Look", invert=True),
    digital(button(R, 0), "pad_button", "RB", "Fire"),
    digital(button(R, 1), "pad_button", "RT", "Jump", extra=[{"type": "pad_button", "target": "LT"}]),
    digital(button(R, 2), "pad_button", "A", "Interact"),
    digital(button(L, 0), "pad_button", "LB", "Ability"),
    digital(button(L, 2), "pad_button", "Y", "Scan"),
    digital(button(L, 1), "key", "LSHIFT", "Sprint", mode="toggle"),
    digital({"dev": R, "type": "hat", "idx": 0, "dir": "up"}, "pad_button", "DPAD_UP", "Quick menu"),
    digital({"dev": L, "type": "hat", "idx": 0, "dir": "left"}, "key", "Q"),
    digital({"dev": L, "type": "hat", "idx": 0, "dir": "right"}, "key", "E"),
    digital(button(R, 3), "pad_button", "START", "Galaxy map", combo=[button(L, 3)]),
]
LABELS = [
    {"src": BINDINGS[5]["src"], "x": 0.89, "y": 0.15},
    {"src": BINDINGS[4]["src"], "x": 0.89, "y": 0.35},
    {"src": BINDINGS[6]["src"], "x": 0.89, "y": 0.53},
    {"src": BINDINGS[9]["src"], "x": 0.11, "y": 0.15},
    {"src": BINDINGS[7]["src"], "x": 0.11, "y": 0.35},
    {"src": BINDINGS[8]["src"], "x": 0.11, "y": 0.53},
    {"src": BINDINGS[11]["src"], "x": 0.5, "y": 0.12},
    {"src": BINDINGS[10]["src"], "x": 0.5, "y": 0.24},
    {"src": BINDINGS[1]["src"], "x": 0.5, "y": 0.46},
    {"src": BINDINGS[2]["src"], "x": 0.5, "y": 0.62},
]
FAKE_HOTAS = {  # Jump (R B2) pressed, sprint toggled on (L B2), hat up, sticks moved
    R: {"axes": [0.35, -0.5, -1.0, 0, 0, 0, 0, 0], "buttons": [False, True] + [False] * 126, "hats": [(0, 1)]},
    L: {"axes": [-0.15, 0.7, 1.0, 0, 0, 0, 0, 0], "buttons": [False, True] + [False] * 126, "hats": [(0, 0)]},
}


class _FakePad:
    def __getattr__(self, name):
        return lambda *a, **kw: None


def main():
    draw_demo_hotas(TMP / "profiles" / "images" / "demo_hotas.png")
    profile = TMP / "profiles" / "demo.json"
    profile.write_text(json.dumps({"bindings": BINDINGS,
                                   "layout": {"image": "images/demo_hotas.png", "labels": LABELS}}), encoding="utf-8")
    gm.Engine._read = lambda self, joys: {k: {kk: list(vv) for kk, vv in v.items()} for k, v in FAKE_HOTAS.items()}
    gm.send_key = lambda name, up: None
    gm.send_mouse_move = lambda dx, dy: None
    gm.vg.VX360Gamepad = _FakePad
    gm.PROFILES_DIR = TMP / "profiles"
    gm.SETTINGS_FILE = TMP / "settings.json"
    gm.SETTINGS_FILE.write_text(json.dumps({"profile": str(profile), "theme": "dark", "lang": "en", "tab": 0}))

    user32 = ctypes.windll.user32
    user32.GetParent.restype = wintypes.HWND
    user32.GetParent.argtypes = (wintypes.HWND,)
    OUT.mkdir(parents=True, exist_ok=True)

    def grab(win, name):
        win.update()
        hwnd = user32.GetParent(win.winfo_id())
        r = wintypes.RECT()
        ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r))
        ImageGrab.grab((r.left, r.top, r.right, r.bottom), all_screens=True).save(OUT / name)
        print("saved", name)

    root = tk.Tk()
    errors = []
    root.report_callback_exception = lambda *a: errors.append("".join(traceback.format_exception(*a)))
    root.attributes("-topmost", True)
    app = gm.App(root)
    root.geometry(f"{int(1320 * app.scale)}x{int(800 * app.scale)}+20+20")
    state = {}

    def layout_mode(on):
        app.view.edit_var.set(on)
        app.view._toggle_edit()

    def dialog(index):
        dlg = gm.BindingDialog(app, app.bindings[index])
        dlg._refresh()
        dlg.attributes("-topmost", True)
        dlg.geometry("+300+160")
        state["dialog"] = dlg

    steps = [
        lambda: grab(root, "main-dark.png"),
        lambda: app.tabs.select(1),
        lambda: grab(root, "view-dark.png"),
        lambda: layout_mode(True),
        lambda: grab(root, "layout-mode.png"),
        lambda: layout_mode(False),
        lambda: app._set_appearance(theme="light"),
        lambda: app.tabs.select(0),
        lambda: grab(root, "main-light.png"),
        lambda: dialog(1),
        lambda: grab(state["dialog"], "dialog-axis.png"),
        lambda: state["dialog"].destroy(),
        lambda: dialog(5),
        lambda: grab(state["dialog"], "dialog-combo.png"),
        lambda: state["dialog"].destroy(),
        lambda: app._set_appearance(theme="dark", lang="fr"),
        lambda: app.tabs.select(1),
        lambda: grab(root, "view-dark-fr.png"),
        lambda: app.tabs.select(0),
        lambda: grab(root, "main-dark-fr.png"),
        lambda: app._close(),
    ]

    def run(i=0):
        try:
            steps[i]()
        except Exception:
            errors.append(traceback.format_exc())
        if i + 1 < len(steps):
            root.after(900, run, i + 1)

    root.after(1800, run)
    root.mainloop()
    if errors:
        print("\n".join(errors))
        sys.exit(1)


if __name__ == "__main__":
    main()
