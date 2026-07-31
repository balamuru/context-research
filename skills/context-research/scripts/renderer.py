#!/usr/bin/env python3
"""
Renders a mined content brief (written by Claude per SKILL.md) into a
single self-contained HTML dashboard: inline CSS, zero external
dependencies, opens in any browser.

Expected input JSON shape (the "mined brief"):
{
  "niche": str,
  "generated_at": str,
  "hooks":       [{"text": str, "platform": str, "url": str, "author": str}],
  "pains":       [{"quote": str, "platforms": [str], "urls": [str]}],
  "desires":     [{"text": str, "platform": str, "url": str}],
  "objections":  [{"text": str, "platform": str, "url": str}],
  "formats":     [{"name": str, "description": str, "examples": [str]}],
  "phrases":     [str],
  "make_next":   [{"title": str, "rationale": str, "format": str, "hook_to_use": str}]
}

Usage:
    python3 renderer.py --brief /tmp/brief.json --out /tmp/dashboard.html
"""

from __future__ import annotations

import argparse
import html
import json
import sys

PLATFORM_COLORS = {
    "reddit": "#FF4500",
    "youtube": "#FF0000",
    "tiktok": "#00F2EA",
    "instagram": "#C13584",
}

CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  margin: 0; padding: 2rem; max-width: 1100px; margin-inline: auto;
  background: #0d0f14; color: #e8e8ec;
  line-height: 1.5;
}
@media (prefers-color-scheme: light) {
  body { background: #f7f7f9; color: #1a1a1f; }
}
h1 { font-size: 1.8rem; margin-bottom: 0.2rem; }
.subtitle { color: #9a9aa5; margin-bottom: 2rem; }
h2 { font-size: 1.2rem; margin-top: 2.5rem; border-bottom: 1px solid #333; padding-bottom: 0.4rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; margin-top: 1rem; }
.card {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 1rem; border-left-width: 4px;
}
@media (prefers-color-scheme: light) {
  .card { background: #fff; border: 1px solid #e2e2e6; border-left-width: 4px; }
}
.card a { color: inherit; }
.platform-tag {
  display: inline-block; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
  padding: 0.15rem 0.5rem; border-radius: 999px; margin-bottom: 0.5rem; color: #0d0f14;
}
.quote { font-style: italic; }
.validated { color: #4ade80; font-size: 0.8rem; font-weight: 600; }
.phrase-bank { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }
.phrase {
  background: rgba(255,255,255,0.06); padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.9rem;
}
.make-next-card { border-left-color: #fbbf24; }
.mini-idea {
  margin-top: 0.6rem; padding-top: 0.6rem; border-top: 1px dashed rgba(255,255,255,0.15);
  font-size: 0.85rem; color: #d4d4dc;
}
@media (prefers-color-scheme: light) {
  .mini-idea { border-top: 1px dashed #e2e2e6; color: #444; }
}
.meta { font-size: 0.75rem; color: #9a9aa5; margin-top: 0.5rem; }
"""


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _tag(platform: str) -> str:
    color = PLATFORM_COLORS.get(platform, "#888")
    return f'<span class="platform-tag" style="background:{color}">{_esc(platform)}</span>'


def render_hooks(hooks: list[dict]) -> str:
    cards = []
    for h in hooks:
        mini_idea = h.get("mini_idea", "")
        idea_html = f'<div class="mini-idea">💡 {_esc(mini_idea)}</div>' if mini_idea else ""
        cards.append(
            f'<div class="card" style="border-left-color:{PLATFORM_COLORS.get(h.get("platform",""), "#888")}">'
            f'{_tag(h.get("platform",""))}'
            f'<div>{_esc(h.get("text",""))}</div>'
            f'{idea_html}'
            f'<div class="meta"><a href="{_esc(h.get("url",""))}" target="_blank">{_esc(h.get("author",""))}</a></div>'
            f'</div>'
        )
    return f'<div class="grid">{"".join(cards)}</div>' if cards else "<p>None found.</p>"


def render_pains(pains: list[dict]) -> str:
    cards = []
    for p in pains:
        platforms = p.get("platforms", [])
        validated = len(platforms) > 1
        badge = '<div class="validated">✓ Validated across platforms</div>' if validated else ""
        tags = "".join(_tag(pl) for pl in platforms)
        urls = " · ".join(
            f'<a href="{_esc(u)}" target="_blank">source</a>' for u in p.get("urls", [])
        )
        cards.append(
            f'<div class="card" style="border-left-color:#f87171">'
            f'{tags}<div class="quote">"{_esc(p.get("quote",""))}"</div>'
            f'{badge}<div class="meta">{urls}</div>'
            f'</div>'
        )
    return f'<div class="grid">{"".join(cards)}</div>' if cards else "<p>None found.</p>"


def render_simple_list(items: list[dict], text_key: str) -> str:
    cards = []
    for item in items:
        cards.append(
            f'<div class="card" style="border-left-color:{PLATFORM_COLORS.get(item.get("platform",""), "#888")}">'
            f'{_tag(item.get("platform",""))}'
            f'<div>{_esc(item.get(text_key,""))}</div>'
            f'<div class="meta"><a href="{_esc(item.get("url",""))}" target="_blank">source</a></div>'
            f'</div>'
        )
    return f'<div class="grid">{"".join(cards)}</div>' if cards else "<p>None found.</p>"


def render_formats(formats: list[dict]) -> str:
    cards = []
    for f in formats:
        examples = " · ".join(
            f'<a href="{_esc(u)}" target="_blank">example</a>' for u in f.get("examples", [])
        )
        cards.append(
            f'<div class="card">'
            f'<strong>{_esc(f.get("name",""))}</strong>'
            f'<div>{_esc(f.get("description",""))}</div>'
            f'<div class="meta">{examples}</div>'
            f'</div>'
        )
    return f'<div class="grid">{"".join(cards)}</div>' if cards else "<p>None found.</p>"


def render_phrases(phrases: list[str]) -> str:
    if not phrases:
        return "<p>None found.</p>"
    spans = "".join(f'<span class="phrase">{_esc(p)}</span>' for p in phrases)
    return f'<div class="phrase-bank">{spans}</div>'


def render_make_next(ideas: list[dict]) -> str:
    cards = []
    for idea in ideas:
        cards.append(
            f'<div class="card make-next-card">'
            f'<strong>{_esc(idea.get("title",""))}</strong>'
            f'<div>{_esc(idea.get("rationale",""))}</div>'
            f'<div class="meta">Format: {_esc(idea.get("format",""))} &middot; '
            f'Hook: "{_esc(idea.get("hook_to_use",""))}"</div>'
            f'</div>'
        )
    return f'<div class="grid">{"".join(cards)}</div>' if cards else "<p>None found.</p>"


def render_dashboard(brief: dict) -> str:
    niche = _esc(brief.get("niche", "Untitled"))
    generated_at = _esc(brief.get("generated_at", ""))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
    <title>Context Research — {niche}</title>
<style>{CSS}</style>
</head>
<body>
    <h1>Context Research: {niche}</h1>
<div class="subtitle">Generated {generated_at}</div>

<h2>Hooks to steal</h2>
{render_hooks(brief.get("hooks", []))}

<h2>Pain points (verbatim)</h2>
{render_pains(brief.get("pains", []))}

<h2>Desires</h2>
{render_simple_list(brief.get("desires", []), "text")}

<h2>Objections</h2>
{render_simple_list(brief.get("objections", []), "text")}

<h2>Winning formats</h2>
{render_formats(brief.get("formats", []))}

<h2>Voice-of-customer phrase bank</h2>
{render_phrases(brief.get("phrases", []))}

<h2>Make this next</h2>
{render_make_next(brief.get("make_next", []))}

</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a mined brief JSON into an HTML dashboard.")
    parser.add_argument("--brief", required=True, help="Path to the mined brief JSON file.")
    parser.add_argument("--out", required=True, help="Path to write the HTML dashboard.")
    args = parser.parse_args()

    with open(args.brief) as f:
        brief = json.load(f)

    html_out = render_dashboard(brief)
    with open(args.out, "w") as f:
        f.write(html_out)

    print(f"Wrote dashboard to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
