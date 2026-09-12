# Path D — what to say, and what not to

Read this for the brief, and whenever projects, experience, contributions or personal details are being written.

## The brief: ask what changes the result, default the rest

- **Who reads it**: recruiters, open-source maintainers, clients, peers, friends. This changes tone and what leads.
- **Identity**: how they describe themselves (for example "full-stack developer"), and whether a current role, location or company appears.
- **Show**:
  - their own public projects, and which ones;
  - open-source contributions (just repos, or merged changes with details);
  - languages and tools, experience, writing and talks, contact links.
- **Hide**: confirm the defaults below; people often have more to add.
- **Look**: a profile they like, an image or character, or no preference (then offer 2–3 quick directions as rendered previews).
- **Languages**: the language of the README, and the language to talk in. Offer a translation of drafts when they differ.
- **Maintenance appetite**: static, or refreshed by a workflow.

Use `scripts/github_facts.py LOGIN` first, so the questions are about choices rather than facts.

## Defaults for privacy and honesty (the user can override each)

- **Private repositories, and pull requests into them**: not shown, not named. Counts appear only if the user wants them.
- **Employer or client work**: not named unless the user says so. Describe it generically ("mobile app and backend for a healthcare startup") if they want the experience visible.
- **Unmerged pull requests, and the details of specific pull requests**: not shown unless asked. Some people want only repos, some want nothing.
- **Personal data** (email, location, age, birthday): only what the user asks for, even if it is already public on the profile.
- **Numbers**: only what an API returns today. No invented percentages, levels or ranks.
- **Private work in stats**: it's the user's call. Some want the anonymous total that reflects their day job; others want public numbers only. Ask, then set `private_contributions` in `card.json`. Also mention that "contributed" counts repos where a pull request is still open, in case that matters to them.
- **Languages and skills**: evidence first. `scan_languages.py` counts files the person actually committed. GitHub's language bytes cover public repositories. List what clears a threshold and mention the rest.

## Presenting projects

- Pick 3–6. For each: what it does in one line, why it is interesting, the stack, a link, and optionally a screenshot or GIF, a status, or stars.
- Formats: a Markdown table (compact); an HTML table with an image per cell (visual); bullet lines (minimal). Pinned repositories in the profile's sidebar complement the README; they are set by the user in the GitHub UI.
- For a contribution, name the upstream project and say what the change did, in plain words taken from the pull request itself — unless the user wants no details.

## Presenting experience

- Roles as short lines: years, role, domain, and one achievement each. Keep employer names out unless allowed.
- A timeline or `<details>` block keeps a long history from dominating the page.

## Language and drafts

- Write the README in the language the user chooses. English reaches the widest open-source audience.
- Show drafts with a translation into the user's own language for review.
- Watch for phrasing that has two readings. For example, in Chinese "不用写出 A，还有 B" means neither A nor B. When a sentence can be read two ways, restate your reading before building.
- If the user says the content will come later, build the style with placeholders and keep the placeholders obviously fake.
