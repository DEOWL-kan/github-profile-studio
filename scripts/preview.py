#!/usr/bin/env python3
"""Preview a profile README the way GitHub shows it, in light and dark.

Renders README.md with GitHub's own Markdown API (so HTML filtering matches),
styles it with GitHub's markdown CSS at the profile README width, and
screenshots it with Chrome/Chromium headless at 2x. Theme-aware <picture>
sources and #gh-dark-mode-only / #gh-light-mode-only images are resolved for
each theme explicitly, so the result does not depend on the machine's theme.
Relative images resolve against the profile directory; remote ones load over
the network. Prints the two PNG paths.

  python3 preview.py PROFILE_DIR OUT_DIR [--login LOGIN] [--width 830] [--mobile]

--mobile adds readme-THEME-mobile.png at a phone's width (390 px), worth it
whenever the page relies on one wide image whose text shrinks on phones.
"""
import argparse
import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

CSS_URL = "https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown-{}.min.css"
FALLBACK_CSS = ".markdown-body{font-family:-apple-system,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif;line-height:1.5}" \
               ".markdown-body img{max-width:100%}"
PAGE = {"light": "#ffffff", "dark": "#0d1117"}
MOBILE_W = 390  # iPhone 12-16 logical width; --mobile and the help text share it so they cannot drift


def for_theme(html, theme):
    """Keep only what GitHub would show in this theme."""
    other = "light" if theme == "dark" else "dark"

    def source(m):
        tag = m.group(0)
        if f"prefers-color-scheme: {theme}" in tag or f"prefers-color-scheme:{theme}" in tag:
            return re.sub(r'media="[^"]*"', 'media="all"', tag)
        return "" if "prefers-color-scheme" in tag else tag

    html = re.sub(r"<source\b[^>]*>", source, html)
    return re.sub(rf'<img\b[^>]*#gh-{other}-mode-only[^>]*>', "", html)


def chrome():
    for c in (os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "google-chrome", "chromium", "chromium-browser"):
        if c and (os.path.exists(c) or shutil.which(c)):
            return c
    raise SystemExit("no Chrome/Chromium found; set CHROME=/path/to/chrome")


def selfcheck():
    pic = ('<picture><source media="(prefers-color-scheme: dark)" srcset="d.svg">'
           '<source media="(prefers-color-scheme: light)" srcset="l.svg"><img src="d.svg"></picture>')
    assert 'srcset="d.svg"' in for_theme(pic, "dark") and 'srcset="l.svg"' not in for_theme(pic, "dark")
    assert 'media="all" srcset="l.svg"' in for_theme(pic, "light")
    assert for_theme('<img src="x.png#gh-dark-mode-only">', "light") == ""


if __name__ == "__main__":
    selfcheck()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--login", help="repo context for relative links (default: gh login)")
    ap.add_argument("--width", type=int, default=830, help="README column width on a desktop profile")
    ap.add_argument("--mobile", action="store_true", help=f"also render at a phone's width ({MOBILE_W} px)")
    a = ap.parse_args()
    src, out = Path(a.profile_dir).resolve(), Path(a.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    login = a.login or subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True).stdout.strip()
    md = (src / "README.md").read_text(encoding="utf-8")
    body = subprocess.run(["gh", "api", "markdown", "-f", "mode=gfm", "-f", f"context={login}/{login}", "-f", f"text={md}"],
                          capture_output=True, text=True, check=True).stdout
    browser = chrome()
    sizes = [(a.width, "")] + ([(MOBILE_W, "-mobile")] if a.mobile else [])
    for theme, (width, tag) in ((t, s) for t in ("light", "dark") for s in sizes):
        try:
            css = urllib.request.urlopen(CSS_URL.format(theme), timeout=10).read().decode()
        except OSError:
            css = FALLBACK_CSS
        page = out / f".preview-{theme}{tag}.html"
        page.write_text(
            f'<!doctype html><html><head><meta charset="utf-8"><base href="{src.as_uri()}/">'
            f"<style>{css}body{{margin:0;background:{PAGE[theme]}}}"
            f".markdown-body{{box-sizing:border-box;width:{width + 40}px;padding:20px;background:{PAGE[theme]}}}</style>"
            f'</head><body><article class="markdown-body">{for_theme(body, theme)}</article></body></html>',
            encoding="utf-8")
        png = out / f"readme-{theme}{tag}.png"
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={width + 40},2400",
                        "--force-device-scale-factor=2", "--virtual-time-budget=6000", f"--screenshot={png}", page.as_uri()],
                       capture_output=True)
        page.unlink()
        if shutil.which("magick"):  # drop the empty page below the content
            subprocess.run(["magick", str(png), "-background", PAGE[theme], "-fuzz", "1%", "-trim", "+repage",
                            "-bordercolor", PAGE[theme], "-border", "40", str(png)], capture_output=True)
        print(png)
