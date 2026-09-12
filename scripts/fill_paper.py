#!/usr/bin/env python3
"""Paint bare paper inside a figure with its skin colour.

Manga often leaves the lit side of a face or neck as unpainted paper; once the
scenery is cut away that reads as a hole. Inside --box, a paper pixel with
figure pixels (ink or colour) on both its left and its right in the same row
gets the average skin colour sampled from --skin. Keep the box tight: rows
below the chin would paint the clothing too. Run it before cutout.py.

  python3 fill_paper.py in.png out.png --box X0,Y0,X1,Y1 --skin X0,Y0,X1,Y1
"""
import argparse
import subprocess

paper = lambda p: min(p) >= 190 and max(p) - min(p) < 28
figure = lambda p: min(p) < 90 or max(p) - min(p) >= 28
skin_like = lambda p: max(p) - min(p) >= 28 and min(p) >= 90


def fill(px, w, box, skin):
    """Paint paper flanked by figure inside box (x0, y0, x1, y1, end exclusive); returns pixels painted."""
    x0, y0, x1, y1 = box
    painted = 0
    for y in range(y0, y1):
        row = [px[y * w + x] for x in range(x0, x1)]
        fig = [k for k, p in enumerate(row) if figure(p)]
        if len(fig) < 2:
            continue
        for k in range(fig[0] + 1, fig[-1]):
            if paper(row[k]):
                px[y * w + x0 + k] = skin
                painted += 1
    return painted


def selfcheck():
    k, p, s = (20, 20, 20), (255, 255, 255), (240, 200, 170)
    row = [p, k, p, p, k, p]
    assert fill(row, 6, (0, 0, 6, 1), s) == 2 and row == [p, k, s, s, k, p], "only paper between figure"


if __name__ == "__main__":
    selfcheck()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--box", required=True, help="x0,y0,x1,y1 region to repair")
    ap.add_argument("--skin", required=True, help="x0,y0,x1,y1 region to sample the skin colour from")
    a = ap.parse_args()
    box = tuple(map(int, a.box.split(",")))
    sx0, sy0, sx1, sy1 = map(int, a.skin.split(","))
    run = lambda *c, **kw: subprocess.run(c, check=True, capture_output=True, **kw).stdout
    w, h = map(int, run("magick", a.src, "-format", "%w %h", "info:").split())
    raw = run("magick", a.src, "-background", "white", "-alpha", "remove", "-alpha", "off", "-depth", "8", "rgb:-")
    px = [tuple(raw[3 * i:3 * i + 3]) for i in range(w * h)]
    sample = [px[y * w + x] for y in range(sy0, sy1) for x in range(sx0, sx1) if skin_like(px[y * w + x])]
    if not sample:
        raise SystemExit("no skin-coloured pixels in --skin; pick a region of plain skin")
    skin = tuple(sum(c[i] for c in sample) // len(sample) for i in range(3))
    n = fill(px, w, box, skin)
    run("magick", "-size", f"{w}x{h}", "-depth", "8", "rgb:-", a.dst, input=b"".join(bytes(p) for p in px))
    print(f"skin #{bytes(skin).hex()}, painted {n} px -> {a.dst}")
