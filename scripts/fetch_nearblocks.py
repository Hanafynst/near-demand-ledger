#!/usr/bin/env python3
"""Fetch daily NEAR network stats from the public NEARBlocks API (no key needed)
and save raw snapshots under data/. Stdlib only.
Usage: python3 scripts/fetch_nearblocks.py
"""
import csv
import json
import os
import urllib.request

BASE = "https://api.nearblocks.io/v1"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
UA = {"User-Agent": "near-demand-ledger/0.1 (hackathon research)"}


def get(path):
    req = urllib.request.Request(BASE + path, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    stats = get("/stats")
    with open(os.path.join(DATA_DIR, "nearblocks_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print("stats keys:", sorted(stats.keys()) if isinstance(stats, dict) else type(stats))

    # NOTE: /v1/charts/txns is 404. The daily panel lives at /v1/charts (no suffix)
    # and already contains txns, active_accounts, market_cap, supplies, fees, etc.
    daily = get("/charts")
    rows = daily if isinstance(daily, list) else daily.get("charts", daily)
    cols = ["date", "near_price", "market_cap", "total_supply", "circulating_supply",
            "blocks", "gas_fee", "txns", "txn_volume", "txn_fee", "txn_fee_usd",
            "new_accounts", "active_accounts", "active_contracts"]
    out = os.path.join(DATA_DIR, "nearblocks_daily.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({c: row.get(c) for c in cols})
    print("daily rows:", len(rows), "->", out)

    # Validators snapshot: carries lastEpochApy + total stake as a cross-check
    # on the RPC staking numbers.
    vals = get("/validators")
    with open(os.path.join(DATA_DIR, "nearblocks_validators.json"), "w") as f:
        json.dump(vals, f, indent=2)
    if isinstance(vals, dict):
        print("validators: lastEpochApy:", vals.get("lastEpochApy"),
              "currentValidators:", vals.get("currentValidators"))


if __name__ == "__main__":
    main()
