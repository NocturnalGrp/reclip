"""Build ReClip.app (a thin launcher for desktop.py) and its icon.

Usage:  venv/bin/python mac/build_app.py [destination dir, default ~/Desktop]
"""
import os
import plistlib
import shutil
import subprocess
import sys
import sysconfig
import tempfile

import AppKit

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
ICNS = os.path.join(HERE, "ReClip.icns")


def hex_color(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, 1)


def render_png(size, path):
    rep = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, size, size, 8, 4, True, False, AppKit.NSDeviceRGBColorSpace, 0, 0
    )
    AppKit.NSGraphicsContext.saveGraphicsState()
    AppKit.NSGraphicsContext.setCurrentContext_(
        AppKit.NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    )
    s = size / 1024

    # macOS icon grid: 824pt rounded square centred on a 1024 canvas.
    tile = AppKit.NSMakeRect(100 * s, 100 * s, 824 * s, 824 * s)
    hex_color("#f5f0e8").setFill()
    AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(tile, 185 * s, 185 * s).fill()

    # Orange disc + white play triangle, from static/favicon.svg.
    r = 300 * s
    hex_color("#e85d2a").setFill()
    AppKit.NSBezierPath.bezierPathWithOvalInRect_(
        AppKit.NSMakeRect(512 * s - r, 512 * s - r, 2 * r, 2 * r)
    ).fill()
    tri = AppKit.NSBezierPath.bezierPath()
    tri.moveToPoint_((450 * s, 427 * s))
    tri.lineToPoint_((450 * s, 597 * s))
    tri.lineToPoint_((603 * s, 512 * s))
    tri.closePath()
    AppKit.NSColor.whiteColor().setFill()
    tri.fill()

    AppKit.NSGraphicsContext.restoreGraphicsState()
    rep.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG, None).writeToFile_atomically_(path, True)


def build_icns():
    with tempfile.TemporaryDirectory() as tmp:
        iconset = os.path.join(tmp, "ReClip.iconset")
        os.mkdir(iconset)
        for pt in (16, 32, 128, 256, 512):
            render_png(pt, os.path.join(iconset, f"icon_{pt}x{pt}.png"))
            render_png(pt * 2, os.path.join(iconset, f"icon_{pt}x{pt}@2x.png"))
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", ICNS], check=True)


def compile_launcher(exe):
    config = os.path.join(sys.base_prefix, "bin", f"python{sys.version_info.major}.{sys.version_info.minor}-config")
    flags = subprocess.run(
        [config, "--embed", "--cflags", "--ldflags"], check=True, capture_output=True, text=True
    ).stdout.split()
    site_packages = sysconfig.get_paths()["purelib"]
    subprocess.run([
        "clang", os.path.join(HERE, "launcher.c"), "-o", exe,
        f'-DPROJECT_DIR="{PROJECT}"', f'-DSITE_PACKAGES="{site_packages}"',
        *flags,
    ], check=True)


def build_app(dest):
    app = os.path.join(dest, "ReClip.app")
    if os.path.exists(app):
        shutil.rmtree(app)
    macos = os.path.join(app, "Contents", "MacOS")
    res = os.path.join(app, "Contents", "Resources")
    os.makedirs(macos)
    os.makedirs(res)

    compile_launcher(os.path.join(macos, "ReClip"))
    shutil.copy(ICNS, os.path.join(res, "ReClip.icns"))

    with open(os.path.join(app, "Contents", "Info.plist"), "wb") as f:
        plistlib.dump({
            "CFBundleName": "ReClip",
            "CFBundleDisplayName": "ReClip",
            "CFBundleIdentifier": "com.nocturnal.reclip",
            "CFBundleExecutable": "ReClip",
            "CFBundleIconFile": "ReClip",
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": "1.0",
            "CFBundleVersion": "1",
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
        }, f)

    subprocess.run(["codesign", "--force", "--sign", "-", app], check=True)
    subprocess.run(["touch", app])
    return app


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Desktop")
    build_icns()
    print(build_app(dest))
