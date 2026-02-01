import sqlite3
from typing import Iterable, Tuple, Any

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS blocks (
  height INTEGER PRIMARY KEY,
  hash TEXT NOT NULL,
  time INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tx (
  txid TEXT PRIMARY KEY,
  block_height INTEGER,
  n_in INTEGER,
  n_out INTEGER,
  total_in_sat INTEGER,
  total_out_sat INTEGER,
  fee_sat INTEGER,
  vsize INTEGER,
  locktime INTEGER
);

CREATE TABLE IF NOT EXISTS tx_out (
  txid TEXT,
  vout INTEGER,
  value_sat INTEGER,
  address TEXT,
  script_type TEXT,
  spent_by TEXT,
  PRIMARY KEY(txid, vout)
);

CREATE TABLE IF NOT EXISTS tx_in (
  txid TEXT,
  vin INTEGER,
  prev_txid TEXT,
  prev_vout INTEGER,
  prev_address TEXT,
  prev_value_sat INTEGER,
  PRIMARY KEY(txid, vin)
);

CREATE INDEX IF NOT EXISTS idx_tx_block ON tx(block_height);
CREATE INDEX IF NOT EXISTS idx_out_addr ON tx_out(address);
CREATE INDEX IF NOT EXISTS idx_in_prev_addr ON tx_in(prev_address);
CREATE INDEX IF NOT EXISTS idx_out_spent_by ON tx_out(spent_by);
"""

def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

def executemany(conn: sqlite3.Connection, sql: str, rows: Iterable[Tuple[Any, ...]]) -> None:
    conn.executemany(sql, rows)
