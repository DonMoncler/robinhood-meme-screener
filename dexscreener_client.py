"""
DexScreener public API client for Robinhood Chain.
Docs: https://docs.dexscreener.com/api/reference
100% free, no signup, no API key. Rate limits: 60 req/min on most
endpoints, 300 req/min on the /latest/dex/* endpoints.

Replaces Codex as the price/liquidity/volume/buy-sell data source.
"""
import requests

BASE = "https://api.dexscreener.com"
CHAIN_ID = "robinhood"  # DexScreener's string slug for Robinhood Chain


def get_latest_token_profiles():
    """
    Newest tokens with a DexScreener profile, across all chains.
    Filter to Robinhood Chain -- this is your discovery feed, replacing
    Codex's filterTokens/trending query.
    """
    r = requests.get(f"{BASE}/token-profiles/latest/v1", timeout=20)
    r.raise_for_status()
    profiles = r.json() or []
    return [p for p in profiles if p.get("chainId") == CHAIN_ID]


def get_token_pairs(token_address):
    """
    All trading pairs for a token: price, liquidity, volume (m5/h1/h6/h24),
    buys/sells per window, pool creation time. Core snapshot data source.
    """
    r = requests.get(f"{BASE}/token-pairs/v1/{CHAIN_ID}/{token_address}", timeout=20)
    r.raise_for_status()
    return r.json() or []


def get_best_pair(token_address):
    """Highest-liquidity pair for a token -- use this one for scoring."""
    pairs = get_token_pairs(token_address)
    if not pairs:
        return None
    return max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)


def search_pairs(query):
    """Search by token name/symbol/address across all chains."""
    r = requests.get(f"{BASE}/latest/dex/search", params={"q": query}, timeout=20)
    r.raise_for_status()
    data = r.json()
    pairs = data.get("pairs") or []
    return [p for p in pairs if p.get("chainId") == CHAIN_ID]
