#!/usr/bin/env python3
"""Compute every number quoted in THESIS.md and the dashboard from the raw
snapshots in data/, and write data/metrics.json. Stdlib only.

Rule: if a number cannot be computed from a snapshot, it is not written here
and THESIS.md lists it as a gap instead.
Usage: python3 scripts/analyze.py
"""
import csv
import json
import math
import os
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")
YOCTO = 1e24


def load_csv():
    with open(os.path.join(DATA, "nearblocks_daily.csv")) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("near_price", "market_cap", "txns", "new_accounts",
                  "active_accounts", "active_contracts", "txn_fee_usd"):
            r[k] = float(r[k]) if r.get(k) else 0.0
        for k in ("total_supply", "circulating_supply", "txn_fee", "gas_fee", "txn_volume"):
            r[k] = float(r[k]) / YOCTO if r.get(k) else 0.0
        r["day"] = r["date"][:10]
    return rows


def avg(rows, key):
    return sum(r[key] for r in rows) / len(rows) if rows else 0.0


def linregress(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return slope, intercept, r2


def main():
    rows = load_csv()
    m = {"snapshot_daily_last_day": rows[-1]["day"], "daily_rows": len(rows)}

    # ---------- Pillar 1: staking / real yield ----------
    vals = json.load(open(os.path.join(DATA, "rpc_validators.json")))["result"]
    cur = vals["current_validators"]
    total_stake = sum(int(v["stake"]) for v in cur) / YOCTO
    stakes = sorted((int(v["stake"]) for v in cur), reverse=True)
    stats = json.load(open(os.path.join(DATA, "nearblocks_stats.json")))["stats"][0]
    total_supply_now = float(stats["total_supply"]) / YOCTO
    cfg = json.load(open(os.path.join(DATA, "rpc_protocol_config.json")))["result"]
    num, den = cfg["max_inflation_rate"]
    nbv = json.load(open(os.path.join(DATA, "nearblocks_validators.json")))
    apy = float(nbv["lastEpochApy"])
    # measured net inflation: total supply growth over the last 365 daily rows
    s_now, s_yr = rows[-1]["total_supply"], rows[-366]["total_supply"]
    net_inflation_365 = (s_now / s_yr - 1) * 100
    m["staking"] = {
        "validators": len(cur),
        "total_stake_near": round(total_stake),
        "total_supply_near": round(total_supply_now),
        "staked_share_pct": round(100 * total_stake / total_supply_now, 1),
        "top10_share_pct": round(100 * sum(stakes[:10]) / sum(stakes), 1),
        "max_inflation_pct": 100 * num / den,
        "last_epoch_apy_pct_nb": apy,
        "net_inflation_365d_pct": round(net_inflation_365, 2),
        "real_yield_pct": round((1 + apy / 100) / (1 + net_inflation_365 / 100) * 100 - 100, 2),
        "apy_ceiling_pct": round(100 * (num / den) * total_supply_now / total_stake, 2),
        "epoch_length_blocks": cfg["epoch_length"],
    }

    # ---------- Pillar 2: active accounts / Metcalfe ----------
    monthly = defaultdict(list)
    for r in rows:
        monthly[r["day"][:7]].append(r)
    months = sorted(monthly)
    pts = []
    for mo in months:
        rs = monthly[mo]
        act, mc = avg(rs, "active_accounts"), avg(rs, "market_cap")
        if act > 0 and mc > 0:
            pts.append((mo, act, mc))
    slope, intercept, r2 = linregress([math.log10(p[1]) for p in pts],
                                      [math.log10(p[2]) for p in pts])
    last30, yr30 = rows[-31:-1], rows[-396:-366]
    m["activity"] = {
        "metcalfe_months": len(pts),
        "metcalfe_slope": round(slope, 2),
        "metcalfe_r2": round(r2, 2),
        "actives_30d_avg": round(avg(last30, "active_accounts")),
        "actives_30d_avg_year_ago": round(avg(yr30, "active_accounts")),
        "txns_30d_avg": round(avg(last30, "txns")),
        "txns_30d_avg_year_ago": round(avg(yr30, "txns")),
        "new_accounts_30d_avg": round(avg(last30, "new_accounts")),
        "new_accounts_30d_avg_year_ago": round(avg(yr30, "new_accounts")),
        "price_snapshot": float(stats["near_price"]),
        "market_cap_snapshot": float(stats["market_cap"]),
        "total_txns_cumulative": int(float(stats["total_txns"])),
    }
    # structural break check: mean txns Mar 2026 vs Apr 2026
    mar = [r for r in rows if r["day"].startswith("2026-03")]
    apr = [r for r in rows if r["day"].startswith("2026-04")]
    if mar and apr:
        m["activity"]["break_mar2026_txns"] = round(avg(mar, "txns"))
        m["activity"]["break_apr2026_txns"] = round(avg(apr, "txns"))

    # ---------- Pillar 3: net supply / fees ----------
    last365 = rows[-366:-1]
    fees365 = sum(r["txn_fee"] for r in last365)
    dsupply = rows[-1]["total_supply"] - rows[-366]["total_supply"]
    s90a = (rows[-1]["total_supply"] / rows[-91]["total_supply"]) ** (365 / 90) - 1
    m["supply_fees"] = {
        "supply_now_near": round(rows[-1]["total_supply"]),
        "supply_365d_ago_near": round(rows[-366]["total_supply"]),
        "net_new_near_365d": round(dsupply),
        "net_inflation_90d_annualized_pct": round(s90a * 100, 2),
        "fees_near_365d": round(fees365),
        "fees_near_30d_avg_per_day": round(avg(last30, "txn_fee")),
        "fees_pct_of_net_issuance": round(100 * fees365 / dsupply, 2) if dsupply else None,
        "fees_usd_30d_avg_per_day": round(avg(last30, "txn_fee_usd")),
    }

    # ---------- Pillar 4: Intents & DeFi (DefiLlama) ----------
    dl = json.load(open(os.path.join(DATA, "defillama_dexs_near.json")))
    breakdown = dl.get("totalDataChartBreakdown") or []
    # Last two days are partial (adapter backfill lag) — drop them.
    full = breakdown[:-2] if len(breakdown) > 2 else breakdown

    def series(name):
        out = []
        for ts, per in full:
            v = per.get(name)
            if isinstance(v, list):
                v = v[0]
            if v:
                out.append((ts, float(v)))
        return out

    def total_series():
        return [(ts, sum((x[0] if isinstance(x, list) else x) or 0
                          for x in per.values())) for ts, per in full]

    import datetime

    def day(ts):
        return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")

    intents = series("NEAR Intents")
    totals = total_series()
    win_i = intents[-30:]
    win_t = totals[-30:]
    yr_i = intents[-395:-365]
    tvl = json.load(open(os.path.join(DATA, "defillama_near_chain.json")))
    protos = {p["name"]: p for p in dl.get("protocols") or []}
    m["intents_defi"] = {
        "source_note": "DefiLlama overview/dexs/near breakdown; last 2 days dropped as partial",
        "intents_first_day": day(intents[0][0]) if intents else None,
        "intents_avg_per_day_30d": round(sum(v for _, v in win_i) / len(win_i)),
        "intents_sum_30d": round(sum(v for _, v in win_i)),
        "intents_avg_per_day_year_ago_30d": round(sum(v for _, v in yr_i) / len(yr_i)) if yr_i else None,
        "intents_share_of_near_dex_30d_pct": round(
            100 * sum(v for _, v in win_i) / sum(v for _, v in win_t), 1),
        "near_dex_total_30d": round(sum(v for _, v in win_t)),
        "rhea_dex_30d": round((protos.get("Rhea Dex") or {}).get("total30d") or 0),
        "near_tvl_usd": round(tvl[0]["tvl"]) if tvl else None,
        "window_end": day(win_i[-1][0]) if win_i else None,
    }
    fees_path = os.path.join(DATA, "defillama_intents_fees.json")
    if os.path.exists(fees_path):
        fees_dl = json.load(open(fees_path))
        m["intents_defi"]["intents_fees_30d_usd"] = round(fees_dl.get("total30d") or 0)
    summary_path = os.path.join(DATA, "defillama_intents_summary.json")
    if os.path.exists(summary_path):
        summ = json.load(open(summary_path))
        m["intents_defi"]["intents_volume_all_time_usd"] = round(summ.get("totalAllTime") or 0)
    proto_path = os.path.join(DATA, "defillama_intents_protocol.json")
    if os.path.exists(proto_path):
        ctv = json.load(open(proto_path)).get("currentChainTvls") or {}
        m["intents_defi"]["intents_tvl_total_usd"] = round(sum(ctv.values()))
        m["intents_defi"]["intents_tvl_on_near_usd"] = round(ctv.get("Near") or 0)

    with open(os.path.join(DATA, "metrics.json"), "w") as f:
        json.dump(m, f, indent=2)
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
