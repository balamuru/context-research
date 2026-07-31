"""
Normalize and rank items pulled from fetchers.py.

Engagement scales are wildly different across platforms (a TikTok can get
millions of plays, a Reddit thread gets thousands of upvotes). We put them on
a comparable log scale, then rank by engagement first and recency second.
Every item also gets an `age_days` field so a two-year-old viral post never
gets passed off as "trending now."

This module is deterministic — it does no interpretation of content. All
creative judgment (hooks, pains, desires, etc.) is Claude's job per
SKILL.md, working from this ranked output.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def _parse_date(date_str: str) -> datetime:
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _log_score(engagement: float) -> float:
    return math.log10(max(engagement, 0) + 1)


def rank_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Takes normalized items (platform, text, author, url, date, engagement)
    and returns them annotated with `log_engagement`, `age_days`, sorted by
    log_engagement desc, then age_days asc (more recent wins ties).
    """
    now = datetime.now(timezone.utc)
    annotated = []
    for item in items:
        published = _parse_date(item.get("date", ""))
        age_days = max((now - published).total_seconds() / 86400.0, 0.0)
        annotated.append(
            {
                **item,
                "log_engagement": round(_log_score(item.get("engagement", 0)), 3),
                "age_days": round(age_days, 1),
            }
        )

    annotated.sort(key=lambda x: (-x["log_engagement"], x["age_days"]))
    return annotated


def summarize_by_platform(ranked_items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in ranked_items:
        counts[item["platform"]] = counts.get(item["platform"], 0) + 1
    return counts
