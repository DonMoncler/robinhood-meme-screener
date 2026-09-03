"""
Twitter-driven discovery scan for Robinhood Chain meme coins:
finds cashtags being talked about on X, cross-references each against
DexScreener for market cap + liquidity, filters to market cap < $500k,
and ranks the survivors by Twitter buzz.

This is a SEPARATE screening view from the main momentum-score dashboard
-- it answers "what's small and loud right now," not "what scores well
across all four sub-scores." Run on a slower cadence than the main
15-min poll loop (hourly is plenty) since Apify calls cost money.

Usage: python twitter_discovery.py
Writes: data/twitter_gems.json
"""
import json
import re
import time
import os

import apify_twitter_client as apify
import dexscreener_client as ds

MARKET_CAP_CEILING = 500_000
TOP_N = 10

CASHTAG_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9]{1,9})\b")

# Broad search covering general Robinhood Chain meme coin chatter.
# Keep this to 1-2 queries per run to control Apify cost -- batch as
# many relevant keywords/cashtags into one OR-joined string as you can.
SEARCH_TERMS = [
    '("Robinhood Chain" OR "RobinhoodChain" OR "#RobinhoodChain") (meme OR coin OR token) lang:en',
]


def extract_cashtag_stats(tweets):
    stats = {}
    for t in tweets:
        text = t.get("text") or t.get("fullText") or ""
        author = (t.get("author") or {}).get("userName") or t.get("authorUsername") or "unknown"
        followers = (t.get("author") or {}).get("followers") or 0
        likes = t.get("likeCount") or t.get("favoriteCount") or 0
        retweets = t.get("retweetCount") or 0
        replies = t.get("replyCount") or 0

        tags = set(m.upper() for m in CASHTAG_RE.findall(text))
        for tag in tags:
            s = stats.setdefault(tag, {"mentions": 0, "authors": set(), "engagement": 0, "followers_sum": 0})
            s["mentions"] += 1
            s["authors"].add(author)
            s["engagement"] += likes + retweets + replies
            s["followers_sum"] += followers

    out = {}
    for tag, s in stats.items():
        out[tag] = {
            "mentions": s["mentions"],
            "distinct_authors": len(s["authors"]),
            "engagement": s["engagement"],
            "followers_sum": s["followers_sum"],
        }
    return out


def enrich_with_market_data(cashtag_stats):
    results = []
    for tag, stats in cashtag_stats.items():
        try:
            pairs = ds.search_pairs(tag)
        except Exception as e:
            print(f"[{tag}] dexscreener search failed: {e}")
            continue

        if not pairs:
            continue

        best = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
        market_cap = best.get("marketCap") or best.get("fdv")
        if market_cap is None or market_cap <= 0 or market_cap >= MARKET_CAP_CEILING:
            continue

        base_token = best.get("baseToken") or {}
        results.append({
            "symbol": base_token.get("symbol") or tag,
            "address": base_token.get("address"),
            "market_cap_usd": market_cap,
            "price_usd": best.get("priceUsd"),
            "liquidity_usd": (best.get("liquidity") or {}).get("usd"),
            "volume_24h_usd": (best.get("volume") or {}).get("h24"),
            "twitter_mentions": stats["mentions"],
            "twitter_distinct_authors": stats["distinct_authors"],
            "twitter_engagement": stats["engagement"],
            "dexscreener_url": best.get("url"),
        })
    return results


def buzz_score(item):
    """Simple composite: mentions x distinct authors, tie-broken by engagement."""
    return (item["twitter_mentions"] * item["twitter_distinct_authors"], item["twitter_engagement"])


if __name__ == "__main__":
    try:
        tweets = apify.search_tweets(SEARCH_TERMS, max_items=150)
    except Exception as e:
        print(f"Apify search failed: {e}")
        tweets = []

    cashtag_stats = extract_cashtag_stats(tweets)
    print(f"Found {len(cashtag_stats)} distinct cashtags mentioned.")

    enriched = enrich_with_market_data(cashtag_stats)
    enriched.sort(key=buzz_score, reverse=True)
    top10 = enriched[:TOP_N]

    out = {"last_updated": int(time.time()), "market_cap_ceiling": MARKET_CAP_CEILING, "coins": top10}

    os.makedirs("data", exist_ok=True)
    with open("data/twitter_gems.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote data/twitter_gems.json with {len(top10)} coins under ${MARKET_CAP_CEILING:,} mcap.")
