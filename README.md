# github-profile-studio

A Claude skill for building a GitHub profile README that fits the person: what they want to show, the style they like, and true facts, previewed in both themes before anything is published.

[中文说明](README.zh-CN.md)

## What it can do

- **Copy a style, not a person.** Point at a profile you like. The skill takes it apart — licence, layout, widgets and how each is produced — and rebuilds the look with your own data.
- **Portrait card.** Turn a photo, a character you choose, or your avatar into a coloured ASCII portrait inside a neofetch-style terminal card, with live GitHub stats refreshed daily by a workflow. It includes tools for cutting figures out of busy artwork and patching gaps.
- **Widgets and sections.** A catalogue of common blocks (stats, typing headers, skill icons, contribution snakes, blog feeds, project tables), with notes on which are live services and which are generated into your repo.
- **Content with judgement.** It asks what to show and what to keep private, presents projects and contributions clearly, and lists languages from your actual commits.
- **Real previews and a safe publish.** It renders the README with GitHub's own Markdown API in light and dark at profile width. It publishes only with your approval, then verifies the live page.

## Install

Copy or clone this folder into your skills directory, for example:

```bash
git clone https://github.com/DEOWL-kan/github-profile-studio ~/.claude/skills/github-profile-studio
```

Then ask Claude things like:
- "Make my GitHub profile look nicer"
- "Use this picture for my profile card"
- "I like how @someone's profile looks — make mine similar"
- "Show my open-source contributions but not my company work"

## Requirements

`gh` (logged in), Python 3 (stdlib only), ImageMagick 7 (`magick`), Chrome or Chromium for previews, optionally `rsvg-convert`.

## Layout

```
SKILL.md                  workflow and working principles
references/               replicate · portrait · components · content · design · publishing
scripts/                  github_facts · inspect_profile · preview · scan_languages · pixel_map · cutout · fill_paper
assets/neofetch-card/     card generator + card.json, image-to-ASCII converter, README, daily workflow
```

## Notes

- The neofetch-card code is original. The idea follows the neofetch-style profiles popularised by Andrew6rant.
- Keep source images you do not own out of public repositories; the card only needs the derived ASCII.

## License

MIT
