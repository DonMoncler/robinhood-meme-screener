"""
One poll cycle: pull fresh data from DexScreener (price/liquidity/volume/
buy-sell) + Blockscout (holders/verification) for every tracked token,
write a snapshot, then recompute its score.

v3 fixes:
- symbol/name now pulled from the DexScreener pair's baseToken object
  (the token-profiles endpoint doesn't include a symbol, which is why
  the dashboard was showing "?" for every token).
- top10 concentration now divides by the token's actual total supply
  (from Blockscout token info), not by the sum of only the top 100
  fetched holders -- the old version overstated concentration for any
  token with more than ~100 holders, which is why almost everything was
  getting flagged as "high top10 concentration."
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


def compute_top10_pct(address, best_pair):
    """
    Top-10 wallet concentration = sum of top 10 holder balances / actual
    total supply (pulled from Blockscout token info) -- NOT divided by
    the sum of only the fetched holder page, which overstates
    concentration for any token with more holders than the page size.
    """
    try:
        holders_data = bs.get_token_holders(address, limit=10)
        items = holders_data.get("items", []) if isinstance(holders_data, dict) else holders_data
        top10_balance = sum(float(h.get("value", 0)) for h in items[:10])

        info = bs.get_token_info(address)
        decimals = int(info.get("decimals") or 18)
        total_supply_raw = info.get("total_supply")
        if total_supply_raw is None:
            return None
        total_supply = float(total_supply_raw) / (10 ** decimals)
        top10_balance_adj = top10_balance / (10 ** decimals)

        if total_supply <= 0:
            return None
        return min(top10_balance_adj / total_supply, 1.0)
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
    best_pair = None

    try:
        best_pair = ds.get_best_pair(address)
        if best_pair:
            price_usd = float(best_pair.get("priceUsd") or 0) or None
            liquidity_usd = (best_pair.get("liquidity") or {}).get("usd")
            volume = best_pair.get("volume") or {}
            vol1 = volume.get("h1")
            vol6 = volume.get("h6")
            vol24 = volume.get("h24")
            txns_h1 = (best_pair.get("txns") or {}).get("h1") or {}
            buys1 = txns_h1.get("buys")
            sells1 = txns_h1.get("sells")

            base_token = best_pair.get("baseToken") or {}
            symbol = base_token.get("symbol")
            name = base_token.get("name")
            if symbol or name:
                upsert_token(address, symbol=symbol, name=name)
    except Exception as e:
        print(f"[{address}] dexscreener pair fetch failed: {e}")

    top10_pct = compute_top10_pct(address, best_pair)

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
