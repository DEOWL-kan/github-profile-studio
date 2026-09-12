#!/usr/bin/env python3
"""Which languages has this person actually written?

Walks every git repository under --root, collects the files changed by the
person's own commits, and counts distinct files per language. Only languages
and counts are printed - never repository names or paths, which may be private.

  python3 scan_languages.py [--root ~] [--author PATTERN ...] [--min 15]

Without --author it matches git's global user.email/user.name, the gh login,
its public email and noreply address. Each pattern becomes its own --author
flag, which git ORs together; an alternation regex with an empty part (from an
unset email) makes git fail silently instead.
"""
import argparse
import collections
import json
import os
import subprocess

LANG = {
    "py": "Python", "ts": "TypeScript", "tsx": "TypeScript", "js": "JavaScript", "jsx": "JavaScript",
    "mjs": "JavaScript", "cjs": "JavaScript", "java": "Java", "kt": "Kotlin", "kts": "Kotlin", "dart": "Dart",
    "swift": "Swift", "go": "Go", "rs": "Rust", "c": "C", "cpp": "C++", "cc": "C++", "hpp": "C++", "cs": "C#",
    "rb": "Ruby", "php": "PHP", "m": "Objective-C", "mm": "Objective-C", "vue": "Vue", "svelte": "Svelte",
    "sh": "Shell", "zsh": "Shell", "bash": "Shell", "sql": "SQL", "html": "HTML", "css": "CSS", "scss": "CSS",
    "lua": "Lua", "r": "R", "scala": "Scala", "ps1": "PowerShell",
}
SKIP = {"node_modules", ".venv", "venv", "Pods", "Library", ".Trash", ".cache", ".npm", ".cargo", ".rustup",
        ".gradle", ".m2", ".pub-cache", ".vscode", ".local", "Applications", "site-packages", "build", "dist"}


def lang_of(path):
    name = os.path.basename(path)
    return LANG.get(name.rsplit(".", 1)[-1].lower()) if "." in name else None


def run(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def repos(root, depth=6):
    base = root.rstrip(os.sep).count(os.sep)
    for d, dirs, _ in os.walk(root):
        if ".git" in dirs:
            yield d
        dirs[:] = [x for x in dirs if x not in SKIP and x != ".git" and d.count(os.sep) - base < depth]


def default_authors():
    found = [run("git", "config", "--global", key) for key in ("user.email", "user.name")]
    try:
        u = json.loads(run("gh", "api", "user"))
        found += [u["login"], f'{u["id"]}+{u["login"]}@users.noreply.github.com', u.get("email") or "", u.get("name") or ""]
    except (ValueError, KeyError):
        pass
    return [a for a in dict.fromkeys(found) if a]


def selfcheck():
    assert lang_of("app/lib/main.dart") == "Dart" and lang_of("x/Y.TSX") == "TypeScript"
    assert lang_of("Makefile") is None and lang_of("notes.md") is None


if __name__ == "__main__":
    selfcheck()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.expanduser("~"))
    ap.add_argument("--author", action="append", help="email or name; repeatable")
    ap.add_argument("--min", type=int, default=15, help="files needed to suggest a language")
    a = ap.parse_args()
    authors = a.author or default_authors()
    if not authors:
        raise SystemExit("no author identity found; pass --author EMAIL")
    counts, hit, total = collections.Counter(), 0, 0
    for repo in repos(a.root):
        total += 1
        files = run("git", "-C", repo, "log", "--all", *[f"--author={x}" for x in authors],
                    "--name-only", "--pretty=format:").splitlines()
        langs = [lang_of(f) for f in set(files) if f]
        hit += bool(files)
        counts.update(x for x in langs if x)
    print(f"{total} repos scanned, {hit} with commits by {len(authors)} author pattern(s)")
    for lang, n in counts.most_common():
        print(f"  {lang:12s} {n}")
    print("suggested:", ", ".join(l for l, n in counts.most_common() if n >= a.min) or "(none)")
