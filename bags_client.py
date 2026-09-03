"""
Bags launches on Robinhood Chain are FULLY ON-CHAIN (no REST API, unlike
Bags on Solana). Per https://docs.bags.fm/robinhood/overview :
watch the `TokenCreated` event on BagsFactory, or poll via web3.

Simplest path for a Python-only stack: piggyback on Blockscout, which
already indexes every contract on the chain.
"""
import requests
from config import BLOCKSCOUT_BASE, CHAIN_ID, BLOCKSCOUT_API_KEY

BAGS_FACTORY = "0xe8Cc4431adF8b5A847C113EF0c6af9043219Cb37"
REST_BASE = f"{BLOCKSCOUT_BASE}/{CHAIN_ID}/api/v2"

TOKEN_CREATED_TOPIC0 = None


def get_recent_bags_launches(limit=50):
    r = requests.get(
        f"{REST_BASE}/addresses/{BAGS_FACTORY}/transactions",
        params={"apikey": BLOCKSCOUT_API_KEY, "limit": limit},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()
