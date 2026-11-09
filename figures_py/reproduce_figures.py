#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce Figures 1-8 of the TCM-SD42 manuscript from the checked-in data.

Run from this directory:  python reproduce_figures.py
Outputs:  Figure1.svg ... Figure8.svg, optional 600-dpi PNGs, then the provenance check.

Only aggregate, non-patient-level inputs are used (source_data/).  SVG generation
needs Python 3 + Pillow-free code paths; PNG rendering additionally needs
Microsoft Edge or Google Chrome (headless screenshot).
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def browser():
    for name in ("msedge", "chrome", "chromium", "google-chrome"):
        p = shutil.which(name)
        if p:
            return p
    for p in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/chromium",
    ):
        if os.path.exists(p):
            return p
    return None


def svg_size(path):
    head = open(path, encoding="utf-8").read(400)
    m = re.search(r'<svg[^>]*width="(\d+)"[^>]*height="(\d+)"', head)
    return int(m.group(1)), int(m.group(2))


def render_pngs(exe):
    from PIL import Image
    for n in range(1, 9):
        svg = os.path.join(HERE, f"Figure{n}.svg")
        html = os.path.join(HERE, f"Figure{n}.html")
        if not os.path.exists(svg) or not os.path.exists(html):
            print(f"  Figure{n}: svg/html missing, skipped")
            continue
        w, h = svg_size(svg)
        shot = os.path.join(HERE, f"_Figure{n}.png")
        subprocess.run([exe, "--headless=new", "--disable-gpu",
                        "--force-device-scale-factor=2",
                        f"--window-size={w},{h}", f"--screenshot={shot}",
                        "file:///" + html.replace("\\", "/")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        im = Image.open(shot).convert("RGB")
        im.save(os.path.join(HERE, f"Figure{n}.png"), dpi=(600, 600))
        os.remove(shot)
        print(f"  Figure{n}.png  {im.size[0]}x{im.size[1]}")


def main():
    for script in ("ga_v2.py", "build_all.py", "fig4_v3.py"):
        print("run", script)
        subprocess.run([sys.executable, os.path.join(HERE, script)], check=True,
                       cwd=HERE)

    exe = browser()
    if exe:
        print("render PNG with", exe)
        render_pngs(exe)
    else:
        print("no Edge/Chrome found: SVG and HTML are complete, PNG skipped")

    print("verify provenance")
    out = subprocess.run([sys.executable, os.path.join(HERE, "verify_provenance.py")],
                         cwd=HERE, capture_output=True, text=True)
    print(out.stdout.strip())
    if "FAIL" in out.stdout:
        raise SystemExit("provenance check failed")


if __name__ == "__main__":
    main()
