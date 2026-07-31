# Stop Guessing What Goes Viral: Building a Data-Backed Social Mining Engine with Claude Code

*How combining deterministic Python scripts with AI creative intelligence turns raw engagement metrics across Reddit, YouTube, TikTok, and Instagram into actionable content briefs. Source code available on [GitHub](https://github.com/balamuru/context-research).*

---

Every creator, marketer, and founder knows the feeling: you need content ideas, so you open TikTok or Instagram Reels and start "researching." Two hours later, you've fallen down a rabbit hole of viral clips, saved three random videos, and gained zero structured insights into *why* certain topics work or *what* your target audience actually cares about.

Manual content research is broken. It's biased by algorithm recommendations, impossible to quantify across different platforms, and deeply exhausting.

To solve this, I built **Scroll Stoppers** — a Claude Code plugin and Python engine designed to automate niche content research. 

Here is how it works under the hood, why we chose a hybrid deterministic-AI architecture, and how you can build similar tools for your workflow.

---

## The Core Philosophy: Code Fetches & Ranks, LLMs Mine & Strategize

When building AI-powered tools, the most common trap is asking the LLM to do everything — including things software primitives are already great at.

Asking an LLM to scrape web pages, calculate engagement metrics, or compare raw numbers across platforms leads to hallucinated data, high costs, and unreliable output. On the flip side, pure code can fetch numbers all day, but it will never understand *human emotion* — why a specific opening phrase stopped someone from scrolling, or why a customer pain point hits a nerve.

**Scroll Stoppers** relies on a strict separation of concerns:

1. **Deterministic Python Engine**: Handles API calls, log-scale engagement normalization, and recency sorting. Cheap, fast, and 100% accurate.
2. **Claude Code Creative Intelligence**: Acts as a senior creative strategist. It resolves fuzzy topics into targets, mines the top-ranked content for emotional hooks and customer language, and generates actionable content briefs.

Every hook, pain point, and quote in the final brief links directly back to a live, verified URL from the data. **Zero fabrication.**

---

## How the Pipeline Works

The entire workflow moves through five distinct phases:

```
[Resolve] ➔ [Fan Out] ➔ [Rank] ➔ [Mine] ➔ [Dashboard Brief]
```

### 1. Target Resolution
When a user asks: *"What should I make about magnesium for sleep?"* Claude Code first resolves that fuzzy request into concrete data targets:
- **Subreddits**: `r/supplements`, `r/biohackers`, `r/insomnia`
- **Search Terms**: `"magnesium for sleep"`, `"magnesium glycinate review"`
- **Creator Handles**: Specific trusted creators in the sleep/wellness space (avoiding low-engagement hashtag spam).
- **Relevance Keywords**: Filtering terms to weed out off-topic posts.

### 2. Fan Out (Data Fetching)
The Python engine (`orchestrator.py` and `fetchers.py`) executes multi-platform scraping in parallel. It queries Reddit's free API alongside Apify actors for YouTube Shorts, TikTok, and Instagram Reels.

### 3. Log-Scale Engagement Ranking
Comparing engagement across platforms is notoriously tricky. A TikTok video might easily rack up 500,000 views, whereas a Reddit thread with 1,500 upvotes represents massive community intent.

To solve this, `ranker.py` transforms raw metrics onto a log scale:

$$\text{Log Engagement} = \log_{10}(\text{Engagement} + 1)$$

Items are sorted by `log_engagement` first and `age_days` second. This ensures a viral post from 3 years ago doesn't pass off as a "trending now" topic, while still surfacing high-value evergreen content.

### 4. Creative Mining & Cross-Platform Validation
Once the data is fetched and ranked, Claude reads the structured JSON output as a creative strategist. It mines for:
- **Scroll-Stopping Hooks**: Opening lines and visual concepts that captured attention.
- **Voice-of-Customer Language**: Exact phrasing used by real people (pain points, desires, objections).
- **Cross-Platform Signals**: When the exact same complaint or desire appears on *both* Reddit and TikTok, Claude flags it as **`validated`** — signifying a proven market opportunity.

### 5. Interactive Dashboard
Finally, `renderer.py` transforms the mined insights into a standalone, dark-mode HTML dashboard containing top insights, data breakdowns, and 3 concrete `"Make Next"` content ideas ready for production.

---

## Clean Architecture & Refactoring

To keep the codebase maintainable, modular, and portable as a Claude Code plugin, the repository structure is organized cleanly:

```
.
├── .claude-plugin/
│   └── plugin.json            # Plugin manifest for Claude Code
└── skills/
    └── scroll-stoppers/
        ├── SKILL.md            # Mining rules & LLM workflow
        └── scripts/
            ├── fetchers.py     # Platform scrapers (Reddit, YT, TikTok, IG)
            ├── ranker.py       # Logarithmic scoring & sorting
            ├── orchestrator.py # Multi-platform CLI runner
            └── renderer.py     # HTML dashboard renderer
```

By leveraging `${CLAUDE_PLUGIN_ROOT}` in the plugin skill definitions, the scripts run seamlessly regardless of what project directory the user is currently working in.

---

## Key Lessons Learned

1. **Don't Scrape Hashtags on Instagram**: Hashtag scrapers on Instagram return high volumes of brand spam and low-engagement noise. Querying specific creator handles filtered by relevance keywords yields 10x higher signal.
2. **Hybrid Workflows Win**: Treating the LLM as a *reasoning layer* on top of deterministic scripts creates reliable, production-grade tools.
3. **Traceability Builds Trust**: In creative tools, users need to trust the output. Providing direct links back to raw source posts turns abstract AI advice into verifiable market research.

---

## Conclusion

Content creation doesn't have to be a guessing game. By combining deterministic data processing with LLM-based creative synthesis, you can transform hours of doom-scrolling into structured, high-converting content strategies in under three minutes.

👉 **Check out the full source code and open-source plugin on GitHub**: [balamuru/context-research](https://github.com/balamuru/context-research)

*Have you built tools combining deterministic scripts with LLM agents? Let's discuss in the comments below!*
