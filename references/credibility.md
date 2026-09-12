# Path E — look like the strong developer you are

Read this when the user wants their profile to look more impressive, professional or senior. For example: "make me look like a serious developer", "recruiters should take me seriously", "I want maintainers to trust my PRs". The goal is to make **real** strength visible fast. Nothing here involves inventing strength, and section 6 explains why that always backfires.

Start with `scripts/audit_profile.py LOGIN`. It lists the weak signals to fix and the strongest proof the person already has.

## 1. What visitors check in the first seconds

- **Recruiters and hiring managers**:
  - a clear role and focus;
  - evidence they can ship: real projects, and contributions to known codebases;
  - recent activity;
  - a way to reach them.
- **Open-source maintainers**:
  - merged PRs elsewhere;
  - the quality of those PRs (tests, clear descriptions);
  - responsiveness.
- **Clients and peers**:
  - what they build;
  - demos;
  - writing that shows how they think.

Ask who matters most (content.md) and lead with what that reader checks.

## 2. Proof beats adjectives

"Passionate full-stack ninja" says nothing. These say a lot:

- **Merged contributions to well-known projects.** Name the project, show its stars with a live badge, and say in one plain sentence what the change did and why it mattered. For example: "Django (80k★): fixed a timezone bug that shifted scheduled jobs by an hour, with tests." A fix to a real bug in a big codebase shows reading unfamiliar code, root-causing and passing review.
- **Own projects that look finished**: a screenshot or GIF, a one-line pitch, a quickstart, a licence, CI, releases. Visitors click through from the profile, so the repo's README is part of the profile.
- **Numbers that are real and sourced**: users, downloads, stars, performance gains, uptime. Only if the user can back them.
- **Writing and talks**: a post explaining a hard bug or a design decision signals seniority more than any badge.
- **Depth over breadth**: three deep projects beat twenty tutorial clones.

## 3. The one-line identity

Specific role, plus domain, plus one proof point:
- "Backend engineer building payment infrastructure · contributor to Django and Celery"
- "Mobile + backend engineer (Flutter, Python) · I ship production apps and fix the tools I use"

Put it in the card or at the top of the README, and reuse it in the bio (160 characters) so the sidebar and the page agree.

## 4. Curate what people see first

- **Pins (6 slots)**: the best 4–6 repositories.
  - Upstream projects the person contributed to can be pinned and show their real stars.
  - Unchanged forks show 0 stars and look like copying.
- **Own public repos**: a description and topics on every one people might open; a licence and a README on the ones worth showing.
- **Weak repos**: tutorials and experiments can be archived, or made private. That is the user's decision, never done silently.
- **Old forks**: forks with open PRs must stay. Forks with nothing in them can be deleted, again only if the user wants.
- **Sidebar**: bio, location or timezone, website, social links. A real photo or a consistent avatar.
- **"Private contributions" toggle**: turn it on if the day job is private work and the user wants the graph to reflect it (content.md).

## 5. Page techniques that read as senior

- **Lead with the strongest proof**: hero, then the identity line, then 2–4 proof items, then projects. Keep the first screen scannable.
- **Show impact, not a tech list**: "cut cold-start time 40%" beats "React, Node, Docker, AWS…". A few evidence-backed languages beat a wall of 30 logos (scan_languages.py).
- **A current line**: "Now: building X · Open to: backend roles / OSS collaboration". This tells a recruiter what to do next.
- **A calm, consistent style**: one palette, few widgets, working links, both themes checked. A broken image or a rate-limited stats card looks careless.
- **Keep it up to date**: an auto-refreshing card or a "latest posts" feed, plus pins that match what they do now.

## 6. What to refuse, and why it backfires

| Tactic | Why not |
|---|---|
| Backdated or scripted commits to fill the contribution graph | Anyone who clicks a day sees empty commits. It reads as deception and ends trust at once |
| Buying stars or followers, follow-for-follow rings | Easy to spot (star history spikes, empty accounts) and against GitHub's terms |
| Presenting trivial PRs (typos, whitespace) as major contributions | Maintainers and recruiters open the PR. Describe it honestly or leave it out |
| Skill or logo walls without evidence | Invites questions the person can't answer in an interview |
| Trophy or rank cards and view counters as "credentials" | Decorative at best, easy to game, and they often break |
| Copying someone else's README text or projects | Plagiarism is obvious to anyone who has seen the original |

If the user asks for one of these, say briefly why it hurts them, then offer the honest version that gets the same effect. For example: instead of a painted graph, make real contributions visible; instead of inflated claims, describe the actual change well.

## 7. A quick audit routine

1. Run `scripts/audit_profile.py LOGIN`; fix its high-priority items, or list them for the user to do in the web UI.
2. Pick the 2–4 strongest proof items it reports, and confirm with the user which they are proud of.
3. Write the identity line; align the bio and pins with it.
4. Build the page (the other paths), preview light, dark and phone widths, then iterate.
