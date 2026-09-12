#!/usr/bin/env python3
"""Check a GitHub profile for the signals visitors notice first.

  python3 audit_profile.py LOGIN [--json]

Prints fixes ranked high / medium / low, then the strongest proof the person
already has (merged PRs into popular projects, their best own repos), which is
what a profile should lead with. Public data only, via the logged-in `gh`.
"""
import argparse
import json
import subprocess
from datetime import datetime, timezone

QUERY = """
query($login: String!, $prq: String!) {
  user(login: $login) {
    login name bio websiteUrl location twitterUsername
    socialAccounts(first: 5) { totalCount }
    pinnedItems(first: 6) { nodes { ... on Repository { nameWithOwner isFork description stargazerCount owner { login } } } }
    repositories(first: 50, ownerAffiliations: OWNER, privacy: PUBLIC, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name isFork isArchived isEmpty stargazerCount description pushedAt homepageUrl
        licenseInfo { spdxId }
        repositoryTopics(first: 1) { totalCount }
        readme: object(expression: "HEAD:README.md") { ... on Blob { byteSize } }
      }
    }
    contributionsCollection { contributionCalendar { totalContributions } }
  }
  profile: repository(owner: $login, name: $login) { name }
  prs: search(query: $prq, type: ISSUE, first: 100) {
    nodes { ... on PullRequest { title url merged repository { nameWithOwner stargazerCount isPrivate } } }
  }
}"""


def audit(d, now=None):
    """Return (findings, proof). findings: list of (priority, message)."""
    now = now or datetime.now(timezone.utc)
    u, f = d["user"], []
    add = lambda pri, msg: f.append((pri, msg))
    if not d.get("profile"):
        add("high", f"No profile README: create the public repo {u['login']}/{u['login']} with a README.md")
    if not u["bio"]:
        add("high", "Bio is empty: add a one-line identity (role · focus · one proof point)")
    elif len(u["bio"]) < 25:
        add("medium", f"Bio is very short ({u['bio']!r}): make it say what you build and for whom")
    pins = [p for p in u["pinnedItems"]["nodes"] if p]
    if not pins:
        add("high", "Nothing pinned: pin your best 4-6 repositories")
    for p in pins:
        if p["isFork"]:
            add("high", f"Pinned fork {p['nameWithOwner']} shows 0 stars: pin the upstream project instead, if you contributed")
        elif not p["description"]:
            add("medium", f"Pinned {p['nameWithOwner']} has no description")
    if not u["websiteUrl"]:
        add("low", "No website or blog link in the profile")
    if not u["socialAccounts"]["totalCount"] and not u["twitterUsername"]:
        add("low", "No social accounts linked")
    if not u["location"]:
        add("low", "No location or timezone: helps recruiters and collaborators")
    own = [r for r in u["repositories"]["nodes"] if not r["isFork"] and not r["isArchived"]]
    for r in own:
        gaps = [g for g, missing in (("description", not r["description"]), ("README", not r["readme"]),
                                     ("licence", not r["licenseInfo"]), ("topics", not r["repositoryTopics"]["totalCount"]))
                if missing]
        if r["isEmpty"]:
            add("medium", f"{r['name']} is empty: fill it, archive it or make it private (your call)")
        elif gaps and r["name"] != u["login"]:
            add("medium" if r["stargazerCount"] or not r["readme"] else "low", f"{r['name']}: missing {', '.join(gaps)}")
    forks = [r["name"] for r in u["repositories"]["nodes"] if r["isFork"]]
    if len(forks) > len(own):
        add("low", f"{len(forks)} forks outnumber {len(own)} own repos in the list: keep forks with open PRs, prune the rest if you like")
    if u["contributionsCollection"]["contributionCalendar"]["totalContributions"] < 50:
        add("medium", "Few public contributions this year: recent visible activity is a strong signal")
    merged = sorted(({"repo": p["repository"]["nameWithOwner"], "stars": p["repository"]["stargazerCount"], "title": p["title"],
                      "url": p["url"]} for p in d["prs"]["nodes"] if p and p["merged"] and not p["repository"]["isPrivate"]),
                    key=lambda p: -p["stars"])
    best_own = sorted(own, key=lambda r: (-r["stargazerCount"], r["pushedAt"]))[:3]
    proof = {"merged_prs_by_upstream_stars": merged[:6],
             "best_own_repos": [{"name": r["name"], "stars": r["stargazerCount"], "description": r["description"]}
                                for r in best_own if r["name"] != u["login"]]}
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(f, key=lambda x: order[x[0]]), proof


def selfcheck():
    repo = lambda name, **kw: {"name": name, "isFork": False, "isArchived": False, "isEmpty": False, "stargazerCount": 0,
                               "description": None, "pushedAt": "2026-01-01", "homepageUrl": None, "licenseInfo": None,
                               "repositoryTopics": {"totalCount": 0}, "readme": None, **kw}
    d = {"user": {"login": "x", "name": None, "bio": "", "websiteUrl": None, "location": None, "twitterUsername": None,
                  "socialAccounts": {"totalCount": 0},
                  "pinnedItems": {"nodes": [{"nameWithOwner": "x/fork", "isFork": True, "description": "d", "stargazerCount": 0,
                                             "owner": {"login": "x"}}]},
                  "repositories": {"nodes": [repo("app", readme={"byteSize": 10})]},
                  "contributionsCollection": {"contributionCalendar": {"totalContributions": 3}}},
         "profile": None,
         "prs": {"nodes": [{"title": "t", "url": "u", "merged": True, "repository": {"nameWithOwner": "big/proj", "stargazerCount": 9000, "isPrivate": False}},
                           {"title": "s", "url": "v", "merged": True, "repository": {"nameWithOwner": "corp/secret", "stargazerCount": 0, "isPrivate": True}}]}}
    findings, proof = audit(d)
    text = " ".join(m for _, m in findings)
    assert findings[0][0] == "high" and "profile README" in text and "Pinned fork" in text and "Bio is empty" in text
    assert "app: missing description, licence, topics" in text
    assert [p["repo"] for p in proof["merged_prs_by_upstream_stars"]] == ["big/proj"], "private PRs never become proof"


if __name__ == "__main__":
    selfcheck()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("login")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    raw = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={a.login}",
                          "-f", f"prq=author:{a.login} is:pr is:merged -user:{a.login}"], capture_output=True, text=True, check=True).stdout
    findings, proof = audit(json.loads(raw)["data"])
    if a.json:
        print(json.dumps({"findings": findings, "proof": proof}, ensure_ascii=False, indent=2))
    else:
        print(f"== {a.login}: {len(findings)} things to improve")
        for pri, msg in findings:
            print(f"  [{pri:6s}] {msg}")
        print("\n== strongest proof to lead with")
        for p in proof["merged_prs_by_upstream_stars"]:
            print(f"  merged into {p['repo']} ({p['stars']:,}★): {p['title']}")
        for r in proof["best_own_repos"]:
            print(f"  own repo {r['name']} ({r['stars']}★): {r['description'] or '(no description)'}")
