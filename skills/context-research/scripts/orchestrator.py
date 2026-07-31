#!/usr/bin/env python3
"""
Orchestrator for context-research. This is the deterministic half of the
pipeline: fetch from all four platforms, normalize, rank, write JSON.
No LLM calls happen here — Claude does the mining afterwards, reading the
JSON this script writes, per SKILL.md.

Usage:
    python3 orchestrator.py \\
        --niche "cold plunge tubs" \\
        --subreddits coldplunge biohackers \\
        --search-terms "cold plunge" "ice bath" \\
        --creator-handles coldplungeguy icebathqueen \\
        --out /tmp/context_research_ranked.json

All targets (subreddits, search terms, creator handles) must already be
resolved from the fuzzy niche before calling this script — that resolution
step is Claude's reasoning job, not this script's.
"""

from __future__ import annotations

import argparse
import json
import sys

from ranker import rank_items, summarize_by_platform
from fetchers import fetch_instagram, fetch_reddit, fetch_tiktok, fetch_youtube


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch, normalize, and rank content across platforms.")
    parser.add_argument("--niche", required=True, help="The niche/keyword this run is for.")
    parser.add_argument("--subreddits", nargs="*", default=[], help="Resolved subreddit names (no r/ prefix).")
    parser.add_argument("--search-terms", nargs="*", default=[], help="Search terms for Reddit/YouTube/TikTok.")
    parser.add_argument("--creator-handles", nargs="*", default=[], help="Resolved Instagram creator handles.")
    parser.add_argument(
        "--relevance-keywords",
        nargs="*",
        default=[],
        help="Keywords used to filter Instagram reels for topical relevance.",
    )
    parser.add_argument("--skip", nargs="*", default=[], choices=["reddit", "youtube", "tiktok", "instagram"],
                         help="Platforms to skip (e.g. if a scraper is failing).")
    parser.add_argument("--out", required=True, help="Path to write the ranked JSON output.")
    args = parser.parse_args()

    query = args.search_terms[0] if args.search_terms else args.niche
    all_items = []
    errors = []

    if "reddit" not in args.skip and args.subreddits:
        try:
            all_items += fetch_reddit(args.subreddits, query)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"reddit: {exc}")

    if "youtube" not in args.skip and args.search_terms:
        try:
            all_items += fetch_youtube(args.search_terms)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"youtube: {exc}")

    if "tiktok" not in args.skip and args.search_terms:
        try:
            all_items += fetch_tiktok(args.search_terms)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"tiktok: {exc}")

    if "instagram" not in args.skip and args.creator_handles:
        try:
            all_items += fetch_instagram(args.creator_handles, args.relevance_keywords)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"instagram: {exc}")

    ranked = rank_items(all_items)

    output = {
        "niche": args.niche,
        "targets": {
            "subreddits": args.subreddits,
            "search_terms": args.search_terms,
            "creator_handles": args.creator_handles,
        },
        "platform_counts": summarize_by_platform(ranked),
        "errors": errors,
        "items": ranked,
    }

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(ranked)} ranked items to {args.out}", file=sys.stderr)
    if errors:
        print(f"Errors during fetch: {errors}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
