"""
Twitter-driven discovery scan for Robinhood Chain meme coins:
finds cashtags being talked about on X, cross-references each against
DexScreener for market cap + liquidity, filters to market cap < $500k,
and ranks the survivors by Twitter buzz.

v3 update: broadened SEARCH_TERMS beyond the literal "Robinhood Chain"
phrase -- most people talking about a specific meme coin just name the
coin/cashtag, not the chain, so the narrower v2 search was missing most
real chatter. Two batched queries now cover chain-name mentions AND
meme/gem-style language, still kept to 2 queries total to control
Apify cost.

v2 fixes (still in effect):
- Ignore major-asset cashtags ($BTC, $ETH, $USDT, etc.) -- these are not
  obscure Robinhood Chain meme coins, they're noise from generic crypto
  tweets, and searching DexScreener for them returns garbage.
- Reject any DexScreener match whose symbol/name is implausibly long
  (>15 chars) -- this is a known impersonation-token scam pattern: a
  token names itself with dozens of major ticker symbols crammed
  together (e.g. "BTCETHUSDTBNB...") so it surfaces in searches for
  ANY of those tickers.
"""
import json
import re
import time
import os

import apify_twitter_client as apify
import dexscreener_client as ds

MARKET_CAP_CEILING = 500_000
TOP_N = 10
MAX_SYMBOL_LEN = 15

CASHTAG_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9]{1,9})\b")

MAJOR_ASSET_BLOCKLIST = {
    "BTC", "ETH", "USDT", "USDC", "BNB", "XRP", "SOL", "TRX", "DOGE",
    "ADA", "LINK", "AVAX", "SHIB", "DOT", "MATIC", "LTC", "BCH", "XLM",
    "UNI", "ATOM", "ETC", "FIL", "APT", "ARB", "OP", "NEAR", "HOOD",
}

SEARCH_TERMS = [
    '("Robinhood Chain" OR "RobinhoodChain" OR "RH chain" OR "#RHChain" OR "chain 4663") lang:en',
    '(cashcat OR "robinhood chain gem" OR "robinhood chain meme" OR "robinhood meme coin") lang:en',
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
        tags -= MAJOR_ASSET_BLOCKLIST
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


def is_plausible_token(symbol, name):
    if symbol and len(symbol) > MAX_SYMBOL_LEN:
        return False
    if name and len(name) > 40:
        return False
    return True


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

        plausible_pairs = [
            p for p in pairs
            if is_plausible_token(
                (p.get("baseToken") or {}).get("symbol"),
                (p.get("baseToken") or {}).get("name"),
            )
        ]
        if not plausible_pairs:
            print(f"[{tag}] all DexScreener matches look like impersonation tokens -- skipped")
            continue

        best = max(plausible_pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
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
    return (item["twitter_mentions"] * item["twitter_distinct_authors"], item["twitter_engagement"])


if __name__ == "__main__":
    try:
        tweets = apify.search_tweets(SEARCH_TERMS, max_items=200)
    except Exception as e:
        print(f"Apify search failed: {e}")
        tweets = []

    cashtag_stats = extract_cashtag_stats(tweets)
    print(f"Found {len(cashtag_stats)} distinct cashtags mentioned (after blocklist filter).")

    enriched = enrich_with_market_data(cashtag_stats)
    enriched.sort(key=buzz_score, reverse=True)
    top10 = enriched[:TOP_N]

    out = {"last_updated": int(time.time()), "market_cap_ceiling": MARKET_CAP_CEILING, "coins": top10}

    os.makedirs("data", exist_ok=True)
    with open("data/twitter_gems.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote data/twitter_gems.json with {len(top10)} coins under ${MARKET_CAP_CEILING:,} mcap.")
