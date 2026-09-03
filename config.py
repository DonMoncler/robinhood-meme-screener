"""
Central config. Put your real API keys in a .env file (never commit it):

BLOCKSCOUT_API_KEY=proapi_xxx
CODEX_API_KEY=your_codex_key
TELEGRAM_BOT_TOKEN=xxx        # optional, for social tracking / alerts
TWITTER_BEARER_TOKEN=xxx      # optional
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CHAIN_ID = 4663  # Robinhood Chain mainnet

BLOCKSCOUT_BASE = "https://api.blockscout.com"
BLOCKSCOUT_API_KEY = os.getenv("BLOCKSCOUT_API_KEY", "")

CODEX_GRAPHQL_URL = "https://graph.codex.io/graphql"
CODEX_API_KEY = os.getenv("CODEX_API_KEY", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

DB_PATH = os.getenv("DB_PATH", "screener.db")

POLL_INTERVAL_MINUTES = 5

WINDOWS_MIN = {"short": 60, "mid": 360, "long": 1440}  # 1h / 6h / 24h

FLAG_THRESHOLDS = {
    "buy_sell_ratio_suspicious": 0.90,
    "buy_sell_ratio_bullish_min": 0.55,
    "vol_to_liquidity_max": 5.0,
    "top10_concentration_max": 0.60,
    "min_flags_for_cap": 2,
    "capped_score_max": 40,
}
