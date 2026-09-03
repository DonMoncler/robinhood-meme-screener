"""
One poll cycle: pull fresh data from DexScreener (price/liquidity/volume/
buy-sell) + Blockscout (holders/verification) for every tracked token,
write a snapshot, then recompute its score.

DexScreener replaces Codex entirely -- free, no API key needed.
"""
import time
import blockscout_client as bs
import dexscreener_client as ds
import scoring
from storage import upsert_token, insert_snapshot, insert_score, all_tracked_tokens


def discover_new_tokens():
    """DexScreener's latest token profiles, filtered to Robinhood Chain."""
    try:
        profiles = ds.get_latest_token_profiles()
    except Exception as e:
        print(f"[discover] DexScreener profiles fetch failed: {e}")
        return []

    new_addrs = []
    for p in profiles:
        addr = p.get("tokenAddress")
        if not addr:
            continue
        upsert_token(addr)
        new_addrs.append(addr)
    return new_addrs


def compute_top10_pct(address):
    """
    Top-10 wallet concentration, computed from Blockscout's holder list
    (Codex used to provide this directly; Blockscout gives us the raw
    holder balances so we compute the percentage ourselves).
    """
    try:
        data = bs.get_token_holders(address, limit=100)
        items = data.get("items", []) if isinstance(data, dict) else data
        balances = [float(h.get("value", 0)) for h in items]
        total = sum(balances)
        if total <= 0:
            return None
        top10 = sum(sorted(balances, reverse=True)[:10])
        return top10 / total
    except Exception as e:
        print(f"[{address}] top10 concentration calc failed: {e}")
        return None


def poll_token(token_row):
    address = token_row["address"]

    try:
        counters = bs.get_token_counters(address)
        holder_count = int(counters.get("token_holders_count", 0))
    except Exception as e:
        print(f"[{address}] blockscout counters failed: {e}")
        holder_count = None

    try:
        verified = bs.is_contract_verified(address)
    except Exception:
        verified = None

    if verified is not None:
        upsert_token(address, verified=verified)

    price_usd = liquidity_usd = None
    vol1 = vol6 = vol24 = None
    buys1 = sells1 = None

    try:
        pair = ds.get_best_pair(address)
        if pair:
            price_usd = float(pair.get("priceUsd") or 0) or None
            liquidity_usd = (pair.get("liquidity") or {}).get("usd")
            volume = pair.get("volume") or {}
            vol1 = volume.get("h1")
            vol6 = volume.get("h6")
            vol24 = volume.get("h24")
            txns_h1 = (pair.get("txns") or {}).get("h1") or {}
            buys1 = txns_h1.get("buys")
            sells1 = txns_h1.get("sells")
    except Exception as e:
        print(f"[{address}] dexscreener pair fetch failed: {e}")

    top10_pct = compute_top10_pct(address)

    insert_snapshot(
        address,
        price_usd=price_usd,
        liquidity_usd=liquidity_usd,
        volume_1h_usd=vol1,
        volume_6h_usd=vol6,
        volume_24h_usd=vol24,
        buys_1h=buys1,
        sells_1h=sells1,
        holder_count=holder_count,
        top10_pct=top10_pct,
    )

    breakdown, final_score, flags, recommended = scoring.compute_score(address, token_row)
    insert_score(address, breakdown, final_score, flags, recommended)

    print(f"[{address}] score={final_score}/90 flags={flags} recommended={recommended}")


def run_cycle():
    discover_new_tokens()
    for token_row in all_tracked_tokens():
        try:
            poll_token(token_row)
        except Exception as e:
            print(f"[{token_row['address']}] poll_token crashed: {e}")
