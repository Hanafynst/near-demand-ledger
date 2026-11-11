#!/usr/bin/env python3
"""Fetch staking/supply facts from the public NEAR mainnet RPC (no key needed)
and save raw snapshots under data/. Stdlib only.
Usage: python3 scripts/fetch_rpc.py
"""
import gzip
import http.client
import json
import os
import time
import urllib.request

RPC = "https://rpc.mainnet.near.org"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _rpc_curl(body):
    """Fallback transport via curl, used only if urllib keeps getting its
    connection cut. Same endpoint, same payload."""
    import shutil
    import subprocess
    if not shutil.which("curl"):
        return None
    out = subprocess.run(
        ["curl", "-s", "--compressed", "-m", "60", "-X", "POST", RPC,
         "-H", "Content-Type: application/json", "--data-binary", "@-"],
        input=body, capture_output=True, timeout=90)
    if out.returncode != 0 or not out.stdout:
        return None
    return json.loads(out.stdout.decode("utf-8"))


def rpc(method, params, attempts=3):
    """One JSON-RPC call with retries. The public RPC occasionally closes a
    large response early (http.client.IncompleteRead on `validators`, whose
    plain response is ~367 KB); asking for gzip shrinks it to ~99 KB and a
    fresh attempt normally succeeds."""
    body = json.dumps({"jsonrpc": "2.0", "id": "x", "method": method, "params": params}).encode()
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(RPC, data=body, headers={
                "Content-Type": "application/json", "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except (http.client.IncompleteRead, ConnectionError, TimeoutError, OSError) as e:
            last = e
            print(f"  retry {i + 1}/{attempts} after {type(e).__name__}")
            time.sleep(2 * (i + 1))
    via_curl = _rpc_curl(body)
    if via_curl is not None:
        print("  urllib kept failing; curl fallback succeeded")
        return via_curl
    raise RuntimeError(f"RPC {method} failed after {attempts} attempts: {last}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    status = rpc("status", [])
    with open(os.path.join(DATA_DIR, "rpc_status.json"), "w") as f:
        json.dump(status, f, indent=2)
    chain_id = status.get("result", {}).get("chain_id")
    print("chain_id:", chain_id)

    validators = rpc("validators", [None])
    with open(os.path.join(DATA_DIR, "rpc_validators.json"), "w") as f:
        json.dump(validators, f, indent=2)
    cur = validators.get("result", {}).get("current_validators", [])
    total_stake = sum(int(v.get("stake", 0)) for v in cur)
    print("current validators:", len(cur), "total stake (yocto):", total_stake)

    # Protocol config carries the inflation parameters the yield math needs.
    # Note: the method wants a single-key map ({"finality": "final"}), and
    # max_inflation_rate sits at the top level of the result, as [num, denom].
    cfg = rpc("EXPERIMENTAL_protocol_config", {"finality": "final"})
    with open(os.path.join(DATA_DIR, "rpc_protocol_config.json"), "w") as f:
        json.dump(cfg, f, indent=2)
    mir = cfg.get("result", {}).get("max_inflation_rate")
    print("max_inflation_rate:", mir)


if __name__ == "__main__":
    main()
