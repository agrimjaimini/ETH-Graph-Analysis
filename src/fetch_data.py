import os
import requests
from typing import List, Dict
import time
import pandas as pd


def fetch_transactions(start_block: int, end_block: int, api_key: str = None) -> List[Dict]:
    """
    Fetch transactions from Ethereum blocks via Etherscan Proxy API.
    Requires ETHERSCAN_API_KEY env var or supplied api_key.
    """
    if api_key is None:
        api_key = os.getenv("ETHERSCAN_API_KEY")
    base_url = "https://api.etherscan.io/api"
    tx_list: List[Dict] = []

    for block_num in range(int(start_block), int(end_block) + 1):
        hex_block = hex(block_num)
        params = {
            "module": "proxy",
            "action": "eth_getBlockByNumber",
            "tag": hex_block,
            "boolean": "true",
            "apikey": api_key
        }
        resp = requests.get(base_url, params=params)
        data = resp.json()
        block = data.get("result")

        if not block:
            print(f"⚠️ Skipped block {block_num}, no data found")
            continue

    timestamp = int(block.get("timestamp", "0x0"), 16)
    for tx in block.get("transactions", []):
            # Convert values from hex
        value_wei = int(tx.get("value", "0x0"), 16)
        gas_price_wei = int(tx.get("gasPrice", "0x0"), 16)
        tx_list.append({
                "hash": tx.get("hash"),
                "from": tx.get("from"),
                "to": tx.get("to"),
                "value": value_wei / 1e18,
                "gas": int(tx.get("gas", "0x0"), 16),
                "gas_price": gas_price_wei / 1e9,
                "timestamp": timestamp,
                "blockNumber": block_num
            })
    return tx_list


def get_balances_etherscan(addresses, etherscan_api_key, batch_size=20, delay=0.25):
    """
    Fetch ETH balances using Etherscan's `balancemulti` API in batches of up to 20 addresses.
    Saves the results to data/balances.csv.
    """
    balances = {}
    base_url = "https://api.etherscan.io/api"
    total = len(addresses)

    for i in range(0, total, batch_size):
        batch = addresses[i:i + batch_size]
        addr_string = ",".join(batch)
        params = {
            "module": "account",
            "action": "balancemulti",
            "address": addr_string,
            "tag": "latest",
            "apikey": etherscan_api_key
        }

        try:
            resp = requests.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data["status"] == "1":
                for item in data["result"]:
                    balances[item["account"].lower()] = int(item["balance"]) / 1e18
            else:
                print("Etherscan error:", data.get("message", "Unknown error"))
                for addr in batch:
                    balances[addr.lower()] = 0.0
        except Exception as e:
            print(f"Error fetching balances from Etherscan: {e}")
            for addr in batch:
                balances[addr.lower()] = 0.0

        print(f"Fetched {min(i + batch_size, total)} / {total} balances...")
        time.sleep(delay)

    os.makedirs("data", exist_ok=True)
    df_balances = pd.DataFrame([
        {"address": addr, "balance": balance}
        for addr, balance in balances.items()
    ])
    df_balances.to_csv("data/balances.csv", index=False)
    print("📁 Saved balances to data/balances.csv")

    return balances


def get_current_block(api_key):
    url = "https://api.etherscan.io/api"
    params = {
        "module": "proxy",
        "action": "eth_blockNumber",
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()

    block_hex = data.get("result")
    if block_hex:
        return int(block_hex, 16)
    return None