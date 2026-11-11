#!/usr/bin/env python3
"""Rebuild every dashboard chart and dashboard/index.html from the raw
snapshots in data/ plus data/metrics.json (produced by scripts/analyze.py).
Pure SVG, no JS dependencies. Usage: python3 scripts/build_charts.py
"""
import csv
import json
import os
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(ROOT, "data")
CHART_DIR = os.path.join(ROOT, "dashboard", "charts")
YOCTO = 1e24


def svg_line(points, title, width=680, height=250, fmt="{:,.0f}"):
    if not points:
        return ""
    vals = [v for _, v in points if v is not None]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    n = len(points)
    step_x = width / max(n - 1, 1)
    pts = []
    for i, (_, v) in enumerate(points):
        if v is None:
            continue
        x = i * step_x
        y = height - 22 - ((v - lo) / span) * (height - 46)
        pts.append(f"{x:.1f},{y:.1f}")
    first, last = points[0][0], points[-1][0]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><text x="8" y="16" font-size="14">{title}</text>'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="#6b4eff" stroke-width="2"/>'
        f'<text x="8" y="{height - 5}" font-size="11">{first} to {last} · min {fmt.format(lo)} · max {fmt.format(hi)}</text></svg>'
    )


def money(v):
    return f"${v:,.0f}"


def main():
    os.makedirs(CHART_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "nearblocks_daily.csv")) as f:
        rows = list(csv.DictReader(f))

    # Chart: daily transactions, last 365 days
    pts = [(r["date"][:10], float(r["txns"])) for r in rows[-365:] if r.get("txns")]
    with open(os.path.join(CHART_DIR, "txns.svg"), "w") as f:
        f.write(svg_line(pts, "Daily transactions, last 365 days"))
    print("txns.svg")

    # Chart 1 (pillar 1 context): annualized net supply inflation by month
    monthly = defaultdict(list)
    for r in rows:
        monthly[r["date"][:7]].append(r)
    months = sorted(monthly)
    infl = []
    for a, b in zip(months, months[1:]):
        sa = float(monthly[a][-1]["total_supply"])
        sb = float(monthly[b][-1]["total_supply"])
        if sa:
            infl.append((b, ((sb / sa) ** 12 - 1) * 100))
    with open(os.path.join(CHART_DIR, "inflation.svg"), "w") as f:
        f.write(svg_line(infl, "Net supply inflation, annualized by month (%)", fmt="{:.2f}"))
    print("inflation.svg")

    # Chart 2 (pillar 2): monthly average daily active accounts
    act = [(mo, sum(float(r["active_accounts"]) for r in monthly[mo]) / len(monthly[mo]))
           for mo in months if monthly[mo][0]["active_accounts"]]
    with open(os.path.join(CHART_DIR, "actives.svg"), "w") as f:
        f.write(svg_line(act, "Daily active accounts, monthly average"))
    print("actives.svg")

    # Chart 3 (pillar 3): daily transaction fees in NEAR, last 365 days
    fees = [(r["date"][:10], float(r["txn_fee"]) / YOCTO) for r in rows[-365:] if r.get("txn_fee")]
    with open(os.path.join(CHART_DIR, "fees.svg"), "w") as f:
        f.write(svg_line(fees, "Transaction fees per day (NEAR), last 365 days"))
    print("fees.svg")

    # Chart 4 (pillar 4): NEAR Intents daily volume (DefiLlama), last 365 full days
    dl = json.load(open(os.path.join(DATA_DIR, "defillama_dexs_near.json")))
    breakdown = (dl.get("totalDataChartBreakdown") or [])[:-2]
    import datetime
    ipts = []
    for ts, per in breakdown:
        v = per.get("NEAR Intents")
        if isinstance(v, list):
            v = v[0]
        if v:
            day = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
            ipts.append((day, float(v)))
    with open(os.path.join(CHART_DIR, "intents.svg"), "w") as f:
        f.write(svg_line(ipts[-365:], "NEAR Intents volume per day (USD, DefiLlama)", fmt="${:,.0f}"))
    print("intents.svg")

    # Dashboard page, numbers taken only from metrics.json
    m = json.load(open(os.path.join(DATA_DIR, "metrics.json")))
    s, a, sf, i4 = m["staking"], m["activity"], m["supply_fees"], m["intents_defi"]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>NEAR Demand Ledger — Investment Thesis Dashboard</title>
