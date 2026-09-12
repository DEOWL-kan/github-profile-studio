#!/usr/bin/env python3
"""Bake a picture into art.txt and art_colors.json for update_profile.py.

Run once, locally. Needs ImageMagick's `magick` on PATH; the rest is stdlib.
Cells are filled by brightness, and cells on a strong outline get a stroke
glyph (- \\ | /) that follows the line. The outline is what keeps a face
recognisable at this size; plain brightness ramps smear it away.

With --braille each cell is a 2 x 4 dot braille glyph, dithered from the
picture: eight times the detail, so eyes and lashes survive as dark gaps.

  python3 make_art.py chisa.png --cols 72 [--crop 600x800+120+0] [--trim] [--mono] [--braille]
"""
import argparse
import json
import math
import subprocess
from collections import deque

from update_profile import CHAR_W, HERE, LINE_H

RAMP = ".:-=+*#%@"  # foreground fill, dim to bright
STROKES = "-\\|/"  # outline at 0, 45, 90, 135 degrees; screen y points down
SX, SY = 3, 5  # samples per cell: a 0.6 x 1.0 cell becomes square samples
GW, GH = 6, 10  # glyph bitmap per cell for --shape, same 0.6 x 1.0 proportions as the cell
BRAILLE_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))  # [dot row][dot col]


def run_magick(src, pre, *args):
    cmd = ["magick", src, "-background", "white", "-alpha", "remove", "-alpha", "off", *pre, *args]
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def lum(c):
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255


def stroke(phi):
    """Glyph for an outline whose intensity gradient points at angle phi (radians)."""
    line = (math.degrees(phi) + 90) % 180
    return STROKES[round(line / 45) % 4]


