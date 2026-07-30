# context-research

A Claude Code plugin that turns a fuzzy content niche into a data-backed
research brief. Point it at a topic — a product, an audience, a question —
and it pulls what's actually winning right now on Reddit, YouTube, TikTok,
and Instagram Reels, ranks it by real engagement, and mines the top
performers for hooks, pain points, desires, objections, and the exact
language your audience uses. The output is a self-contained HTML dashboard
plus a per-hook "here's a concrete way to use this" idea, so you walk away
with something to make next, not just a pile of data.

The core design principle: **code fetches and ranks deterministically,
Claude does the creative mining.** Nothing in the brief is fabricated —
every hook, quote, and idea traces back to a specific ranked item from the
live data.

## Layout

- **`scroll-stoppers/`** — the plugin itself: a Claude Code skill plus the
  Python engine behind it (platform fetchers, ranking, dashboard renderer).
  This directory is portable — see
  [`scroll-stoppers/README.md`](./scroll-stoppers/README.md) for the full
  pipeline explanation and how to install/run it in another project.
- **`output/`** — where a run's results land: ranked data, the mined brief,
  and the rendered dashboard. **This directory is not part of the repo** —
  it's gitignored and won't exist on a fresh clone. It's created locally the
  first time you run the plugin against a niche (see the scroll-stoppers
  README's "Running the engine directly" section) and is fully
  regenerable, so there's nothing to restore or set up by hand.

## Getting started

See [`scroll-stoppers/README.md`](./scroll-stoppers/README.md) for setup
(Apify token), usage examples, and running the engine directly for
debugging.
