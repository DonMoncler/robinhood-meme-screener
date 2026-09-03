"""
Codex API client (GraphQL) for Robinhood Chain (network=4663).
Docs: https://docs.codex.io/networks/robinhood

Verify exact field names against Codex's GraphQL Explorer
(https://docs.codex.io/explore) before relying on this in production.
"""
import requests
from config import CODEX_GRAPHQL_URL, CODEX_API_KEY, CHAIN_ID

HEADERS = {"Content-Type": "application/json", "Authorization": CODEX_API_KEY}


def _post(query, variables=None):
    r = requests.post(
        CODEX_GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers=HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def get_trending_tokens(limit=25, min_liquidity_usd=1000):
    query = """
    query FilterTokens($network: Int!, $limit: Int!, $minLiquidity: Float!) {
      filterTokens(
        filters: { network: [$network], liquidity: { gt: $minLiquidity } }
        rankings: { attribute: trendingScore, direction: DESC }
        limit: $limit
      ) {
        results {
          token { address symbol name }
          liquidity
          volume24
          priceUSD
          createdAt
        }
      }
    }
    """
    data = _post(query, {"network": CHAIN_ID, "limit": limit,
                          "minLiquidity": min_liquidity_usd})
    return data["filterTokens"]["results"]


def get_token_price(token_address):
    query = """
    query GetTokenPrices($input: [TokenPriceInput!]!) {
      getTokenPrices(inputs: $input) {
        address
        priceUsd
        timestamp
      }
    }
    """
    data = _post(query, {"input": [{"address": token_address, "networkId": CHAIN_ID}]})
    return data["getTokenPrices"][0]


def get_pair_stats(pair_address):
    query = """
    query GetDetailedPairStats($pairAddress: String!, $network: Int!) {
      getDetailedPairStats(pairAddress: $pairAddress, networkId: $network) {
        liquidity
        volume1
        volume6
        volume24
        buys1
        sells1
        buys24
        sells24
      }
    }
    """
    data = _post(query, {"pairAddress": pair_address, "network": CHAIN_ID})
    return data["getDetailedPairStats"]


def get_token_events(token_address, limit=100):
    query = """
    query GetTokenEvents($address: String!, $network: Int!, $limit: Int!) {
      getTokenEvents(address: $address, networkId: $network, limit: $limit) {
        items {
          type
          amountUsd
          maker
          timestamp
        }
      }
    }
    """
    data = _post(query, {"address": token_address, "network": CHAIN_ID, "limit": limit})
    return data["getTokenEvents"]["items"]


def get_top_traders(token_address, limit=20):
    query = """
    query TokenTopTraders($address: String!, $network: Int!, $limit: Int!) {
      tokenTopTraders(address: $address, networkId: $network, limit: $limit) {
        wallet
        volumeUsd
        pnlUsd
      }
    }
    """
    data = _post(query, {"address": token_address, "network": CHAIN_ID, "limit": limit})
    return data["tokenTopTraders"]


def get_top10_holder_pct(token_address):
    query = """
    query Top10HoldersPercent($address: String!, $network: Int!) {
      top10HoldersPercent(address: $address, networkId: $network)
    }
    """
    data = _post(query, {"address": token_address, "network": CHAIN_ID})
    return data["top10HoldersPercent"]