def outlines(gray, w, h, cols, rows):
    """Per cell: (coherent edge strength per sample, gradient angle)."""
    acc = [[0.0, 0.0] for _ in range(cols * rows)]

    def g(x, y):
        return gray[min(max(y, 0), h - 1) * w + min(max(x, 0), w - 1)]

    for y in range(h):
        for x in range(w):
            gx = g(x + 1, y - 1) + 2 * g(x + 1, y) + g(x + 1, y + 1) - g(x - 1, y - 1) - 2 * g(x - 1, y) - g(x - 1, y + 1)
            gy = g(x - 1, y + 1) + 2 * g(x, y + 1) + g(x + 1, y + 1) - g(x - 1, y - 1) - 2 * g(x, y - 1) - g(x + 1, y - 1)
            m = math.hypot(gx, gy)
            if m:
                # Doubled angle: the two sides of a thin line have opposite
                # gradients, which would cancel instead of adding up.
                a = acc[min(y // SY, rows - 1) * cols + min(x // SX, cols - 1)]
                a[0] += (gx * gx - gy * gy) / m
                a[1] += 2 * gx * gy / m
    return [(math.hypot(c, s) / (SX * SY), math.atan2(s, c) / 2) for c, s in acc]


def braille_cells(gray, cols, rows, bg):
    """Floyd-Steinberg dither at 2 x 4 dots per cell; a lit dot is a bright pixel."""
    w, h = cols * 2, rows * 4
    v = [g / 255 for g in gray]
    bits = [0] * (cols * rows)
    for y in range(h):
        for x in range(w):
            i, cell = y * w + x, (y // 4) * cols + x // 2
            new = 1.0 if v[i] >= 0.5 else 0.0
            err = v[i] - new
            if new and not bg[cell]:
                bits[cell] |= BRAILLE_BITS[y % 4][x % 2]
            if x + 1 < w:
                v[i + 1] += err * 7 / 16
            if y + 1 < h:
                if x > 0:
                    v[i + w - 1] += err * 3 / 16
                v[i + w] += err * 5 / 16
                if x + 1 < w:
                    v[i + w + 1] += err / 16
    return [chr(0x2800 + b) if b else " " for b in bits]


def glyph_masks(font="/System/Library/Fonts/Menlo.ttc"):
    """Every printable ASCII glyph, drawn as the card draws it, averaged down to GW x GH."""
    masks = {}
    for code in range(32, 127):
        ch = chr(code)
        text = {"%": "%%", "\\": "\\\\", "@": "\\@"}.get(ch, ch)  # ImageMagick escapes
        # The card puts the baseline 0.8 em down a 1.0 em row, so do the same in a 60 x 100 box.
        raw = subprocess.run(["magick", "-size", "60x100", "xc:black", "-font", font, "-pointsize", "100",
                              "-fill", "white", "-annotate", "+0+80", text, "-resize", f"{GW}x{GH}!",
                              "-depth", "8", "gray:-"], check=True, capture_output=True).stdout
        masks[ch] = [b / 255 for b in raw]
    return masks


def shape_cells(gray, cols, rows, bg, masks, floor=0.0):
    """Per cell, the glyph whose shape is closest to that patch of the picture.

    floor lifts every figure cell to at least that brightness, so dark hair and
    shadows get glyphs instead of leaving holes in the figure.
    """
    # A glyph never fills its cell, so scale brightness to the densest glyph's
    # coverage; otherwise every mid tone would pick the densest glyph.
    cover = max(sum(m) / len(m) for m in masks.values())
    items = list(masks.items())
    w = cols * GW
    out = []
    for cy in range(rows):
        for cx in range(cols):
            if bg[cy * cols + cx]:
                out.append(" ")
                continue
            t = [(floor + (1 - floor) * gray[(cy * GH + y) * w + cx * GW + x] / 255) * cover
                 for y in range(GH) for x in range(GW)]
            out.append(min(items, key=lambda kv: sum((a - b) ** 2 for a, b in zip(t, kv[1])))[0])
    return out


def largest_region(glyphs, cols, rows):
    """Blank every glyph that is not 8-connected to the biggest drawn region."""
    seen, best = [False] * len(glyphs), []
    for s in range(len(glyphs)):
        if glyphs[s] == " " or seen[s]:
            continue
        comp, q = [], deque([s])
        seen[s] = True
        while q:
            i = q.popleft()
            comp.append(i)
            x, y = i % cols, i // cols
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    j = ny * cols + nx
                    if 0 <= nx < cols and 0 <= ny < rows and glyphs[j] != " " and not seen[j]:
                        seen[j] = True
                        q.append(j)
        if len(comp) > len(best):
            best = comp
    keep = set(best)
    return [g if i in keep else " " for i, g in enumerate(glyphs)]


def background(colors, cols, rows, tol):
    """Cells joined to the border that match the corner colour; interior whites stay."""
    corners = [colors[0], colors[cols - 1], colors[-cols], colors[-1]]
    bg = [sum(ch) / 4 for ch in zip(*corners)]
    near = [math.dist(c, bg) <= tol for c in colors]
    seen = [False] * len(colors)
    q = deque(i for i in range(len(colors))
              if near[i] and (i < cols or i >= len(colors) - cols or i % cols in (0, cols - 1)))
    for i in q:
        seen[i] = True
    while q:
        i = q.popleft()
        x, y = i % cols, i // cols
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            j = ny * cols + nx
            if 0 <= nx < cols and 0 <= ny < rows and near[j] and not seen[j]:
                seen[j] = True
                q.append(j)
    return seen


def lift(c, floor=0.42):
    """Raise dark colours so they stay visible on the dark card, keeping the hue."""
    level = lum(c)
    f = min(floor / level, 6.0) if 0 < level < floor else 1.0
    return [min(255, (round(v * f) + 8) // 16 * 16) for v in c]


def tint_of(c, floor):
    """Hex colour of a figure cell; near-black takes the card's art colour so it stays visible."""
    return None if lum(c) < 0.04 else "#%02x%02x%02x" % tuple(lift(c, floor))


def bake(src, cols, pre, tone, color, edges, tol, mono, braille, shape, fill_floor=0.0, largest=False):
    """pre shapes the picture; tone only steers glyph choice; color only tints."""
    w, h = map(int, run_magick(src, pre, "-format", "%w %h", "info:").split())
    rows = max(1, round(cols * h / w * CHAR_W / LINE_H))
    rgb = run_magick(src, pre + color, "-scale", f"{cols}x{rows}!", "-depth", "8", "rgb:-")
    colors = [tuple(rgb[i:i + 3]) for i in range(0, cols * rows * 3, 3)]
    bg = background(colors, cols, rows, tol)
    if braille or shape:
        if braille:
            gray = run_magick(src, pre + tone, "-colorspace", "Gray", "-resize", f"{cols * 2}x{rows * 4}!", "-depth", "8", "gray:-")
            glyphs, floor = braille_cells(gray, cols, rows, bg), 0.62
        else:
            gray = run_magick(src, pre + tone, "-colorspace", "Gray", "-resize", f"{cols * GW}x{rows * GH}!", "-depth", "8", "gray:-")
            glyphs, floor = shape_cells(gray, cols, rows, bg, glyph_masks(), fill_floor), 0.42
        if largest:
            glyphs = largest_region(glyphs, cols, rows)
        text = ["".join(glyphs[y * cols:(y + 1) * cols]).rstrip() for y in range(rows)]
        tint = [[None if glyphs[y * cols + x] == " " else tint_of(colors[y * cols + x], floor)
                 for x in range(cols)] for y in range(rows)]
        return text, None if mono else tint
    gw, gh = cols * SX, rows * SY
    gray = run_magick(src, pre + tone, "-colorspace", "Gray", "-resize", f"{gw}x{gh}!", "-depth", "8", "gray:-")
    cells = outlines(gray, gw, gh, cols, rows)

    fg_strength = sorted(s for (s, _), b in zip(cells, bg) if not b) or [0]
    # edges <= 0 turns outlines off; otherwise keep the strongest share of figure cells.
    cut = min(int(len(fg_strength) * (1 - edges)), len(fg_strength) - 1)
    threshold = max(fg_strength[cut], 20) if edges > 0 else math.inf

    text, tint = [], []
    for y in range(rows):
        line, crow = "", []
        for x in range(cols):
            i = y * cols + x
            strength, phi = cells[i]
            if strength >= threshold:
                line += stroke(phi)
                crow.append(None)  # outlines use the card's art colour
            elif bg[i]:
                line += " "
                crow.append(None)
            else:
                c = colors[i]
                line += RAMP[min(int(lum(c) * len(RAMP)), len(RAMP) - 1)]
                crow.append("#%02x%02x%02x" % tuple(min(v, 255) for v in lift(c)))
        text.append(line.rstrip())
        tint.append(crow)
    return text, None if mono else tint


def selfcheck():
    assert stroke(math.pi / 2) == "-"  # brightness changes vertically: horizontal line
    assert stroke(0) == "|"
    assert stroke(-math.pi / 4) == "\\" and stroke(math.pi / 4) == "/"
    grid = [(255, 255, 255)] * 9
    grid[4] = (255, 255, 254)  # near-white but walled in? no: its neighbours are background
    assert all(background(grid, 3, 3, 10))
    walled = [(0, 0, 0)] * 25
    walled[0] = walled[12] = (255, 255, 255)  # corner is background, centre white is not
    walled[4] = walled[20] = walled[24] = (255, 255, 255)
    bg = background(walled, 5, 5, 10)
    assert bg[0] and not bg[12]
    assert braille_cells([255] * 8, 1, 1, [False]) == ["\u28ff"]  # every dot lit
    assert braille_cells([0] * 8, 1, 1, [False]) == [" "]
    assert braille_cells([255] * 8, 1, 1, [True]) == [" "]  # background stays blank
    fake = {" ": [0.0] * (GW * GH), "#": [1.0] * (GW * GH)}
    assert shape_cells([255] * (GW * GH), 1, 1, [False], fake) == ["#"]
    assert shape_cells([0] * (GW * GH), 1, 1, [False], fake) == [" "]
    fake["."] = [0.3] * (GW * GH)
    assert shape_cells([0] * (GW * GH), 1, 1, [False], fake, floor=0.35) == ["."]  # dark still drawn
    assert largest_region(list("ab #"), 4, 1) == list("ab  ")


if __name__ == "__main__":
    selfcheck()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--cols", type=int, default=72)
    ap.add_argument("--crop", help="ImageMagick geometry, e.g. 600x800+120+0")
    ap.add_argument("--trim", action="store_true", help="trim a flat border first")
    ap.add_argument("--edges", type=float, default=0.22, help="share of figure cells drawn as outline")
    ap.add_argument("--tol", type=float, default=40, help="RGB distance that still counts as background")
    ap.add_argument("--mono", action="store_true", help="one colour, like a classic neofetch logo")
    ap.add_argument("--braille", action="store_true", help="2 x 4 dot glyphs, dithered")
    ap.add_argument("--shape", action="store_true", help="pick each glyph by shape, not just brightness")
    ap.add_argument("--contrast", type=float, default=0, help="sigmoidal contrast strength, e.g. 4")
    ap.add_argument("--gamma", type=float, default=0, help="lift mid tones, e.g. 1.8, so darker hair still fills in")
    ap.add_argument("--saturation", type=int, default=100, help="colour saturation in percent, e.g. 150")
    ap.add_argument("--floor", type=float, default=0, help="--shape: minimum brightness inside the figure, e.g. 0.35")
    ap.add_argument("--largest", action="store_true", help="drop glyph islands cut off from the figure")
    a = ap.parse_args()
    pre = (["-crop", a.crop, "+repage"] if a.crop else []) + (["-fuzz", "8%", "-trim", "+repage"] if a.trim else [])
    tone = (["-sigmoidal-contrast", f"{a.contrast}x50%"] if a.contrast else []) + (["-gamma", str(a.gamma)] if a.gamma else [])
    color = ["-modulate", f"100,{a.saturation}"] if a.saturation != 100 else []
    text, tint = bake(a.src, a.cols, pre, tone, color, a.edges, a.tol, a.mono, a.braille, a.shape, a.floor, a.largest)
    (HERE / "art.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    colors_path = HERE / "art_colors.json"
    if tint:
        colors_path.write_text(json.dumps(tint, separators=(",", ":")))
    elif colors_path.exists():
        colors_path.unlink()
    print(f"art.txt: {a.cols} x {len(text)}{'' if tint else ' (mono)'}")
