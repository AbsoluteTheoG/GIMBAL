"""Build Gimbal.exe and the release zip (Gimbal-vX.Y.Z-windows-x64.zip).

Usage, from the repository root:
    py -m pip install pyinstaller -r requirements.txt
    py tools/build_release.py

The version comes from APP_VERSION in gimbal.pyw. Options:
    --work DIR   temporary build folder (default: build)
    --out DIR    where the zip is written (default: dist)
"""
import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.search(r'^APP_VERSION = "([^"]+)"', (ROOT / "gimbal.pyw").read_text(encoding="utf-8"), re.M).group(1)
RELEASE_NAME = f"Gimbal-v{VERSION}-windows-x64"
EXTRA_FILES = ["README.md", "README.fr.md", "LICENSE", "CHANGELOG.md"]

VERSION_INFO = """VSVersionInfo(
  ffi=FixedFileInfo(filevers={nums}, prodvers={nums}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'AbsoluteTheoG'),
      StringStruct('FileDescription', 'Gimbal - HOTAS to keyboard, mouse and gamepad mapper'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'Gimbal'),
      StringStruct('LegalCopyright', 'MIT License'),
      StringStruct('OriginalFilename', 'Gimbal.exe'),
      StringStruct('ProductName', 'Gimbal'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def make_icon(path):
    """Same joystick glyph as the in-app icon, drawn large then downscaled for crisp edges."""
    s = 16
    img = Image.new("RGBA", (64 * s, 64 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2 * s, 2 * s, 62 * s, 62 * s), 15 * s, fill="#0b6bcb")
    d.rounded_rectangle((14 * s, 46 * s, 50 * s, 55 * s), 4 * s, fill="white")
    d.rectangle((29 * s, 24 * s, 35 * s, 48 * s), fill="white")
    d.ellipse((21 * s, 9 * s, 43 * s, 31 * s), fill="white")
    img.resize((256, 256), Image.LANCZOS).save(path, sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", default=str(ROOT / "build"))
    parser.add_argument("--out", default=str(ROOT / "dist"))
    args = parser.parse_args()
    work, out = Path(args.work).resolve(), Path(args.out).resolve()

    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    icon = work / "gimbal.ico"
    make_icon(icon)
    nums = tuple(int(n) for n in (VERSION.split(".") + ["0"] * 4)[:4])
    version_file = work / "version_info.txt"
    version_file.write_text(VERSION_INFO.format(nums=nums, version=VERSION), encoding="utf-8")

    subprocess.run([
        sys.executable, "-m", "PyInstaller", str(ROOT / "gimbal.pyw"),
        "--name", "Gimbal", "--windowed", "--noconfirm", "--clean",
        "--icon", str(icon), "--version-file", str(version_file),
        "--collect-data", "sv_ttk",           # Sun Valley theme (.tcl + images)
        "--collect-binaries", "vgamepad",     # ViGEmClient.dll
        "--distpath", str(work / "dist"), "--workpath", str(work / "pyinstaller"), "--specpath", str(work),
    ], check=True)

    app = work / "dist" / "Gimbal"
    for name in EXTRA_FILES:
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, app / name)
    shutil.copytree(ROOT / "profiles" / "examples", app / "profiles" / "examples")

    out.mkdir(parents=True, exist_ok=True)
    zip_path = out / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(app.rglob("*")):
            if f.is_file():
                z.write(f, Path("Gimbal") / f.relative_to(app))  # extracts into a "Gimbal" folder
    print(f"\n{zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
