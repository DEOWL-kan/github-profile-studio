# Publishing and handing over

Read this when the user approves publishing, and whenever you verify the live page.

## Where things go

- **User profile**: a public repository named exactly like the login (`LOGIN/LOGIN`), with `README.md` at its root.
- **Organisation profile**: a public repo `ORG/.github` with `profile/README.md`. A private `ORG/.github-private` with `profile/README.md` is shown only to members.
- **Local working copy**: follow the user's own conventions for where repositories live, and ask if you don't know them. Don't import conventions from elsewhere, including your own habits or another project's rules.
- **Files in the public repo**: only the deliverables, i.e. the README, the generated images, the generator scripts, their config, the workflows and a `.gitignore`. Keep source photos, cut-outs and scratch renders local. Add agent, editor or tooling files only if the user wants them there.

## Publishing (only after an explicit yes)

1. **Commit identity**: the user's choice. A good default is their GitHub noreply address, `ID+LOGIN@users.noreply.github.com` (`gh api user --jq .id`), configured in this repository only. Add whatever commit trailers the current environment requires.
2. **Create and push**: `gh repo create LOGIN/LOGIN --public --source . --remote origin --push`. Then check that `gh api repos/LOGIN/LOGIN/commits/main --jq .sha` equals the local `HEAD`.
3. **Run the scheduled workflow once**: `gh workflow run update.yml`, then watch it (`gh run watch ID --exit-status`). Confirm the bot's commit, then `git pull --ff-only` locally.
4. **Tokens**: the workflow's `GITHUB_TOKEN` sees public data only.
   - Contribution counts include private work only if the user turns on "Private contributions" in their profile settings.
   - A personal access token in a repository secret can read more. Suggest it only if the user wants that, with minimal read-only scope.

## Verifying the live page

- GitHub rewrites relative image paths in the profile README to `/LOGIN/LOGIN/raw/main/FILE`. Check the page's HTML (`curl -sL https://github.com/LOGIN`) for those URLs, and check that each returns 200 with an image content type.
- Render the live image URL in a local page and screenshot it. This is the reliable proof that it displays.
- Headless screenshots of github.com often show images as alt text because of lazy loading. That alone does not mean the page is broken.
- Raw file URLs are cached for a few minutes, so fresh numbers show up with a delay.

## Handing over

- Settings only the user can change in the web UI:
  - bio, location, links, social accounts and avatar;
  - pinned repositories — they can pin upstream projects they contributed to, which show real star counts, unlike forks;
  - the "Private contributions" toggle.
- How to update later: edit the config or content, run the generator, preview, and commit. Numbers refresh on schedule.
- Keep a short log of the chosen parameters (crop, conversion flags, colours) somewhere the user controls, so the look can be regenerated.
