# Scroll Stoppers

A Claude Code plugin that turns a fuzzy niche into a content research brief.
Give it a topic, and it pulls what's winning right now on Reddit, YouTube,
TikTok, and Instagram Reels — ranked by real engagement — then mines the
winners for hooks, pain points, desires, objections, winning formats, and
exact customer language. The output is a self-contained HTML dashboard
telling you what to make next.

Code does the fetching and ranking (cheap, deterministic). Claude does the
mining (hooks, pains, creative judgment). Never fabricated — every hook,
quote, and idea in the brief traces back to a specific item in the data.

## How it works

```
Resolve → Fan out → Rank → Mine → Brief
```

1. **Resolve** — Claude turns your fuzzy niche into real targets: subreddits,
   search terms, and specific Instagram creator handles (never hashtags —
   hashtag-based Instagram scraping returns low-engagement spam).
2. **Fan out** — `scroll_stoppers.py` fetches from all four platforms in
   parallel-ish sequence via `sources.py`.
3. **Rank** — `analyze.py` puts engagement on a comparable log scale across
   platforms and ranks by engagement first, recency second.
4. **Mine** — Claude reads the ranked data as a creative strategist and
   extracts hooks, pains, desires, objections, formats, and
   voice-of-customer phrases, flagging anything validated across 2+
   platforms.
5. **Brief** — `render.py` turns the mined brief into a shareable,
   self-contained HTML dashboard.

## Structure

```
scroll-stoppers/
├── .claude-plugin/
│   └── plugin.json          # plugin manifest
└── skills/
    └── scroll-stoppers/
        ├── SKILL.md          # the workflow + mining rules Claude follows
        └── scripts/
            ├── sources.py         # 4 platform fetchers
            ├── analyze.py         # normalize + rank
            ├── scroll_stoppers.py # orchestrator CLI
            └── render.py          # HTML dashboard renderer
```

## Requirements

- **Claude Code**
- **An Apify account + API token** (free tier is enough to start) — runs the
  YouTube, TikTok, and Instagram scrapers
- Python 3 with the `requests` package installed

Reddit needs no key — it uses the free public JSON API. Note: some
datacenter/cloud IPs get blocked (`403`) by Reddit's endpoint; this works
reliably from a normal residential/office connection.

## Setup

```bash
export APIFY_API_TOKEN="your-apify-token-here"
```

Install the plugin in Claude Code, then just chat naturally:

> find scroll stoppers for cold plunge tubs

> what should I make about magnesium for sleep?

> research the glass skin niche for content angles

Claude resolves the niche into real targets, runs the engine (a couple of
minutes), mines the data, and hands you back the dashboard path plus a
summary of the top findings.

## Running the engine directly

For debugging or a dry run without going through Claude:

```bash
cd skills/scroll-stoppers/scripts

python3 scroll_stoppers.py \
  --niche "cold plunge tubs" \
  --subreddits coldplunge biohackers \
  --search-terms "cold plunge" "ice bath" \
  --creator-handles coldplungeguy icebathqueen \
  --relevance-keywords "cold plunge" "ice bath" \
  --out /tmp/ranked.json

python3 render.py --brief /tmp/brief.json --out /tmp/dashboard.html
```

`scroll_stoppers.py` writes ranked, normalized data only — it does no
content interpretation. The mined `brief.json` (hooks/pains/desires/etc.) is
Claude's output per `SKILL.md`'s schema, which `render.py` then turns into
the dashboard.

## Cost

All three paid platforms use pay-per-result Apify pricing. At current
defaults (30 YouTube videos/term, 30 TikToks/term, 18 reels/creator), a
typical niche run costs roughly **$0.50-0.65** in Apify credits — comfortably
inside the platform's monthly free credit for a dozen or more runs.

## Packaging as a shareable plugin

```bash
claude plugin validate .
```

Then zip the directory to share or install elsewhere. All script paths use
`${CLAUDE_PLUGIN_ROOT}` so they resolve correctly after install, regardless
of the user's working directory.

## License

MIT — see [LICENSE](./LICENSE).
