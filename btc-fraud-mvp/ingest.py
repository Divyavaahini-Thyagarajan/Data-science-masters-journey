import json
from typing import Dict, Any, Optional, Tuple
from tqdm import tqdm

from rpc import BitcoinRPC
from db import connect, init_db, executemany


def load_config(path: str = "config.json") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def satoshis(btc: float) -> int:
    return int(round(btc * 100_000_000))


def parse_address(vout: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to extract a single address + script type from a vout.
    Depending on Bitcoin Core version and output type, fields vary.
    """
    spk = vout.get("scriptPubKey", {})
    stype = spk.get("type")

    # Newer versions commonly provide "address"
    addr = spk.get("address")
    if isinstance(addr, str) and addr:
        return addr, stype

    # Some versions provide "addresses": [...]
    addrs = spk.get("addresses")
    if isinstance(addrs, list) and len(addrs) == 1 and isinstance(addrs[0], str):
        return addrs[0], stype

    return None, stype


def ingest_range(cfg: Dict[str, Any]) -> None:
    rpc = BitcoinRPC(cfg["rpc_url"], cfg["rpc_user"], cfg["rpc_password"])
    conn = connect(cfg["db_path"])
    init_db(conn)

    start_h = int(cfg["start_height"])
    end_h = int(cfg["end_height"])

    for h in tqdm(range(start_h, end_h + 1), desc="Blocks"):
        bhash = rpc.call("getblockhash", [h])
        block = rpc.call("getblock", [bhash, 2])  # verbosity=2 => full tx list
        btime = int(block["time"])

        conn.execute(
            "INSERT OR REPLACE INTO blocks(height, hash, time) VALUES (?, ?, ?)",
            (h, bhash, btime),
        )

        tx_rows = []
        out_rows = []
        in_rows = []

        for t in block["tx"]:
            txid = t["txid"]
            vin = t.get("vin", [])
            vout = t.get("vout", [])

            # Outputs (we can store fully without txindex)
            total_out = 0
            for o in vout:
                vout_n = int(o["n"])
                value_sat = satoshis(float(o["value"]))
                total_out += value_sat

                addr, stype = parse_address(o)
                out_rows.append((txid, vout_n, value_sat, addr, stype, None))

            # Inputs:
            # IMPORTANT: In pruned mode / without txindex, we often cannot fetch prev tx details.
            # So we store only references (prev_txid, prev_vout) and leave address/value NULL.
            for i, inp in enumerate(vin):
                if "coinbase" in inp:
                    in_rows.append((txid, i, None, None, None, None))
                    continue

                prev_txid = inp.get("txid")
                prev_vout = int(inp.get("vout", 0))
                in_rows.append((txid, i, prev_txid, prev_vout, None, None))

            # Without prevout values we cannot compute total_in or fee accurately
            total_in = None
            fee = None

            tx_rows.append((
                txid,
                h,
                len(vin),
                len(vout),
                total_in,             # NULL
                int(total_out),
                fee,                  # NULL
                int(t.get("vsize", 0)),
                int(t.get("locktime", 0)),
            ))

        executemany(
            conn,
            "INSERT OR REPLACE INTO tx(txid, block_height, n_in, n_out, total_in_sat, total_out_sat, fee_sat, vsize, locktime) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tx_rows,
        )
        executemany(
            conn,
            "INSERT OR REPLACE INTO tx_out(txid, vout, value_sat, address, script_type, spent_by) VALUES (?, ?, ?, ?, ?, ?)",
            out_rows,
        )
        executemany(
            conn,
            "INSERT OR REPLACE INTO tx_in(txid, vin, prev_txid, prev_vout, prev_address, prev_value_sat) VALUES (?, ?, ?, ?, ?, ?)",
            in_rows,
        )

        conn.commit()

    conn.close()


if __name__ == "__main__":
    cfg = load_config("config.json")
    ingest_range(cfg)
