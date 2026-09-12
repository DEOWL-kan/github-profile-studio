# Visual design

Read this when choosing a style, adjusting the card, or judging a composition.

## Principles

- **One hero, restraint elsewhere.** Profiles people admire tend to have one strong visual, little text, a clear hierarchy and one palette. Walls of badges and stat cards read as noise, and cards with small numbers (one follower, zero stars) look sparse.
- **The user's taste decides.** Offer 2–3 rendered directions when they have no preference, then refine from their reactions rather than from theory.
- **Both themes, real width.** Judge every change in a real browser at the README width (about 830 px), in light and dark (`scripts/preview.py`).
- **Honest data.** No invented numbers; an empty-looking stat is better replaced than faked.

## Studying references

- The neofetch-style profile made popular by Andrew6rant/Andrew6rant: a terminal-like card, ASCII art on the left, key–value info on the right, refreshed by a workflow. Many profile repos like this have no licence, so the template in this skill is original code that follows the idea.
- abhisheknaiidu/awesome-github-profile-readme (CC0) collects hundreds of examples by category: code mode, minimalistic, anime, retro, dynamic, and more. Screenshot a handful to calibrate (replicate.md has the command).

## The neofetch card (assets/neofetch-card)

- **Frame**: 920×540, rounded 12, 1 px border. A 34 px macOS-style title bar with three dots and `LOGIN@github: ~`.
- **Left**: a solid, dark backdrop (`backdrop`, default `#161b2e`), 442 px wide, edge to edge, in both themes, with the portrait centred on it.
- **Right**, from top to bottom:
  - `❯ neofetch`
  - the name, 30 px bold
  - `@login · role`
  - a gradient rule
  - aligned key–value rows from `card.json`
  - language chips in GitHub's colours, wrapping in the value column
  - four stat pills: repos, commits, contributed, followers
  - eight swatches taken from the portrait
  - a blinking cursor
- **Content**: everything about the person lives in `card.json` (`login`, `name`, `role`, `joined`, `rows`, `langs`, `backdrop`, `swatches`). The code stays untouched.
- **Fonts**: system font stacks only, with `textLength` on every row so fallback fonts cannot skew the grid.

## Lessons learned (each one came from a real complaint)

- **No fade-in or reveal animations.** Screenshots and renderers that skip animation show frame zero, and the panel was blank. Only a blinking cursor remains, whose first frame is complete, and it stops under `prefers-reduced-motion`.
- **Choosing the portrait backdrop.**
  - Textured backgrounds (water, rays, bubbles) competed with the figure or looked unfinished.
  - A white panel was not what the user meant.
  - What worked: a solid, darkish colour that doesn't touch the figure's colours.
  - Pick it by rendering 4–5 candidates side by side. A colour near the hair's hue swallows the hair: teal hair on a deep teal backdrop failed. A neutral black clashed with a blue-toned card.
- **An approved design is the baseline.** When the profile already has a card the user signed off (colours, backdrop, portrait), a new request changes only its own subject. One test run swapped the user's chosen navy backdrop for another colour unasked.
- **Check the phone width** (`preview.py --mobile`): a single wide card shrinks its text to about 6 px on phones.
- **Delete rows the person doesn't care about** (OS, IDE, and so on). Fewer rows read better.
- **Rendering the stats**: prefer "contributed" over "merged PRs" when the person does not want to spotlight pull requests.
- **Title and structure over decoration**: when a panel looks bad, fix the hierarchy (size, spacing, alignment, colour of keys versus values) before adding ornaments.

## Accessibility

- Every image gets meaningful alt text.
- Motion respects `prefers-reduced-motion`.
- Text inside images keeps enough contrast in both themes.
- Colour is never the only carrier of meaning.
