# NEAR Demand Ledger

An evidence-first investment thesis for NEAR, built for NEAR HACKATHON, Build Beyond Boundaries (track: `thesis`).

Working hypothesis: cross-chain settlement volume through NEAR Intents is a better leading indicator of real NEAR network demand than token price or raw transaction count. This repo tests that claim with public data and reports what cuts against it too. See [THESIS.md](THESIS.md).

Short version of the findings (11 Nov 2026 snapshots): Intents settled $3.73B in 30 days, up 59% year on year, while mainnet active accounts fell 78% over the same year. Staking pays a real return (4.91% epoch APY against 2.48% measured net inflation). Fees cover 1.88% of net issuance. The hypothesis comes out unproven, and THESIS.md shows the work.

## What it is

A reproducible research package:

- `scripts/fetch_nearblocks.py` pulls daily network stats and the validator snapshot from the public NEARBlocks API (no key).
- `scripts/fetch_rpc.py` pulls validator, status, and protocol-config facts from the public NEAR mainnet RPC (no key).
- `scripts/fetch_defillama.py` pulls DEX and NEAR Intents volume plus Near TVL from the public DefiLlama API (no key).
- `scripts/analyze.py` computes every number quoted in THESIS.md and the dashboard into `data/metrics.json`.
- `scripts/build_charts.py` rebuilds every chart and `dashboard/index.html` from the snapshots in `data/`.
- `dashboard/index.html` is a static dashboard: one section per pillar, with its chart, its source, and a plain reading of what it shows.
- `THESIS.md` holds the claim, the evidence for it, the evidence against it, and what would change our mind.

## Do X, see Y (for judges)

1. Run `bash rebuild.sh`. See: fresh snapshots in `data/`, a regenerated `data/metrics.json`, five rebuilt charts, and a regenerated `dashboard/index.html`.
2. Open `dashboard/index.html` in a browser. See: one section per pillar (real staking yield, active accounts, net supply and fees, Intents and DeFi share), each with its chart and the figures from `data/metrics.json`.
3. Read `THESIS.md`. See: the hypothesis, the numbers that support it, the numbers that do not, and the exact results that would falsify it.

## Data sources (all free, no API key)

- NEARBlocks public API: https://api.nearblocks.io
- NEAR public mainnet RPC: https://rpc.mainnet.near.org
- DefiLlama public API: https://api.llama.fi (its Near DEX overview classifies NEAR Intents as a protocol, which is how Intents volume is measured here)
- NEAR Intents Explorer API: attempted; it requires a partner key, so Intents volume is read from DefiLlama and cross-checked against the Explorer's public dashboard instead (see THESIS.md, Gaps)

## Reproducibility

Every number in THESIS.md and the dashboard comes from a script in `scripts/` reading a snapshot in `data/`. If a metric cannot be computed from these sources, THESIS.md lists it under Gaps instead of estimating it. One transport note: the public RPC sometimes cuts the large `validators` response short; `fetch_rpc.py` asks for gzip, retries, and falls back to curl for that call.

## NEAR tools used

Public NEAR RPC and the NEARBlocks indexer for on-chain data, plus DefiLlama's public API for Intents and DeFi figures. No smart contract was deployed for this project. The thesis track is judged on evidence.

## License

MIT. See [LICENSE](LICENSE).
