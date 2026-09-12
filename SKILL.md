---
name: github-profile-studio
description: Design, build and publish a GitHub profile README that fits the person — what they want to show, the look they like, and how they want to present their projects, experience and contributions. Recreate the style of a profile they admire with their own data; turn a photo, a chosen character or their avatar into a coloured ASCII portrait inside a neofetch-style terminal card with live stats; compose sections and widgets such as stats, typing headers, skill icons, contribution snakes and project showcases; preview in both themes at GitHub's width, then publish the profile repo with their approval. Use this whenever someone wants to create, redesign, polish or copy the style of a GitHub profile page or organisation profile, even if they never say README (also 个人主页, 主页做好看点, 把项目放到主页, 参考别人的主页).
---

# GitHub Profile Studio

Help a person end up with a GitHub profile they are glad to show: it says what they want said, in a style they like, with true facts. The user is the judge of taste. Your job is to understand them, render real previews quickly, and refine from their reactions.

`SKILL_DIR` below means this skill's base directory.

## How to work

- **Speak the user's language.** The README may use another language (English reaches the widest audience). Offer translations of drafts.
- **Start from the person, not a template.** Learn the goals, the audience and the taste first; then pick the paths that serve them.
- **Only real previews reach the user**: rendered in a browser at GitHub's width, in both themes, and looked at by you first (`scripts/preview.py`). If you must show a pipeline test, say plainly that it is one.
- **Build on what they already have.** If the profile already carries a design the user approved (card, portrait, colours), keep it and change only what the request is about.
- **Change what was asked, no more.** For judgement calls (a crop line, a colour, a parameter), render several candidates side by side and choose with evidence.
- **Restate ambiguous requests before building.** Short instructions often have two readings, and one wrong turn costs an iteration.
- **Show only verified facts, and only what the user wants shown.** Default to keeping private work private (content.md).
- **Follow the user's own conventions**: where repositories live, which files belong in them, and the commit identity. Ask when unknown. Never assume another workspace's rules.
- **Anything outward-facing needs an explicit yes**: creating repositories, pushing, editing profile settings, posting. Local work needs no permission.

## Workflow

### 1. Discover (read-only)

```bash
python3 "$SKILL_DIR/scripts/github_facts.py" LOGIN > facts.json   # add --private only to discuss private work
python3 "$SKILL_DIR/scripts/inspect_profile.py" LOGIN              # their current profile README, if any
```

Summarise briefly for the user:
- bio and pinned repos (forks show zero stars and look empty);
- whether a profile repo exists;
- public projects, contributions (merged and open) and languages.

### 2. Brief

Ask only what changes the result, and default the rest (content.md):
- the audience;
- what to show and what to hide;
- the look (a profile they like, an image or character, or "surprise me");
- the README language;
- static page or auto-updating;
- whether stats may include private work as anonymous counts. Their answer sets `private_contributions` in `card.json`.

### 3. Choose the path, or combine them

| The user wants | Read |
|---|---|
| "Make it look like X's profile" | references/replicate.md |
| A portrait (photo, character, avatar) in a terminal card with stats | references/portrait.md + `assets/neofetch-card/` |
| Sections and widgets (stats, typing header, icons, snake, blog feed…) | references/components.md |
| Mainly to present projects, experience, contributions | references/content.md |
| No idea yet | Render 2–3 quick directions and let them point |

Visual decisions follow references/design.md.

### 4. Build locally

- Work in a directory the user agrees on.
- **The card**: `cp -R "$SKILL_DIR/assets/neofetch-card/." DIR/`, then fill `DIR/card.json`. Get `langs` from `scripts/scan_languages.py` and `joined` from the facts.
- Prefer images generated into the repo by a workflow over live third-party services for anything central to the page.
- Keep a short work log of choices and exact commands.

### 5. Preview

```bash
GITHUB_TOKEN=$(gh auth token) python3 DIR/update_profile.py     # when using the card
python3 "$SKILL_DIR/scripts/preview.py" DIR OUT --login LOGIN --mobile   # light and dark, desktop and phone
```

Look at both PNGs yourself, then share them (in Claude Code: `! open PATH`). Say what changed and any known blemish.

### 6. Iterate

One requested change per round; candidates for judgement calls; symptom-to-fix tables in portrait.md. Back up approved outputs before experiments, since generators overwrite them.

### 7. Publish, verify, hand over

Only after an explicit yes. Follow references/publishing.md:
- repo naming (user or organisation profile) and which files to commit;
- commit identity;
- running the workflow once;
- live verification;
- the settings only the user can change (bio, pins).

## Bundled files

| Path | What it does |
|---|---|
| `scripts/github_facts.py` | A person's GitHub facts as JSON; private work reduced to counts unless `--private` |
| `scripts/inspect_profile.py` | Takes apart any profile README: licence, layout, components and how each is produced, workflows, assets |
| `scripts/preview.py` | Renders README.md with GitHub's Markdown API and screenshots light and dark at 830 px |
| `scripts/scan_languages.py` | Languages the person really wrote, from their own commits in local repos (counts only) |
| `scripts/pixel_map.py` | Character map of image regions, to measure crop lines and gaps |
| `scripts/cutout.py` | Cuts a figure out of busy artwork |
| `scripts/fill_paper.py` | Paints bare-paper gaps inside a figure with skin colour |
| `assets/neofetch-card/` | Card generator (`update_profile.py`, `card.json`), image-to-ASCII converter (`make_art.py`), README, daily workflow |
| `references/*.md` | replicate, portrait, components, content, design, publishing |

Requirements: `gh` (logged in), Python 3 (stdlib only), ImageMagick 7 (`magick`) for image work, Chrome or Chromium for previews, and optionally `rsvg-convert` for quick static renders.
