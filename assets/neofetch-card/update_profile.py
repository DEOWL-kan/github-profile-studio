#!/usr/bin/env python3
"""Render the profile card: dark_mode.svg and light_mode.svg.

A terminal window. Left: an ASCII portrait read from art.txt (plus
art_colors.json), which make_art.py bakes once from a picture. Right: a
neofetch-style panel with live GitHub stats. Who it is about comes from
card.json. Stdlib only, so the daily Action needs no install step.
"""
import calendar
import html
import json
import os
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent

# Everything about the person lives in card.json next to this file, so the code
# never needs editing per person. Missing keys fall back to placeholders.
CONFIG = json.loads((HERE / "card.json").read_text(encoding="utf-8")) if (HERE / "card.json").exists() else {}
# GitHub's language colours (linguist) for the languages people list most.
LINGUIST = {
    "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A", "Java": "#B07219", "Kotlin": "#A97BFF",
    "Dart": "#00B4AB", "Swift": "#F05138", "Go": "#00ADD8", "Rust": "#DEA584", "C": "#555555", "C++": "#F34B7D",
    "C#": "#178600", "Ruby": "#701516", "PHP": "#4F5D95", "Shell": "#89E051", "HTML": "#E34C26", "CSS": "#663399",
    "Vue": "#41B883", "SQL": "#E38C00", "Objective-C": "#438EFF", "Lua": "#000080", "Scala": "#C22D40",
    "R": "#198CE7", "Haskell": "#5E5086", "Elixir": "#6E4A7E", "Zig": "#EC915C", "Svelte": "#FF3E00",
}
USER = CONFIG.get("login", "your-login")
NAME = CONFIG.get("name", "Your Name")
ROLE = CONFIG.get("role", "Developer")
JOINED = date.fromisoformat(CONFIG.get("joined", "2020-01-01")[:10])  # account creation; Uptime counts from here
# Panel rows as [key, value]; a null Uptime value is computed from JOINED.
ROWS = [tuple(r) for r in CONFIG.get("rows", [["Uptime", None], ["Speaks", "English"]])]
LANGS = [(name, LINGUIST.get(name, "#8b949e")) for name in CONFIG.get("langs", ["Python", "TypeScript"])]
# Eight swatches under the stats; pick them from the portrait's own tones.
# Whether Commits includes private work (as an anonymous count) is the person's
# call, asked in the brief. Off: only commits in public repositories are counted.
PRIVATE_CONTRIBUTIONS = bool(CONFIG.get("private_contributions", False))
SWATCHES = CONFIG.get("swatches", ["#0f3d3e", "#1f6f6f", "#2fa39b", "#7fd3c7", "#f3d3b0", "#e8a878", "#c7743f", "#7a3b1f"])

CARD_W, CARD_H, BAR_H = 920, 540, 34
BACKDROP_W = 442  # the portrait's backdrop runs edge to edge, left of the panel
# A dark solid behind the portrait in both themes, and the portrait's default ink.
BACKDROP, INK = CONFIG.get("backdrop", "#161b2e"), "#8b949e"
ART_BOX = (20, BAR_H + 16, 410, CARD_H - BAR_H - 32)  # x, y, width, height for the portrait
PX = 462  # panel left edge
PANEL_W = CARD_W - PX - 24
# Glyph cell of the portrait, in em. make_art.py sizes its grid with the same
# numbers, so the picture keeps its proportions.
CHAR_W, LINE_H = 0.6, 1.0
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

PALETTES = {
    "dark": {"bg": "#0d1117", "bar": "#161b22", "border": "#30363d", "text": "#e6edf3",
             "muted": "#7d8590", "key": "#f0a868", "accent": "#3fc1b7", "pill": "#161b22",},
    "light": {"bg": "#ffffff", "bar": "#f6f8fa", "border": "#d0d7de", "text": "#1f2328",
              "muted": "#656d76", "key": "#b45309", "accent": "#0f766e", "pill": "#f6f8fa",},
}

# Only the prompt cursor moves. Its first frame is the finished card, so a
# screenshot or a renderer that skips animation never shows a blank panel.
STYLE = """<style>
.c{animation:c 1.1s steps(1) infinite}
@keyframes c{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.c{animation:none}}
</style>"""


