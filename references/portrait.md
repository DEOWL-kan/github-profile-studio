# Path B — a portrait card from a picture

Read this when the page should feature a picture of the person, a character they chose, or their avatar, drawn as coloured ASCII inside the neofetch-style card (`assets/neofetch-card`). The converter `make_art.py` sits in that template next to `update_profile.py`, because it reads the glyph-cell geometry from it.

## 1. Get the picture

- **The user supplies it**: pasted images are usually temporary files, so copy them into the working directory first.
- **The user names a character or artwork**: find candidates yourself rather than handing the search back. Useful sources:
  - web search;
  - a fan wiki's MediaWiki API (`api.php?action=query&generator=images&titles=PAGE&prop=imageinfo&iiprop=url|size&format=json`);
  - Zerochan (`?json`, with an honest User-Agent);
  - official merchandise pages, which is where chibi/Q versions often live.
  - Double-check the title: similarly named works are easy to confuse.
  - Skip suggestive images; this is a public page.
- **No picture**: offer the GitHub avatar (`curl -L https://github.com/LOGIN.png -o avatar.png`).
- Put candidates on one contact sheet and look at it yourself first: `magick montage a.png b.png ... -geometry 360x440+8+8 -tile 3x -background '#222' sheet.png`. Good candidates:
  - a front or three-quarter view;
  - the head large in the frame;
  - clean line art;
  - a plain background, or a white cut-out outline.
- **Rights**: keep the source image and intermediate files local. Commit only the derived `art.txt` and `art_colors.json`, and tell the user where the picture came from.

## 2. Measure before cropping

Don't guess crop lines or repair boxes. Map the pixels:

```bash
python3 "$SKILL_DIR/scripts/pixel_map.py" src.png --x 140:356 --y 250:346
```

`#` is ink, `o` is colour (skin, hair, shading), `.` is paper, `-` is grey. Read off three things: where the chin ends, where the clothing starts, and which rows a paper gap spans.

- **Crop the head plus the whole chin, and stop before the clothing.** White hoodies and collars turn into scattered blobs that ruin the picture.
- **Take requests literally.** "Complete the chin" means the chin, not the neck and shoulders too.
- **When unsure**, render each candidate crop and compare them side by side (section 5).

## 3. Cut the figure out

```bash
magick src.png -crop WxH+X+Y +repage head.png
python3 "$SKILL_DIR/scripts/fill_paper.py" head.png fixed.png --box X0,Y0,X1,Y1 --skin X0,Y0,X1,Y1   # only if needed
python3 "$SKILL_DIR/scripts/cutout.py" fixed.png cut.png [--drop-hedge]
```

`cutout.py` works in three steps:
1. It floods the scenery from the top, left and right edges up to the figure's white outline.
2. It keeps the largest region of ink or colour as the figure.
3. It paints white everything reachable from the edges around the figure.

Enclosed whites such as eyes keep their colour. The bottom edge is not a seed, because a bust runs off the frame.

`fill_paper.py` repairs a common manga trait: lit skin left as bare paper, which reads as a notch once the background is gone.
- Keep its box tight. Rows below the chin would paint the clothing as skin blotches.
- On rows with the mouth, start the box to the right of the lips.
- It is fine to run it twice with two boxes.

After each step, compare before and after side by side: `magick a.png b.png +append -resize x520 view.png`.

## 4. Convert to ASCII

A good starting point for anime and manga portraits on the dark backdrop:

```bash
python3 make_art.py cut.png --trim --cols 100 --shape --saturation 150 --gamma 1.8 --floor 0.45 --largest
```

| Flag | Effect | Adjust when |
|---|---|---|
| `--cols` | Detail. The card's art box is about 410×474 px; 100 cols gives about 6.8 px glyphs | Blurry: more. Glyphs unreadable: fewer |
| `--shape` | Picks each glyph by its shape, not just brightness; eyes and hairlines survive | Keep on |
| `--gamma` | Lifts mid tones for glyph choice only | Dark hair looks empty (1.5–2.2) |
| `--saturation` | Colour saturation only | Colours look grey (130–160) |
| `--floor` | Minimum brightness inside the figure, so dark areas still get glyphs | Holes inside the figure: 0.45 |
| `--largest` | Keeps only the biggest glyph region | Stray specks or fragments around the figure |
| `--crop` / `--trim` | Crop, or trim a flat border, before converting | Usually `--trim` after cutout |
| `--edges` | Directional stroke glyphs | Not recommended: they cover the eyes |
| `--braille` | Braille dots | Not recommended: dot size depends on the viewer's fonts, often tiny and dim |
| `--mono` | One colour | For a classic monochrome neofetch look |

The colours are lifted for a dark backdrop, so keep the portrait's backdrop dark (design.md).

## 5. Compare candidates whenever a choice is a judgement call

```bash
cp art.txt art.ok.txt; cp art_colors.json art_colors.ok.json   # make_art.py overwrites these
for v in "a --floor 0.3" "b --floor 0.45"; do set -- $v; n=$1; shift
  python3 make_art.py cut.png --trim --cols 100 --shape --saturation 150 --gamma 1.8 --largest "$@"
  python3 update_profile.py >/dev/null && rsvg-convert dark_mode.svg -o "c-$n.png"
done
magick montage c-*.png -geometry +6+6 -tile 4x -background '#222' compare.png
```

Keep the final command in the work log so the portrait can be regenerated.

## 6. Symptom → cause → fix

| The user sees | Cause | Fix |
|---|---|---|
| Holes or "gaps" inside the figure (hair strands, shadows under the fringe) | Dark areas map to spaces | `--floor 0.45` |
| Specks or broken fragments around the figure | Islands cut off from the figure | `--largest` |
| A diagonal notch cut out of the face or chin | The artwork left lit skin as bare paper | `fill_paper.py` with a tight box |
| The chin is cut off | The crop's bottom edge is too high | Measure with `pixel_map.py`; extend to just below the chin |
| A mess of blobs at the bottom, like legs | Clothing got into the crop | Stop the crop before the clothing |
| A line across the picture | Light-grey panel borders counted as both wall and ink | cutout.py's outside flood handles it; otherwise crop it away |
| Face and hair painted white after cutout | Clothing without an outline let the flood leak in | Crop the clothing away; cutout.py treats colour as figure |
| Hair looks grey | Gamma was applied to colour | Raise `--saturation`; gamma only affects glyph choice |
| Hair edges melt into the background | The backdrop is close to the hair colour, or too textured | Change the backdrop (design.md) |
| A yellow-green patch at the edge | Foliage specks touching the outline | `cutout.py --drop-hedge` |
