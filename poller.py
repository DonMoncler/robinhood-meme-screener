"""
One poll cycle: pull fresh data from Blockscout + Codex for every tracked
token, write a snapshot, then recompute its score.
"""
import time
import blockscout_client as bs
import codex_client as cx
import scoring
from storage import upsert_token, insert_snapshot, insert_score, all_tracked_tokens


def discover_new_tokens():
    try:
        trending = cx.get_trending_tokens(limit=25)
    except Exception as e:
        print(f"[discover] Codex trending fetch failed: {e}")
        return []

    new_addrs = []
    for item in trending:
        addr = item["token"]["address"]
        upsert_token(
            addr,
            symbol=item["token"].get("symbol"),
            name=item["token"].get("name"),
        )
        new_addrs.append(addr)
    return new_addrs


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
    top10_pct = None
    try:
        price_data = cx.get_token_price(address)
        price_usd = price_data.get("priceUsd")
    except Exception as e:
        print(f"[{address}] codex price failed: {e}")

    try:
        top10_pct = cx.get_top10_holder_pct(address)
    except Exception as e:
        print(f"[{address}] codex top10 failed: {e}")

    try:
        events = cx.get_token_events(address, limit=200)
        cutoff = time.time() - 3600
        recent = [e for e in events if e.get("timestamp", 0) >= cutoff]
        buys1 = sum(1 for e in recent if e.get("type") == "buy")
        sells1 = sum(1 for e in recent if e.get("type") == "sell")
    except Exception as e:
        print(f"[{address}] codex events failed: {e}")

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
