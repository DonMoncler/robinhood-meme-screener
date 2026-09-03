"""
Composite momentum score (0-90) + manipulation penalty layer.
Built around RATE OF CHANGE: sub-scores mostly look at slopes between
the current snapshot and snapshots 1h/6h/24h back, not absolute levels.
"""
import time
from config import FLAG_THRESHOLDS
from storage import get_snapshots_since, get_social_since


def _closest(snapshots, target_ts):
    if not snapshots:
        return None
    return min(snapshots, key=lambda s: abs(s["ts"] - target_ts))


def _pct_change(new, old):
    if old in (None, 0):
        return None
    return (new - old) / old


def _slope_per_hour(new_val, old_val, hours):
    if new_val is None or old_val is None or hours <= 0:
        return None
    return (new_val - old_val) / hours


def score_liquidity_volume(address, now_ts=None):
    now_ts = now_ts or int(time.time())
    hist = get_snapshots_since(address, now_ts - 26 * 3600)
    if not hist:
        return 0.0, {}

    latest = hist[-1]
    h6 = _closest(hist, now_ts - 6 * 3600)

    score = 0.0
    detail = {}

    liq_change_6h = _pct_change(latest["liquidity_usd"], h6["liquidity_usd"] if h6 else None)
    detail["liquidity_change_6h_pct"] = liq_change_6h
    if liq_change_6h is not None:
        score += max(0, min(8, 4 + liq_change_6h * 20))

    v1 = latest.get("volume_1h_usd") or 0
    v6 = latest.get("volume_6h_usd") or 0
    run_rate_1h = v1
    run_rate_6h_avg = v6 / 6 if v6 else 0
    accel_short = _pct_change(run_rate_1h, run_rate_6h_avg)
    detail["volume_accel_1h_vs_6h_pct"] = accel_short
    if accel_short is not None:
        score += max(0, min(9, 4.5 + accel_short * 9))

    buys = latest.get("buys_1h") or 0
    sells = latest.get("sells_1h") or 0
    total = buys + sells
    buy_ratio = buys / total if total else None
    detail["buy_ratio_1h"] = buy_ratio
    if buy_ratio is not None:
        if FLAG_THRESHOLDS["buy_sell_ratio_bullish_min"] <= buy_ratio <= FLAG_THRESHOLDS["buy_sell_ratio_suspicious"]:
            score += 8
        elif buy_ratio > FLAG_THRESHOLDS["buy_sell_ratio_suspicious"]:
            score += 2
        else:
            score += max(0, 8 * (buy_ratio / FLAG_THRESHOLDS["buy_sell_ratio_bullish_min"]))

    return round(min(score, 25), 2), detail


def score_holder_growth(address, now_ts=None):
    now_ts = now_ts or int(time.time())
    hist = get_snapshots_since(address, now_ts - 26 * 3600)
    if not hist:
        return 0.0, {}

    latest = hist[-1]
    h1 = _closest(hist, now_ts - 3600)

    score = 0.0
    detail = {}

    holders_per_hr = _slope_per_hour(latest.get("holder_count"),
                                      h1.get("holder_count") if h1 else None, 1)
    detail["holders_growth_per_hr"] = holders_per_hr
    if holders_per_hr is not None:
        score += max(0, min(12, holders_per_hr / 50 * 12))

    top10 = latest.get("top10_pct")
    detail["top10_pct"] = top10
    if top10 is not None:
        score += max(0, min(8, (1 - top10) * 8))

    detail["deployer_selling_pct"] = None
    score += 2.5

    return round(min(score, 25), 2), detail


