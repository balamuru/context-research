"""
Platform fetchers for scroll-stoppers.

Each fetch_* function returns a list of normalized dicts:
    {platform, text, author, url, date, engagement, raw}

`date` is an ISO 8601 string (UTC). `engagement` is a single comparable
number (see analyze.py for how it's put on a common scale across platforms).

This module only fetches and normalizes. It never interprets or ranks
content — that's split across analyze.py (ranking) and the SKILL.md
instructions Claude follows (mining).
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

import requests

APIFY_TOKEN_ENV = "APIFY_API_TOKEN"
APIFY_BASE = "https://api.apify.com/v2"

USER_AGENT = "scroll-stoppers-research-bot/1.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_from_unix(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _get_apify_token() -> str:
    token = os.environ.get(APIFY_TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"{APIFY_TOKEN_ENV} is not set. Export your Apify API token "
            f"before running the engine."
        )
    return token


def _run_apify_actor(actor_id: str, run_input: dict[str, Any], timeout_secs: int = 180) -> list[dict]:
    """
    Runs an Apify actor synchronously and returns its dataset items.
    Uses the "run-sync-get-dataset-items" endpoint so we don't have to poll.
    """
    token = _get_apify_token()
    url = f"{APIFY_BASE}/acts/{actor_id}/run-sync-get-dataset-items"
    resp = requests.post(
        url,
        params={"token": token},
        json=run_input,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout_secs,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Reddit — free public JSON API, no auth required.
# ---------------------------------------------------------------------------

def fetch_reddit(
    subreddits: list[str],
    query: str,
    time_window: str = "month",
    limit: int = 25,
    max_retries: int = 3,
) -> list[dict]:
    results: list[dict] = []
    failures: list[str] = []
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/search.json"
        params = {
            "q": query,
            "restrict_sr": "1",
            "sort": "top",
            "t": time_window,
            "limit": limit,
        }
        last_error: Exception | None = None
        resp = None
        for attempt in range(max_retries):
            try:
                resp = requests.get(
                    url,
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=20,
                )
                if resp.status_code == 429:
                    last_error = RuntimeError(f"rate-limited (429) on r/{sub}")
                    resp = None
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = exc
                resp = None
                if attempt == max_retries - 1:
                    break
                time.sleep(2 ** attempt)
        if resp is None:
            failures.append(f"r/{sub}: {last_error}")
            continue

        data = resp.json()
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            score = post.get("score", 0) or 0
            comments = post.get("num_comments", 0) or 0
            text = post.get("title", "")
            if post.get("selftext"):
                text = f"{text}\n\n{post['selftext']}"
            results.append(
                {
                    "platform": "reddit",
                    "text": text,
                    "author": post.get("author", "unknown"),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "date": _iso_from_unix(post.get("created_utc", time.time())),
                    "engagement": score + comments * 2,
                    "raw": {"score": score, "num_comments": comments, "subreddit": sub},
                }
            )

    if failures and not results:
        # Every subreddit failed and we have nothing to show for it -- raise
        # so the orchestrator records this in its `errors` field instead of
        # silently reporting zero Reddit items as if the search just had no
        # results.
        raise RuntimeError(f"Reddit fetch failed for all subreddits: {failures}")

    return results


# ---------------------------------------------------------------------------
# YouTube — Apify actor streamers/youtube-scraper
# ---------------------------------------------------------------------------

def fetch_youtube(search_keywords: list[str], date_filter: str = "month", max_results: int = 30) -> list[dict]:
    """
    Runs the actor once per keyword (rather than passing the whole list in
    one call) since Apify's docs don't confirm whether `maxResults` is a
    total cap or a per-keyword limit when given a list. Looping guarantees
    up to `max_results` per keyword regardless of the actor's internal
    behavior. Results are deduped by URL since the same video can surface
    for multiple keywords.
    """
    seen_urls: set[str] = set()
    results = []
    for keyword in search_keywords:
        run_input = {
            "searchQueries": [keyword],
            "dateFilter": date_filter,
            "maxResults": max_results,
        }
        items = _run_apify_actor("streamers~youtube-scraper", run_input)

        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            views = item.get("viewCount") or item.get("views") or 0
            likes = item.get("likes") or 0
            date_str = item.get("date") or item.get("uploadDate")
            results.append(
                {
                    "platform": "youtube",
                    "text": f"{item.get('title', '')}\n\n{item.get('description', '') or ''}",
                    "author": item.get("channelName", "unknown"),
                    "url": url,
                    "date": date_str or _now_iso(),
                    "engagement": int(views) + int(likes) * 5,
                    "raw": {"views": views, "likes": likes},
                }
            )
    return results


# ---------------------------------------------------------------------------
# TikTok — Apify actor clockworks/tiktok-scraper
# ---------------------------------------------------------------------------

def fetch_tiktok(search_queries: list[str], max_results: int = 30) -> list[dict]:
    run_input = {
        "searchQueries": search_queries,
        "resultsPerPage": max_results,
    }
    items = _run_apify_actor("clockworks~tiktok-scraper", run_input)

    results = []
    for item in items:
        plays = item.get("playCount", 0) or 0
        likes = item.get("diggCount", 0) or 0
        created = item.get("createTimeISO") or item.get("createTime")
        results.append(
            {
                "platform": "tiktok",
                "text": item.get("text", "") or item.get("desc", ""),
                "author": (item.get("authorMeta") or {}).get("name", "unknown"),
                "url": item.get("webVideoUrl", ""),
                "date": created or _now_iso(),
                "engagement": int(plays) + int(likes) * 3,
                "raw": {"plays": plays, "likes": likes},
            }
        )
    return results


# ---------------------------------------------------------------------------
# Instagram — Apify actor apify/instagram-reel-scraper
#
# IMPORTANT (playbook lesson #1): feed this creator handles, not hashtags.
# Hashtag-based scraping returns today's low-engagement brand spam. Resolve
# 5-8 niche-relevant creator handles up front (this is Claude's job in
# SKILL.md, not this script's), then apply the caption-relevance filter
# below so an off-topic viral reel from a real creator doesn't pollute
# the brief.
# ---------------------------------------------------------------------------

def fetch_instagram(
    creator_handles: list[str],
    relevance_keywords: list[str] | None = None,
    results_per_creator: int = 18,
) -> list[dict]:
    run_input = {
        "username": creator_handles,
        "resultsLimit": results_per_creator,
    }
    items = _run_apify_actor("apify~instagram-reel-scraper", run_input)

    relevance_keywords = [k.lower() for k in (relevance_keywords or [])]

    results = []
    for item in items:
        caption = item.get("caption", "") or ""
        if relevance_keywords and not any(k in caption.lower() for k in relevance_keywords):
            continue  # caption-relevance filter: drop off-topic reels

        likes = item.get("likesCount", 0) or 0
        plays = item.get("videoPlayCount") or item.get("playsCount") or 0
        timestamp = item.get("timestamp")
        results.append(
            {
                "platform": "instagram",
                "text": caption,
                "author": item.get("ownerUsername", "unknown"),
                "url": item.get("url", ""),
                "date": timestamp or _now_iso(),
                "engagement": int(plays) + int(likes) * 3,
                "raw": {"plays": plays, "likes": likes},
            }
        )
    return results
