import argparse
import csv
from typing import Any, Dict, List, Optional

import requests

# ERC-20 Approval event signature:
# Approval(address indexed owner, address indexed spender, uint256 value)
APPROVAL_TOPIC0 = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
MAX_UINT256 = (1 << 256) - 1


def rpc_call(rpc_url: str, method: str, params: list) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(rpc_url, json=payload, timeout=60)

    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"RPC returned non-JSON: HTTP {r.status_code}, body={r.text[:200]}")

    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} error from RPC: {data}")

    if "error" in data and data["error"]:
        raise RuntimeError(data["error"])

    return data["result"]


def hex_to_int(x: str) -> int:
    # safe conversion for hex strings like "0x1a"
    return int(x, 16)


def normalize_address(addr: str) -> str:
    addr = addr.strip()
    if not addr.startswith("0x"):
        addr = "0x" + addr
    return addr.lower()


def topic_to_address(topic_hex: str) -> str:
    """
    topics[1] and topics[2] are 32-byte values.
    The last 20 bytes represent the address.
    """
    if not topic_hex.startswith("0x"):
        topic_hex = "0x" + topic_hex
    return "0x" + topic_hex[-40:].lower()


def get_block_number(rpc_url: str) -> int:
    return hex_to_int(rpc_call(rpc_url, "eth_blockNumber", []))


def get_logs_approval(rpc_url: str, from_block: int, to_block: int) -> List[Dict[str, Any]]:
    flt = {
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
        "topics": [APPROVAL_TOPIC0],
    }
    return rpc_call(rpc_url, "eth_getLogs", [flt])


def safe_get_logs_chunked(rpc_url: str, start: int, end: int, chunk: int) -> List[Dict[str, Any]]:
    """
    Fetch logs in small block chunks to handle RPC limits.
    Alchemy free tier often requires very small chunk (like 10).
    """
    all_logs = []
    cur = start

    while cur <= end:
        nxt = min(cur + chunk - 1, end)
        logs = get_logs_approval(rpc_url, cur, nxt)
        all_logs.extend(logs)
        cur = nxt + 1

    return all_logs


def decode_approval_log(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    topics = log.get("topics", [])
    if len(topics) < 3:
        return None

    token = (log.get("address") or "").lower()
    owner = topic_to_address(topics[1])
    spender = topic_to_address(topics[2])

    data_hex = log.get("data", "0x0")

    # Some RPCs return empty data as "0x"
    if not data_hex or data_hex == "0x":
        value = 0
    else:
        value = hex_to_int(data_hex)

    block_number = hex_to_int(log.get("blockNumber", "0x0"))
    tx_hash = log.get("transactionHash", "")

    return {
        "token": token,
        "owner": owner,
        "spender": spender,
        "value": value,
        "blockNumber": block_number,
        "txHash": tx_hash,
    }


def is_unlimited(value: int) -> bool:
    return value == MAX_UINT256


def risk_score(value: int) -> int:
    # MVP scoring: unlimited approvals are high risk
    if is_unlimited(value):
        return 60
    return 10


def save_csv(rows: List[Dict[str, Any]], filename: str):
    if not rows:
        return

    cols = ["risk_score", "unlimited", "blockNumber", "token", "owner", "spender", "value", "txHash"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", required=True, help="Ethereum RPC URL (Alchemy)")
    parser.add_argument("--address", required=True, help="Wallet address (0x...)")
    parser.add_argument("--lookback_blocks", type=int, default=2000, help="How many recent blocks to scan")
    parser.add_argument("--chunk", type=int, default=10, help="Block chunk size (use 10 for Alchemy free tier)")

    # FAST DEMO MODE
    parser.add_argument("--from_block", type=int, default=None, help="Start block (optional)")
    parser.add_argument("--to_block", type=int, default=None, help="End block (optional)")

    # GUARANTEED OUTPUT MODE
    parser.add_argument(
        "--no_owner_filter",
        action="store_true",
        help="Do not filter by owner wallet (prints approvals from all wallets in range)",
    )

    parser.add_argument("--out", default="report.csv", help="Output CSV file name")

    args = parser.parse_args()

    rpc_url = args.rpc.strip()
    wallet = normalize_address(args.address)

    print("\n==============================")
    print(" EVM WALLET APPROVAL RISK SCAN")
    print("==============================")
    print(f"Wallet (filter target): {wallet}")

    latest = get_block_number(rpc_url)

    # Decide scan range
    if args.to_block is not None:
        end = args.to_block
    else:
        end = latest

    if args.from_block is not None:
        start = args.from_block
    else:
        start = max(0, end - args.lookback_blocks)

    print(f"Latest block: {latest}")
    print(f"Scanning blocks: {start} -> {end}\n")

    # Fetch logs
    logs = safe_get_logs_chunked(rpc_url, start, end, args.chunk)
    print(f"Found Approval logs (all tokens): {len(logs)}")

    approvals: List[Dict[str, Any]] = []

    for lg in logs:
        d = decode_approval_log(lg)
        if not d:
            continue

        # Filter by owner unless demo wants all
        if args.no_owner_filter or d["owner"] == wallet:
            d["unlimited"] = is_unlimited(d["value"])
            d["risk_score"] = risk_score(d["value"])
            approvals.append(d)

    if args.no_owner_filter:
        print(f"Approvals collected (NO owner filter): {len(approvals)}\n")
    else:
        print(f"Approvals belonging to wallet: {len(approvals)}\n")

    if not approvals:
        print("No approvals found for this wallet in this range.")
        print("Tip: Increase --lookback_blocks or try --no_owner_filter for demo output.")
        return

    # Sort: highest risk first, newest first
    approvals.sort(key=lambda x: (x["risk_score"], x["blockNumber"]), reverse=True)

    # Print top results
    print("Top approvals (ranked):")
    print("-" * 120)
    print(f"{'risk':>4}  {'unlim':>5}  {'block':>10}  {'token':<42}  {'owner':<42}  {'spender':<42}")
    print("-" * 120)

    for a in approvals[:15]:
        print(
            f"{a['risk_score']:>4}  {str(a['unlimited']):>5}  {a['blockNumber']:>10}  "
            f"{a['token']:<42}  {a['owner']:<42}  {a['spender']:<42}"
        )

    # Save CSV
    save_csv(approvals, args.out)
    print(f"\n✅ CSV saved: {args.out}")

    print("\nExplaination:")
    print("- unlimited=True means allowance was MAX_UINT256 (highest risk).")
    print("- spender is the contract that can spend tokens from owner wallet.\n")


if __name__ == "__main__":
    main()
