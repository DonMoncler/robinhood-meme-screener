"""
Blockscout PRO API client for Robinhood Chain (chain_id=4663).
https://docs.blockscout.com/robinhood-api
"""
import requests
from config import BLOCKSCOUT_BASE, BLOCKSCOUT_API_KEY, CHAIN_ID

RPC_V2_URL = f"{BLOCKSCOUT_BASE}/v2/api"
REST_BASE = f"{BLOCKSCOUT_BASE}/{CHAIN_ID}/api/v2"


def _get_rpc(module, action, **params):
    q = {"chain_id": CHAIN_ID, "module": module, "action": action,
         "apikey": BLOCKSCOUT_API_KEY, **params}
    r = requests.get(RPC_V2_URL, params=q, timeout=20)
    r.raise_for_status()
    return r.json()


def _get_rest(path, **params):
    q = {"apikey": BLOCKSCOUT_API_KEY, **params}
    r = requests.get(f"{REST_BASE}{path}", params=q, timeout=20)
    r.raise_for_status()
    return r.json()


def get_token_info(token_address):
    return _get_rest(f"/tokens/{token_address}")


def get_token_holders(token_address, limit=50):
    return _get_rest(f"/tokens/{token_address}/holders", limit=limit)


def get_token_counters(token_address):
    return _get_rest(f"/tokens/{token_address}/counters")


def get_token_transfers(token_address, next_page_params=None):
    params = next_page_params or {}
    return _get_rest(f"/tokens/{token_address}/transfers", **params)


def get_contract_info(address):
    return _get_rest(f"/smart-contracts/{address}")


def is_contract_verified(address):
    try:
        info = get_contract_info(address)
        return bool(info.get("is_verified") or info.get("verified_at"))
    except requests.HTTPError:
        return False


def get_address_txlist(address, sort="asc", startblock=0):
    return _get_rpc("account", "txlist", address=address, sort=sort,
                    startblock=startblock)


def get_address_token_transfers(address):
    return _get_rpc("account", "tokentx", address=address)


def get_deploy_timestamp(token_address):
    info = get_contract_info(token_address)
    creation_tx = info.get("creation_tx_hash") or info.get("creation_transaction_hash")
    if not creation_tx:
        return None
    tx = _get_rest(f"/transactions/{creation_tx}")
    return tx.get("timestamp")
