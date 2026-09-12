#!/usr/bin/env python3
"""Cut a figure out of busy artwork and paint everything around it white.

Made for manga and anime panels, where the figure usually has a white cut-out
outline and busy scenery behind it:

1. flood the scenery from the picture's edges, stopping at the white outline;
2. the figure is the largest region of pixels that are dark (ink) or visibly
   coloured (skin, hair) - white clothing, paper and panel gutters are neither;
3. paint white everything reachable from the edges without crossing the figure,
   so enclosed whites such as eyes and highlights keep their colour.

The bottom edge is not a seed unless --seed-bottom, because a bust runs off the
bottom of the picture. Needs ImageMagick's `magick`; the rest is stdlib.

  python3 cutout.py in.png out.png [--sat 28] [--white 190] [--seed-bottom] [--drop-hedge]
"""
import argparse
import subprocess
from collections import deque


def neighbours(i, w, h, diag=False):
    x, y = i % w, i // w
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if diag else ())
    for dx, dy in steps:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h:
            yield ny * w + nx


def flood(seeds, passable, w, h):
    seen = bytearray(w * h)
    q = deque(i for i in seeds if passable(i))
    for i in q:
        seen[i] = 1
    while q:
        i = q.popleft()
        for j in neighbours(i, w, h):
            if not seen[j] and passable(j):
                seen[j] = 1
                q.append(j)
    return seen


def outside(px, w, h, sat_min=28, white_min=190, seed_bottom=False, drop_hedge=False):
    """1 for every pixel that is not part of the figure."""
    n = w * h
    lo = [min(p) for p in px]
    sat = [max(p) - min(p) for p in px]
    edges = list(range(w)) + [y * w for y in range(h)] + [y * w + w - 1 for y in range(h)]
    if seed_bottom:
        edges += list(range((h - 1) * w, n))
    # 1) The white outline, one pixel thicker so anti-aliased seams cannot leak.
    white = [lo[i] >= white_min and sat[i] < sat_min for i in range(n)]
    wall = white[:]
    for i in range(n):
        if white[i]:
            for j in neighbours(i, w, h):
                wall[j] = True
    scenery = flood(edges, lambda i: not wall[i], w, h)
    # 2) The figure: largest 8-connected region of ink or colour. Yellow-green
    # foliage is never hair (teal: g ~ b) or skin (r > g), so it can be dropped.
    hedge = [drop_hedge and p[1] > p[0] + 10 and p[1] > p[2] + 40 for p in px]
    ink = [not scenery[i] and not hedge[i] and (lo[i] < white_min or sat[i] >= sat_min) for i in range(n)]
    seen, best = bytearray(n), []
    for s in range(n):
        if ink[s] and not seen[s]:
            comp, q = [], deque([s])
            seen[s] = 1
            while q:
                i = q.popleft()
                comp.append(i)
                for j in neighbours(i, w, h, diag=True):
                    if ink[j] and not seen[j]:
                        seen[j] = 1
                        q.append(j)
            if len(comp) > len(best):
                best = comp
    figure = bytearray(n)
    for i in best:
        figure[i] = 1
    # 3) Outside: whatever the edges reach without crossing the figure.
    return flood(edges, lambda i: not figure[i], w, h)


def selfcheck():
    # 11x11: green scenery, a white outline ring, a dark figure with a white "eye".
    w = h = 11
    green, white, dark = (60, 150, 60), (255, 255, 255), (20, 20, 20)
    px = [green] * (w * h)
    for y in range(1, 10):
        for x in range(1, 10):
            px[y * w + x] = white if x in (1, 9) or y in (1, 9) else dark
    px[5 * w + 5] = white
    out = outside(px, w, h)
    assert out[0] and out[1 * w + 1], "scenery and outline are painted"
    assert not out[3 * w + 3], "the figure stays"
    assert not out[5 * w + 5], "an enclosed white (eye) keeps its colour"


if __name__ == "__main__":
    selfcheck()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--sat", type=int, default=28, help="max-min channel spread that counts as colour")
    ap.add_argument("--white", type=int, default=190, help="min channel that counts as white/paper")
    ap.add_argument("--seed-bottom", action="store_true", help="also flood from the bottom edge")
    ap.add_argument("--drop-hedge", action="store_true", help="treat yellow-green foliage as scenery")
    a = ap.parse_args()
    run = lambda *c, **k: subprocess.run(c, check=True, capture_output=True, **k).stdout
    w, h = map(int, run("magick", a.src, "-format", "%w %h", "info:").split())
    raw = bytearray(run("magick", a.src, "-background", "white", "-alpha", "remove", "-alpha", "off", "-depth", "8", "rgb:-"))
    out = outside([tuple(raw[3 * i:3 * i + 3]) for i in range(w * h)], w, h, a.sat, a.white, a.seed_bottom, a.drop_hedge)
    for i in range(w * h):
        if out[i]:
            raw[3 * i:3 * i + 3] = b"\xff\xff\xff"
    run("magick", "-size", f"{w}x{h}", "-depth", "8", "rgb:-", a.dst, input=bytes(raw))
    print(f"{sum(out) / (w * h):.0%} painted white -> {a.dst}")
