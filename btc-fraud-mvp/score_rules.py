import sqlite3
import pandas as pd

DB = "btc.sqlite"

def main():
    conn = sqlite3.connect(DB)

    tx = pd.read_sql("SELECT txid, block_height, n_in, n_out, total_out_sat, vsize FROM tx", conn)

    # Basic safe features
    tx["out_per_in"] = tx["n_out"] / tx["n_in"].replace(0, 1)
    tx["out_btc"] = tx["total_out_sat"] / 100_000_000

    # Simple risk scoring rules (demo-friendly)
    tx["risk"] = 0.0

    # 1) Many outputs (fan-out) -> could be structuring / distribution
    tx.loc[tx["n_out"] >= 10, "risk"] += 0.35
    tx.loc[tx["n_out"] >= 50, "risk"] += 0.35

    # 2) Very large value transfers (contextual risk)
    tx.loc[tx["out_btc"] >= 50, "risk"] += 0.25
    tx.loc[tx["out_btc"] >= 200, "risk"] += 0.25

    # 3) Unusual output/input ratio
    tx.loc[tx["out_per_in"] >= 5, "risk"] += 0.15
    tx.loc[tx["out_per_in"] >= 20, "risk"] += 0.25

    # Clip risk to [0, 1]
    tx["risk"] = tx["risk"].clip(0, 1)

    # Show top suspicious
    alerts = tx.sort_values("risk", ascending=False).head(20)

    print("\nTOP SUSPICIOUS TRANSACTIONS (MVP RULE SCORE):\n")
    print(alerts[["txid", "block_height", "n_in", "n_out", "out_btc", "vsize", "risk"]].to_string(index=False))

    conn.close()

if __name__ == "__main__":
    main()