def score_social_momentum(address, now_ts=None):
    now_ts = now_ts or int(time.time())
    hist = get_social_since(address, now_ts - 26 * 3600)
    if not hist:
        return 0.0, {}

    latest = hist[-1]
    h1 = _closest(hist, now_ts - 3600)

    score = 0.0
    detail = {}

    mentions_now = latest.get("mentions_count") or 0
    mentions_prev = h1.get("mentions_count") if h1 else None
    velocity = _pct_change(mentions_now, mentions_prev)
    detail["mention_velocity_pct"] = velocity
    if velocity is not None:
        score += max(0, min(10, 5 + velocity * 5))
    elif mentions_now > 0:
        score += 3

    distinct = latest.get("distinct_authors") or 0
    detail["distinct_authors"] = distinct
    score += max(0, min(8, distinct / 30 * 8))

    followers = latest.get("followers_sum") or 0
    engagement = latest.get("engagement_sum") or 0
    eng_ratio = engagement / followers if followers else None
    detail["engagement_to_follower_ratio"] = eng_ratio
    if eng_ratio is not None:
        score += max(0, min(7, eng_ratio * 700))

    return round(min(score, 25), 2), detail


def score_contract_safety(token_row, now_ts=None):
    now_ts = now_ts or int(time.time())
    score = 0.0
    detail = {}

    verified = bool(token_row.get("verified"))
    detail["verified"] = verified
    score += 6 if verified else 0

    detail["ownership_renounced"] = None
    detail["mint_or_blacklist_present"] = None
    score += 4

    deploy_ts = token_row.get("deploy_ts")
    if deploy_ts:
        age_hours = (now_ts - deploy_ts) / 3600
        detail["age_hours"] = age_hours
        if age_hours < 1:
            score += 2
        elif age_hours < 72:
            score += 5
        else:
            score += 3

    return round(min(score, 15), 2), detail


def detect_flags(address, liquidity_detail, holder_detail, social_detail, now_ts=None):
    now_ts = now_ts or int(time.time())
    flags = []
    hist = get_snapshots_since(address, now_ts - 26 * 3600)
    latest = hist[-1] if hist else {}

    buy_ratio = liquidity_detail.get("buy_ratio_1h")
    if buy_ratio is not None and buy_ratio > FLAG_THRESHOLDS["buy_sell_ratio_suspicious"]:
        flags.append("one_sided_buy_pressure")

    velocity = social_detail.get("mention_velocity_pct")
    holders_per_hr = holder_detail.get("holders_growth_per_hr")
    if velocity is not None and velocity > 1.0 and (holders_per_hr or 0) < 2:
        flags.append("social_spike_no_holder_growth")

    vol24 = latest.get("volume_24h_usd") or 0
    liq = latest.get("liquidity_usd") or 0
    if liq > 0 and (vol24 / liq) > FLAG_THRESHOLDS["vol_to_liquidity_max"]:
        flags.append("implausible_volume_to_liquidity")

    top10 = holder_detail.get("top10_pct")
    if top10 is not None and top10 > FLAG_THRESHOLDS["top10_concentration_max"]:
        flags.append("high_top10_concentration")

    return flags


def compute_score(address, token_row, now_ts=None):
    now_ts = now_ts or int(time.time())

    liq_score, liq_detail = score_liquidity_volume(address, now_ts)
    hold_score, hold_detail = score_holder_growth(address, now_ts)
    soc_score, soc_detail = score_social_momentum(address, now_ts)
    safe_score, safe_detail = score_contract_safety(token_row, now_ts)

    raw_total = liq_score + hold_score + soc_score + safe_score

    flags = detect_flags(address, liq_detail, hold_detail, soc_detail, now_ts)

    final_score = raw_total
    if len(flags) >= FLAG_THRESHOLDS["min_flags_for_cap"]:
        final_score = min(raw_total, FLAG_THRESHOLDS["capped_score_max"])

    recommended = (len(flags) < FLAG_THRESHOLDS["min_flags_for_cap"]) and final_score >= 45

    breakdown = {
        "liquidity": liq_score,
        "holders": hold_score,
        "social": soc_score,
        "safety": safe_score,
        "raw_total": round(raw_total, 2),
        "detail": {
            "liquidity": liq_detail, "holders": hold_detail,
            "social": soc_detail, "safety": safe_detail,
        },
    }
    return breakdown, round(final_score, 2), flags, recommended