def add_months(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    y += d.year
    return date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def uptime(start, end):
    months = (end.year - start.year) * 12 + end.month - start.month
    if add_months(start, months) > end:
        months -= 1
    return months // 12, months % 12, (end - add_months(start, months)).days


def graphql(query, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {token}", "User-Agent": USER},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch_stats(token):
    # Public data only, so the Actions token and a personal token agree.
    years = " ".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z")'
        " { totalCommitContributions restrictedContributionsCount"
        " commitContributionsByRepository(maxRepositories: 100) { repository { isPrivate } contributions { totalCount } } }"
        for y in range(JOINED.year, datetime.now(timezone.utc).year + 1)
    )
    u = graphql(f"""{{
      user(login: "{USER}") {{
        followers {{ totalCount }}
        repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {{ totalCount }}
        repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST], privacy: PUBLIC) {{ totalCount }}
        {years}
      }}
    }}""", token)["user"]
    return {
        "Repos": u["repositories"]["totalCount"],
        "Commits": count_commits([v for k, v in u.items() if k.startswith("y")], PRIVATE_CONTRIBUTIONS),
        "Contributed": u["repositoriesContributedTo"]["totalCount"],
        "Followers": u["followers"]["totalCount"],
    }


def count_commits(years, private):
    """Commits across yearly contribution collections.

    With private work, add the anonymous count the public sees for it. Without,
    sum only public repositories: a personal token would otherwise count the
    owner's private commits in totalCommitContributions.

    That sum stops at maxRepositories: 100, the API's ceiling for the list, so
    a year spread over more public repositories than that is undercounted. The
    year's total cannot stand in for it: a token that reads some of this
    person's private work would fold those commits into a public number as soon
    as the private repository falls outside the truncated list.
    """
    if private:
        return sum(y["totalCommitContributions"] + y["restrictedContributionsCount"] for y in years)
    return sum(c["contributions"]["totalCount"] for y in years
               for c in y["commitContributionsByRepository"] if not c["repository"]["isPrivate"])


def runs(row, crow, default):
    """One tspan per run of equal colour; a space takes any colour, so it never splits a run."""
    out, cur, buf = [], None, ""
    for i, ch in enumerate(row):
        c = (crow[i] if crow and i < len(crow) else None) or default
        if ch == " " and buf:
            c = cur
        if c != cur and buf:
            out.append(f'<tspan fill="{cur}">{html.escape(buf)}</tspan>')
            buf = ""
        cur, buf = c, buf + ch
    if buf:
        out.append(f'<tspan fill="{cur}">{html.escape(buf)}</tspan>')
    return "".join(out)


def load_art():
    rows = (HERE / "art.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    path = HERE / "art_colors.json"
    return rows, json.loads(path.read_text()) if path.exists() else None


def portrait(rows, colors):
    """The ASCII portrait, coloured for its dark backdrop in both themes."""
    cols = max(map(len, rows))
    x0, y0, bw, bh = ART_BOX
    fs = min(bw / (cols * CHAR_W), bh / (len(rows) * LINE_H))
    cw, lh = CHAR_W * fs, LINE_H * fs
    ax = x0 + (bw - cols * cw) / 2
    ay = y0 + (bh - len(rows) * lh) / 2
    # Braille dots are thin; bold makes them read as a picture, not a haze.
    bold = ' font-weight="bold"' if any("⠀" <= ch <= "⣿" for r in rows for ch in r) else ""
    out = [f'<g font-family="{MONO}" font-size="{fs:.2f}px"{bold}>']
    # textLength pins every row to the grid width, so a fallback font with a
    # different advance cannot skew the picture.
    for i, row in enumerate(rows):
        crow = colors[i] if colors else None
        out.append(
            f'<text x="{ax:.1f}" y="{ay + (i + 0.8) * lh:.1f}" textLength="{cols * cw:.1f}" '
            f'lengthAdjust="spacing" xml:space="preserve">{runs(row.ljust(cols), crow, INK)}</text>'
        )
    out.append("</g>")
    return out


def panel(mode, stats):
    p = PALETTES[mode]
    e = html.escape
    y, m, d = uptime(JOINED, date.today())
    mono = f'font-family="{MONO}" font-size="13"'
    vx = PX + 86  # value column
    out = [
        f'<text x="{PX}" y="100" {mono}><tspan fill="{p["accent"]}">❯</tspan>'
        f'<tspan fill="{p["text"]}"> neofetch</tspan></text>',
        f'<text x="{PX}" y="146" font-family="{SANS}" font-size="30" font-weight="700" fill="{p["text"]}">'
        f'{e(NAME)}</text>',
        f'<text x="{PX}" y="172" font-family="{SANS}" font-size="14">'
        f'<tspan fill="{p["accent"]}">@{e(USER)}</tspan><tspan fill="{p["muted"]}"> · {e(ROLE)}</tspan></text>',
        f'<rect x="{PX}" y="190" width="{PANEL_W}" height="1.5" fill="url(#rule-{mode})"/>',
    ]
    ry = 222
    for key, val in ROWS:
        text = f"{y} years, {m} months, {d} days" if key == "Uptime" else val
        out.append(f'<text x="{PX}" y="{ry}" {mono} fill="{p["key"]}">{e(key)}</text>'
                   f'<text x="{vx}" y="{ry}" {mono} fill="{p["text"]}">{e(text)}</text>')
        ry += 26
    # Languages wrap as dot-and-name chips inside the value column.
    out.append(f'<text x="{PX}" y="{ry}" {mono} fill="{p["key"]}">Langs</text>')
    x = vx
    for name, colour in LANGS:
        w = 15 + len(name) * 7.8
        if x + w > PX + PANEL_W and x > vx:
            x, ry = vx, ry + 24
        out.append(f'<circle cx="{x + 5:.1f}" cy="{ry - 4.5}" r="4.5" fill="{colour}"/>'
                   f'<text x="{x + 15:.1f}" y="{ry}" {mono} fill="{p["text"]}">{e(name)}</text>')
        x += w + 14
    gap, top = 10, ry + 30
    pw = (PANEL_W - 3 * gap) / 4
    for i, label in enumerate(["Repos", "Commits", "Contributed", "Followers"]):
        x = PX + i * (pw + gap)
        value = f"{stats[label]:,}" if stats else "—"
        out.append(
            f'<rect x="{x:.1f}" y="{top}" width="{pw:.1f}" height="54" rx="8" fill="{p["pill"]}" stroke="{p["border"]}"/>'
            f'<text x="{x + pw / 2:.1f}" y="{top + 25}" text-anchor="middle" font-family="{SANS}" font-size="19" '
            f'font-weight="700" fill="{p["text"]}">{value}</text>'
            f'<text x="{x + pw / 2:.1f}" y="{top + 43}" text-anchor="middle" font-family="{SANS}" font-size="11" '
            f'letter-spacing="0.5" fill="{p["muted"]}">{label.upper()}</text>'
        )
    out.append("".join(f'<rect x="{PX + i * 30}" y="{top + 80}" width="26" height="12" rx="3" fill="{c}"/>'
                       for i, c in enumerate(SWATCHES)))
    out.append(f'<text x="{PX}" y="{top + 128}" {mono} fill="{p["accent"]}">❯</text>'
               f'<rect class="c" x="{PX + 14}" y="{top + 117}" width="8" height="15" fill="{p["text"]}"/>')
    return out


def render(mode, rows, colors, stats):
    p = PALETTES[mode]
    title = f"{USER.lower()}@github: ~"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}">',
        STYLE,
        f'<defs><clipPath id="card-{mode}"><rect width="{CARD_W}" height="{CARD_H}" rx="12"/></clipPath>'
        f'<linearGradient id="rule-{mode}" x1="0" x2="1"><stop offset="0" stop-color="{p["accent"]}"/>'
        f'<stop offset="0.6" stop-color="{p["key"]}" stop-opacity="0.5"/>'
        f'<stop offset="1" stop-color="{p["key"]}" stop-opacity="0"/></linearGradient></defs>',
        f'<g clip-path="url(#card-{mode})"><rect width="{CARD_W}" height="{CARD_H}" fill="{p["bg"]}"/>'
        f'<rect width="{CARD_W}" height="{BAR_H}" fill="{p["bar"]}"/>'
        f'<rect y="{BAR_H + 1}" width="{BACKDROP_W}" height="{CARD_H - BAR_H - 1}" fill="{BACKDROP}"/>'
        f'<rect y="{BAR_H}" width="{CARD_W}" height="1" fill="{p["border"]}"/></g>',
        "".join(f'<circle cx="{22 + i * 20}" cy="{BAR_H / 2}" r="6" fill="{c}"/>'
                for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"])),
        f'<text x="{CARD_W / 2}" y="{BAR_H / 2 + 4.5}" text-anchor="middle" font-family="{SANS}" font-size="13" '
        f'fill="{p["muted"]}">{html.escape(title)}</text>',
        f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="12" fill="none" stroke="{p["border"]}"/>',
    ]
    return "\n".join(out + portrait(rows, colors) + panel(mode, stats) + ["</svg>"])


def selfcheck():
    assert uptime(date(2023, 12, 28), date(2026, 9, 11)) == (2, 8, 14)
    assert uptime(date(2025, 1, 31), date(2025, 3, 1)) == (0, 1, 1)
    assert uptime(date(2024, 2, 29), date(2025, 2, 28)) == (1, 0, 0)  # Feb 29 clamps to Feb 28
    assert runs("ab  c", ["#111", "#111", None, "#222", "#222"], "#999") == \
        '<tspan fill="#111">ab  </tspan><tspan fill="#222">c</tspan>'
    year = {"totalCommitContributions": 10, "restrictedContributionsCount": 5, "commitContributionsByRepository": [
        {"repository": {"isPrivate": False}, "contributions": {"totalCount": 3}},
        {"repository": {"isPrivate": True}, "contributions": {"totalCount": 7}}]}
    assert count_commits([year], private=False) == 3 and count_commits([year], private=True) == 15
    svg = render("dark", ["@@"], None, None)
    assert svg.count("<svg") == 1 and "—" in svg and "Merged" not in svg and "IDE" not in svg and f'fill="{BACKDROP}"' in svg


if __name__ == "__main__":
    selfcheck()
    token = os.environ.get("GITHUB_TOKEN", "")
    stats = fetch_stats(token) if token else None
    print("stats:", stats)
    rows, colors = load_art()
    for mode in PALETTES:
        (HERE / f"{mode}_mode.svg").write_text(render(mode, rows, colors, stats), encoding="utf-8")
    print("wrote dark_mode.svg, light_mode.svg")