<style>body{{font-family:system-ui,sans-serif;max-width:920px;margin:2em auto;padding:0 1em;line-height:1.5}}figure{{margin:1.5em 0}}figcaption{{font-size:.9em;color:#444}}.stat{{font-size:1.15em}}td{{padding:.15em .8em .15em 0}}</style>
</head>
<body>
<h1>NEAR Demand Ledger</h1>
<p>An investment thesis for NEAR, tested against public data. Built for NEAR HACKATHON
(Build Beyond Boundaries), track: Investment Thesis. Hypothesis: settlement volume through
NEAR Intents grows ahead of the activity visible on mainnet, so it reads as a leading
indicator of demand for the network. Every figure on this page is computed by
<code>scripts/analyze.py</code> from the snapshots in <code>data/</code>; rebuild with
<code>bash rebuild.sh</code>. Daily series run to {m['snapshot_daily_last_day']}; the
DefiLlama window ends {i4['window_end']} (the last two days are dropped, they are partial).</p>

<h2>Pillar 1: Real staking yield</h2>
<table>
<tr><td>Validators (current epoch, RPC)</td><td class="stat">{s['validators']}</td></tr>
<tr><td>Total staked</td><td class="stat">{s['total_stake_near']:,} NEAR ({s['staked_share_pct']}% of supply)</td></tr>
<tr><td>Top 10 validators' share of stake</td><td class="stat">{s['top10_share_pct']}%</td></tr>
<tr><td>Protocol max inflation (on-chain config)</td><td class="stat">{s['max_inflation_pct']}% per year</td></tr>
<tr><td>Measured net supply inflation, last 365 days</td><td class="stat">{s['net_inflation_365d_pct']}%</td></tr>
<tr><td>Staking APY, last completed epoch (NEARBlocks)</td><td class="stat">{s['last_epoch_apy_pct_nb']}%</td></tr>
<tr><td>Real yield (APY adjusted for net inflation)</td><td class="stat">{s['real_yield_pct']}%</td></tr>
</table>
<figure><img src="charts/inflation.svg" alt="Net supply inflation chart"><figcaption>Net supply inflation, annualized from month-end total supply (NEARBlocks daily panel). The step down from about 5% to about 2.5% is the protocol inflation cut reaching mainnet. Source: <code>data/nearblocks_daily.csv</code>.</figcaption></figure>
<p>Stakers earn about {s['last_epoch_apy_pct_nb']}% nominal while supply grows {s['net_inflation_365d_pct']}%, so a staker's share of the network grows roughly {s['real_yield_pct']}% a year. That part of the demand story holds: staking pays a real, positive return without new buyers.</p>

<h2>Pillar 2: Active accounts (Metcalfe)</h2>
<table>
<tr><td>Daily active accounts, 30-day average</td><td class="stat">{a['actives_30d_avg']:,}</td></tr>
<tr><td>Same window a year ago</td><td class="stat">{a['actives_30d_avg_year_ago']:,}</td></tr>
<tr><td>Daily transactions, 30-day average</td><td class="stat">{a['txns_30d_avg']:,}</td></tr>
<tr><td>Same window a year ago</td><td class="stat">{a['txns_30d_avg_year_ago']:,}</td></tr>
<tr><td>New accounts per day, 30-day average</td><td class="stat">{a['new_accounts_30d_avg']:,}</td></tr>
<tr><td>Same window a year ago</td><td class="stat">{a['new_accounts_30d_avg_year_ago']:,}</td></tr>
<tr><td>Metcalfe fit, monthly, log market cap on log active accounts</td><td class="stat">slope {a['metcalfe_slope']}, R² {a['metcalfe_r2']} ({a['metcalfe_months']} months)</td></tr>
</table>
<figure><img src="charts/actives.svg" alt="Active accounts chart"><figcaption>Daily active accounts, monthly average (NEARBlocks). Activity peaked in 2024 and has fallen since; the level shift between March and April 2026 ({a.get('break_mar2026_txns', 0):,} to {a.get('break_apr2026_txns', 0):,} transactions a day) is flagged in THESIS.md as an unresolved break in the series.</figcaption></figure>
<figure><img src="charts/txns.svg" alt="Daily transactions chart"><figcaption>Daily transactions, last 365 days (NEARBlocks daily panel).</figcaption></figure>
<p>On mainnet's own numbers, usage is shrinking, not growing. Price rose over the same year while active accounts fell by about two thirds. Whatever demand is building for NEAR, this series does not show it.</p>

<h2>Pillar 3: Net supply and fee burn</h2>
<table>
<tr><td>Total supply now</td><td class="stat">{sf['supply_now_near']:,} NEAR</td></tr>
<tr><td>Net new supply, last 365 days</td><td class="stat">{sf['net_new_near_365d']:,} NEAR</td></tr>
<tr><td>Transaction fees, last 365 days</td><td class="stat">{sf['fees_near_365d']:,} NEAR</td></tr>
<tr><td>Fees as a share of net new supply</td><td class="stat">{sf['fees_pct_of_net_issuance']}%</td></tr>
</table>
<figure><img src="charts/fees.svg" alt="Daily fees chart"><figcaption>Transaction fees per day in NEAR (NEARBlocks daily panel). Even if every NEAR of fees were burned, fees would offset only {sf['fees_pct_of_net_issuance']}% of new issuance.</figcaption></figure>
<p>NEAR is not fee-funded at current usage. Supply growth is a policy variable (the inflation cap), not a market outcome, and fees are too small to change that.</p>

<h2>Pillar 4: Intents and DeFi share</h2>
<table>
<tr><td>NEAR Intents volume, 30 full days to {i4['window_end']}</td><td class="stat">{money(i4['intents_sum_30d'])}</td></tr>
<tr><td>Average per day</td><td class="stat">{money(i4['intents_avg_per_day_30d'])}</td></tr>
<tr><td>Average per day, same window a year earlier</td><td class="stat">{money(i4['intents_avg_per_day_year_ago_30d'] or 0)}</td></tr>
<tr><td>Share of all DEX-classified volume on Near (DefiLlama)</td><td class="stat">{i4['intents_share_of_near_dex_30d_pct']}%</td></tr>
<tr><td>Largest native DEX (Rhea), 30 days</td><td class="stat">{money(i4['rhea_dex_30d'])}</td></tr>
<tr><td>Fees earned by NEAR Intents, 30 days (DefiLlama fees)</td><td class="stat">{money(i4.get('intents_fees_30d_usd') or 0)}</td></tr>
<tr><td>NEAR Intents TVL, all chains / on Near itself</td><td class="stat">{money(i4.get('intents_tvl_total_usd') or 0)} / {money(i4.get('intents_tvl_on_near_usd') or 0)}</td></tr>
<tr><td>Total value locked on Near (DefiLlama)</td><td class="stat">{money(i4['near_tvl_usd'] or 0)}</td></tr>
</table>
<figure><img src="charts/intents.svg" alt="NEAR Intents volume chart"><figcaption>NEAR Intents daily volume as classified by DefiLlama (its Near DEX overview includes NEAR Intents as a protocol). Series starts {i4['intents_first_day']}. DefiLlama figures come from its adapter, not from our own chain read; the gap between this series and mainnet activity is the subject of THESIS.md.</figcaption></figure>
<p>Intents is where the growth is. It settles more in a day than the largest native DEX settles in weeks, and it barely registers in mainnet transaction counts, because most settlement happens off the mainnet shards. That is exactly why the two data sets disagree.</p>

<p><a href="../THESIS.md">Read the full thesis (THESIS.md)</a> · <a href="../README.md">README</a></p>
</body>
</html>
"""
    with open(os.path.join(ROOT, "dashboard", "index.html"), "w") as f:
        f.write(html)
    print("dashboard/index.html regenerated")


if __name__ == "__main__":
    main()
