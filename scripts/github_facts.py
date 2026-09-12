#!/usr/bin/env python3
"""Everything a profile brief needs to know about a GitHub user, as JSON.

  python3 github_facts.py LOGIN [--private] > facts.json

Uses the logged-in `gh` CLI. Public facts are listed in full. Private
repositories and pull requests into private repositories are reduced to
counts unless --private is given, and even then every entry is marked private:
they are for the conversation with the owner, never for the published page.
"""
import argparse
import json
import subprocess
from collections import Counter

QUERY = """
query($login: String!, $prq: String!) {
  user(login: $login) {
    login name bio company location websiteUrl twitterUsername createdAt
    followers { totalCount } following { totalCount }
    pinnedItems(first: 6) { nodes { ... on Repository { nameWithOwner stargazerCount isFork } } }
    repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        name isPrivate isFork stargazerCount forkCount description homepageUrl updatedAt
        primaryLanguage { name }
        repositoryTopics(first: 8) { nodes { topic { name } } }
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
    repositoriesContributedTo(first: 100, contributionTypes: [COMMIT, PULL_REQUEST], includeUserRepositories: false) {
      totalCount nodes { nameWithOwner isPrivate stargazerCount }
    }
    contributionsCollection { contributionCalendar { totalContributions } }
  }
  prs: search(query: $prq, type: ISSUE, first: 100) {
    issueCount
    nodes { ... on PullRequest { title url state merged createdAt repository { nameWithOwner isPrivate stargazerCount } } }
  }
}"""


def summarize(d, include_private=False):
    u, prs = d["user"], d["prs"]
    show = lambda private: include_private or not private
    mark = lambda private, row: {**row, "private": True} if private else row
    repos = u["repositories"]["nodes"]
    own = [r for r in repos if not r["isFork"]]
    lang_bytes = Counter()
    for r in own:
        if show(r["isPrivate"]):
            for e in r["languages"]["edges"]:
                lang_bytes[e["node"]["name"]] += e["size"]
    pr_rows = [p for p in prs["nodes"] if p]
    public_prs = [p for p in pr_rows if show(p["repository"]["isPrivate"])]
    pr = lambda p: mark(p["repository"]["isPrivate"], {"repo": p["repository"]["nameWithOwner"], "title": p["title"],
                                                        "url": p["url"], "stars": p["repository"]["stargazerCount"]})
    return {
        "profile": {k: u[k] for k in ("login", "name", "bio", "company", "location", "websiteUrl", "twitterUsername", "createdAt")}
                   | {"followers": u["followers"]["totalCount"], "following": u["following"]["totalCount"]},
        "pinned": [{"repo": n["nameWithOwner"], "stars": n["stargazerCount"], "fork": n["isFork"]} for n in u["pinnedItems"]["nodes"] if n],
        "own_repos": [mark(r["isPrivate"], {
            "name": r["name"], "stars": r["stargazerCount"], "forks": r["forkCount"], "description": r["description"],
            "language": (r["primaryLanguage"] or {}).get("name"), "homepage": r["homepageUrl"], "updated": r["updatedAt"][:10],
            "topics": [t["topic"]["name"] for t in r["repositoryTopics"]["nodes"]]}) for r in own if show(r["isPrivate"])],
        "own_private_repo_count": sum(r["isPrivate"] for r in own),
        "forks": [r["name"] for r in repos if r["isFork"] and show(r["isPrivate"])],
        "languages_by_bytes": dict(lang_bytes.most_common()),
        "contributed_to": [mark(n["isPrivate"], {"repo": n["nameWithOwner"], "stars": n["stargazerCount"]})
                           for n in u["repositoriesContributedTo"]["nodes"] if show(n["isPrivate"])],
        "pull_requests_to_others": {
            "merged": [pr(p) for p in public_prs if p["merged"]],
            "open": [pr(p) for p in public_prs if p["state"] == "OPEN"],
            "closed_unmerged": sum(1 for p in public_prs if p["state"] == "CLOSED" and not p["merged"]),
            "in_private_repos": sum(p["repository"]["isPrivate"] for p in pr_rows),
        },
        "contributions_last_year": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "truncated": {"repos": u["repositories"]["totalCount"] > 100, "prs": prs["issueCount"] > 100},
    }


def selfcheck():
    repo = lambda name, private: {"name": name, "isPrivate": private, "isFork": False, "stargazerCount": 0, "forkCount": 0,
                                  "description": None, "homepageUrl": None, "updatedAt": "2026-01-01T00:00:00Z",
                                  "primaryLanguage": None, "repositoryTopics": {"nodes": []},
                                  "languages": {"edges": [{"size": 10, "node": {"name": "Go"}}]}}
    d = {"user": {"login": "x", "name": None, "bio": None, "company": None, "location": None, "websiteUrl": None,
                  "twitterUsername": None, "createdAt": "2020", "followers": {"totalCount": 0}, "following": {"totalCount": 0},
                  "pinnedItems": {"nodes": []}, "repositories": {"totalCount": 2, "nodes": [repo("pub", False), repo("secret", True)]},
                  "repositoriesContributedTo": {"totalCount": 0, "nodes": []},
                  "contributionsCollection": {"contributionCalendar": {"totalContributions": 0}}},
         "prs": {"issueCount": 0, "nodes": []}}
    s = summarize(d)
    assert [r["name"] for r in s["own_repos"]] == ["pub"] and s["own_private_repo_count"] == 1, "private names hidden"
    assert "secret" not in json.dumps(s)
    assert summarize(d, include_private=True)["own_repos"][1] == {**summarize(d, True)["own_repos"][1], "private": True}


if __name__ == "__main__":
    selfcheck()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("login")
    ap.add_argument("--private", action="store_true", help="list private repos/PRs too (marked private)")
    a = ap.parse_args()
    raw = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={a.login}",
                          "-f", f"prq=author:{a.login} is:pr -user:{a.login}"], capture_output=True, text=True, check=True).stdout
    print(json.dumps(summarize(json.loads(raw)["data"], a.private), ensure_ascii=False, indent=2))
