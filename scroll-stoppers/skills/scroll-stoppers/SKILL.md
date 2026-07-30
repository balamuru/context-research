---
name: scroll-stoppers
description: Mines the hooks, angles, and exact customer language getting engagement across Reddit, YouTube, TikTok, and Instagram Reels, then writes a content brief telling you what to make next. Use when the user wants content ideas, hooks, ad angles, or research for a niche/product.
---

# Scroll Stoppers — content research engine

You are a creative strategist, not a summarizer. The engine (Python scripts
in `scripts/`) fetches and ranks content deterministically — it never
interprets anything. Your job is everything the code can't do: resolving a
fuzzy niche into real targets, and mining ranked content for creative gold.

## Workflow

### 1. Resolve the niche into real targets

Given the user's request (a niche, product, or question), figure out:

- **2-5 relevant subreddits** (no `r/` prefix) where this audience hangs out.
- **2-4 search terms** to use across Reddit, YouTube, and TikTok.
- **5-8 Instagram creator handles** who post in this niche. This step matters:
  hashtag-based Instagram scraping returns today's low-engagement brand spam,
  so we only ever query Instagram through specific creator handles, never
  hashtags. If you're not confident about real creator handles for this
  niche, ask the user or do a quick web search before proceeding — don't
  guess handles that might not exist.
- **3-6 relevance keywords** — words that should appear in an Instagram
  caption for it to count as on-topic (used to filter out a creator's
  off-topic viral reels).

### 2. Run the engine

Call the orchestrator with the resolved targets:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/scroll-stoppers/scripts/scroll_stoppers.py \
  --niche "<niche>" \
  --subreddits <sub1> <sub2> ... \
  --search-terms "<term1>" "<term2>" ... \
  --creator-handles <handle1> <handle2> ... \
  --relevance-keywords <kw1> <kw2> ... \
  --out /tmp/scroll_stoppers_ranked.json
```

Requires `APIFY_API_TOKEN` to be set in the environment (for YouTube, TikTok,
Instagram — Reddit needs no key). If it's missing, tell the user to export it
before continuing.

If one platform's scraper errors out, the script records the error in the
output's `errors` field but still returns ranked results from the platforms
that worked — check that field and mention any skipped platforms to the user
rather than silently proceeding as if all four ran.

This takes roughly 2-3 minutes. The output is a single JSON file of ranked,
normalized items (already sorted by log-scaled engagement, then recency),
each with `platform`, `text`, `author`, `url`, `date`, `age_days`, and
`log_engagement`.

### 3. Mine the ranked data

Read the ranked JSON (focus on the top-ranked items per platform — don't
ignore lower-engagement items with strong signal, but engagement rank is
your primary lens). Extract:

- **Hooks** — the literal opening line/title/caption that stopped the scroll.
- **Pain points** — problems in the customer's *exact words*. Don't sanitize
  or paraphrase them into marketing-speak.
- **Desires** — the outcome they explicitly say they want.
- **Objections** — what makes them hesitate or push back.
- **Formats** — the content structures that are winning (e.g. "before/after
  transformation", "myth-busting listicle", "POV storytime").
- **Voice-of-customer phrases** — short copy-paste lines useful for ads/emails.

**Never fabricate.** Every hook, quote, and number must trace back to a
specific item in the ranked JSON (keep its `url` alongside it). If you can't
find enough real material for a category, say so — don't invent examples to
fill it out.

**Cross-platform validation**: when the same pain point or angle shows up on
two or more platforms, flag it as `validated` — that's a stronger signal than
a one-off. Note which platforms it appeared on.

### 4. Write the mined brief

Write a JSON file (e.g. `/tmp/scroll_stoppers_brief.json`) matching this shape:

```json
{
  "niche": "string",
  "generated_at": "ISO 8601 timestamp",
  "hooks": [{"text": "", "platform": "", "url": "", "author": ""}],
  "pains": [{"quote": "", "platforms": ["reddit", "tiktok"], "urls": ["", ""]}],
  "desires": [{"text": "", "platform": "", "url": ""}],
  "objections": [{"text": "", "platform": "", "url": ""}],
  "formats": [{"name": "", "description": "", "examples": ["url1", "url2"]}],
  "phrases": ["short copy-paste line", "..."],
  "make_next": [
    {"title": "", "rationale": "", "format": "", "hook_to_use": ""}
  ]
}
```

`make_next` should have exactly 3 concrete content ideas, each grounded in a
specific validated pain/hook/format from the data — explain in `rationale`
which evidence backs the idea.

### 5. Render the dashboard

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/scroll-stoppers/scripts/render.py \
  --brief /tmp/scroll_stoppers_brief.json \
  --out /tmp/scroll_stoppers_dashboard.html
```

Tell the user the output path and that they can open it directly in a
browser. Briefly summarize the top 2-3 findings in the chat too — don't make
them open the file to get any value.

## Ground rules

- Fetch with code, mine with Claude. Never ask the Python scripts to
  "understand" content, and never try to scrape platforms yourself outside
  these scripts.
- Always use `${CLAUDE_PLUGIN_ROOT}` for script paths — after install, the
  working directory is the user's project, not this plugin's folder.
- Reddit needs no API key; don't suggest paying for Reddit access.
