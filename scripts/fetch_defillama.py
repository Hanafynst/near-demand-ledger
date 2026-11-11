#!/usr/bin/env python3
"""Fetch NEAR DEX + Intents volume and chain TVL from the public DefiLlama API
(no key needed) and save raw snapshots under data/. Stdlib only.

DefiLlama classifies "NEAR Intents" as a DEX protocol on the Near chain, which
makes Intents settlement volume publicly measurable here even though the
Intents Explorer API itself requires a partner JWT.
Usage: python3 scripts/fetch_defillama.py
"""
import json
import os
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
UA = {"User-Agent": "near-demand-ledger/0.1 (hackathon research)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    dexs = get("https://api.llama.fi/overview/dexs/near"
               "?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=false")
    with open(os.path.join(DATA_DIR, "defillama_dexs_near.json"), "w") as f:
        json.dump(dexs, f)
    print("dexs total24h:", dexs.get("total24h"), "protocols:",
          [p.get("name") for p in (dexs.get("protocols") or [])][:10])

    chains = get("https://api.llama.fi/v2/chains")
    near = [c for c in chains if c.get("name") == "Near"]
    with open(os.path.join(DATA_DIR, "defillama_near_chain.json"), "w") as f:
        json.dump(near, f, indent=2)
    print("Near TVL (USD):", near[0].get("tvl") if near else None)

    summary = get("https://api.llama.fi/summary/dexs/near-intents")
    with open(os.path.join(DATA_DIR, "defillama_intents_summary.json"), "w") as f:
        json.dump(summary, f)
    print("NEAR Intents volume totalAllTime (USD):", summary.get("totalAllTime"))

    fees = get("https://api.llama.fi/summary/fees/near-intents")
    with open(os.path.join(DATA_DIR, "defillama_intents_fees.json"), "w") as f:
        json.dump(fees, f)
    print("NEAR Intents fees total30d (USD):", fees.get("total30d"))

    proto = get("https://api.llama.fi/protocol/near-intents")
    keep = {"currentChainTvls": proto.get("currentChainTvls"),
            "chains": proto.get("chains"), "methodology": proto.get("methodology")}
    with open(os.path.join(DATA_DIR, "defillama_intents_protocol.json"), "w") as f:
        json.dump(keep, f, indent=2)
    print("NEAR Intents TVL by chain (USD):", keep["currentChainTvls"])


if __name__ == "__main__":
    main()
