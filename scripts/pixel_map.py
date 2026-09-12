#!/usr/bin/env python3
"""Print a character map of part of a picture, to find boundaries by measuring.

  # ink (dark)   o colour (skin, hair, shading)   . paper (white)   - grey

Use it before choosing a crop or a repair box: e.g. where the chin ends and the
clothing starts, or which rows a paper-white gap spans.

  python3 pixel_map.py in.png --x 100:320 --y 200:350 [--step 2] [--ystep 3]
"""
import argparse
import subprocess

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("src")
ap.add_argument("--x", default=None, help="x0:x1")
ap.add_argument("--y", default=None, help="y0:y1")
ap.add_argument("--step", type=int, default=2)
ap.add_argument("--ystep", type=int, default=3)
a = ap.parse_args()
run = lambda *c: subprocess.run(c, check=True, capture_output=True).stdout
w, h = map(int, run("magick", a.src, "-format", "%w %h", "info:").split())
rgb = run("magick", a.src, "-background", "white", "-alpha", "remove", "-alpha", "off", "-depth", "8", "rgb:-")
x0, x1 = map(int, a.x.split(":")) if a.x else (0, w)
y0, y1 = map(int, a.y.split(":")) if a.y else (0, h)


def cls(x, y):
    r, g, b = rgb[3 * (y * w + x):3 * (y * w + x) + 3]
    lo, sat = min(r, g, b), max(r, g, b) - min(r, g, b)
    return "#" if lo < 90 else "o" if sat >= 28 else "." if lo >= 190 else "-"


xs = range(x0, min(x1, w), a.step)
print(f"{w}x{h}; x={x0}..{x1} step {a.step}, a digit marks every 20 px (tens of x)")
print("      " + "".join(str(x // 20 % 10) if x % 20 < a.step else " " for x in xs))
for y in range(y0, min(y1, h), a.ystep):
    print(f"y={y:4d} " + "".join(cls(x, y) for x in xs))
