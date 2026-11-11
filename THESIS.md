# NEAR Demand Ledger: an investment thesis, tested

Track: Investment Thesis (`thesis`), NEAR HACKATHON 2026 (Build Beyond Boundaries).

Snapshot dates. NEARBlocks daily panel through 10 Nov 2026 (2,304 daily rows from 21 Jul 2020). NEAR RPC snapshot taken 11 Nov 2026 at block 224,002,004. DefiLlama pulled 11 Nov 2026; volume windows use the 30 full days ending 9 Nov 2026, with the last two partial days dropped. Activity windows are the 30 days ending 9 Nov 2026, compared with the same 30 days a year earlier. Run `bash rebuild.sh` to regenerate every figure from the snapshots in `data/`; `scripts/analyze.py` writes them to `data/metrics.json`.

## The hypothesis

Settlement volume through NEAR Intents is a better leading indicator of real demand for NEAR than the token price or the mainnet transaction count. If that holds, Intents volume should already be large and growing, and mainnet usage, staking, and fees should follow it with a lag.

## Verdict

The evidence splits cleanly in two, and the halves disagree.

Intents is large and still growing. It settled $3,727,751,510 in the 30 days ending 9 Nov 2026, an average of $124,258,384 a day, up 59% from $77,935,548 a day in the same window a year earlier. Staking economics also hold up: a 4.91% epoch APY against 2.48% measured net supply inflation, a real yield of about 2.37%.

Mainnet's own series moved the other way over the same year. Daily active accounts fell 78%, transactions fell 85%, new accounts fell 96%. Fees cover 1.88% of net issuance. After 23 months of Intents data, the series that would confirm a leading indicator have not followed. We rate the hypothesis unproven: the demand is measurable in Intents settlement and absent from the chain's own counters.

## Evidence for

1. Intents volume, size and growth. DefiLlama's daily series for NEAR Intents starts 10 Dec 2024. The 30 full days ending 9 Nov 2026 sum to $3,727,751,510 ($124,258,384 a day), against $77,935,548 a day a year earlier. Cross-check: the public Intents Explorer dashboard showed a 30 day total of $3,727,751,509 when read on 11 Nov 2026, one dollar from the sum we computed out of DefiLlama's daily breakdown. Cumulative volume reads $37,171,767,218 on DefiLlama and $38.11B on the Explorer; the methods differ, the recent window agrees.
2. Intents dominates exchange activity attributed to Near. In the same 30 days it was 92.6% of the $4,024,785,541 of DEX-classified volume on Near in DefiLlama's overview. Rhea, the largest native DEX, recorded $288,871,260 in 30 days. Intents settled roughly 13 times that.
3. Intents earns fees and holds capital. Fees were $5,458,382 over the trailing 30 days (DefiLlama fees summary, pulled 11 Nov 2026). Value locked in Intents contracts is $184,004,347 across 26 chains, with $91,749,436 of it on Near (DefiLlama protocol page).
4. Staking pays a real return. The RPC snapshot counts 338 current validators and 581,233,869 NEAR staked, 44.3% of the 1,311,369,535 NEAR supply. NEARBlocks reports 4.91% APY for the last completed epoch. The protocol formula in the NEAR documentation (a reward budget of 2.5% of supply, 10% of it to the protocol treasury) implies about 5.08% at a 44.3% staking ratio, before unearned rewards and pool commissions. The reported 4.91% sits just under that figure.
5. Supply policy tightened on schedule and the chain data shows it. The live protocol config (version 88) sets `max_inflation_rate` to 1/40, or 2.5% a year. The cut from 5% reached mainnet around 30 Oct 2025 with protocol version 81, per the nearcore economics spec and the NEAR Foundation and NEAR One posts of Oct 2025. Measured net supply inflation is 2.48% over the last 365 days and 2.50% annualized over the last 90 days.

## Evidence against

1. Mainnet usage fell hard. Thirty day averages, NEARBlocks daily panel: active accounts 58,223 a day against 262,972 a year earlier; transactions 662,520 against 4,444,290; new accounts 9,573 against 220,745.
2. Price and usage decoupled. The daily panel has NEAR at $3.03 on 10 Nov 2025 and $3.62 on 10 Nov 2026, a 19% rise across a year in which active accounts fell 78%. The statistics snapshot read on 11 Nov 2026 puts market cap at $4,772,415,789.
3. The Metcalfe fit is weak. A monthly log-log regression of market cap on daily active accounts across 73 months gives a slope of 0.21 and an R² of 0.28. A Metcalfe-style relationship would put the slope near 2. In this sample, market cap pays little attention to the account count.
4. The activity series breaks in April 2026. Average daily transactions went from 3,479,269 in March 2026 to 946,610 in April 2026. New accounts went from about 135,000 a day in March to about 22,000 a day in April. A step that size in one month means the indexer changed how it counts, or a very large source of activity switched off. Public sources do not say which. Comparisons that cross April 2026 carry the break inside them. The months after the break (May to Nov 2026) still show activity flat to falling, so the decline does not rest on the break alone.
5. Fees are too small to fund anything. Total transaction fees over the last 365 days were 596,325 NEAR, against 31,740,869 NEAR of net new supply: 1.88%. Protocol version 87 removed the 30% contract rebate on gas, so in the current version (88) all gas is burned. Burning every NEAR of fees would still offset under 2% of issuance. Staking rewards come from issuance, and the NEAR documentation states the reward rate does not vary with fees collected.
6. Stake is concentrated. The 10 largest validators hold 36.3% of total stake.

## What would change our mind

- Intents' 30 day average falling below the year-ago level of $77.9M a day for two consecutive months would end the growth claim.
- Mainnet active accounts recovering above 150,000 a day for a full quarter, alongside Intents growth, would mean the series move together and the leading-indicator framing adds nothing.
- A public, keyless count of distinct Intents end users (rather than volume) that grows with volume would strengthen the demand reading a great deal. Volume alone cannot separate end users from solver and market maker flow.
- Real yield turning negative for a full quarter, with epoch APY below net supply inflation, would remove the staking leg of the thesis.

## Gaps

- The Intents Explorer API needs a partner key. `explorer.near-intents.org/api/v0` returned HTTP 400 without one, and keys are issued through partners.near-intents.org. We used DefiLlama's adapter series for the time series and the Explorer's public dashboard total as a cross-check.
- The cause of the April 2026 break in the NEARBlocks activity series is unresolved, as described in point 4 of the evidence against.
- DefiLlama and the Explorer disagree on cumulative Intents volume by about $0.94B ($37.17B against $38.11B). Their 30 day figures match to within a dollar, so we lean on the recent window.
- Daily active accounts count accounts, not people, and we have no retention or cohort data. The June 2024 monthly average was about 1.99M active accounts a day, a level that points to heavy automated or farming activity in the older data. That cuts both ways: the fall since then may overstate lost human users, and the Metcalfe regression inherits the same problem.

## Method and sources

- `scripts/fetch_nearblocks.py`: NEARBlocks public API, daily panel, network statistics, validator snapshot (carries the last epoch APY of 4.91%).
- `scripts/fetch_rpc.py`: NEAR public mainnet RPC, chain status, current validators, protocol config (`max_inflation_rate` 1/40, `epoch_length` 43,200 blocks, protocol version 88).
- `scripts/fetch_defillama.py`: DefiLlama public API, Near DEX overview with per-protocol breakdown, NEAR Intents volume and fees summaries, Intents protocol TVL by chain, Near chain TVL of $169,269,941.
- `scripts/analyze.py`: computes every figure quoted here into `data/metrics.json`.
- `scripts/build_charts.py`: builds the five SVG charts and this dashboard page from the same snapshots.
- Protocol facts: nearcore economics spec (github.com/near/nearcore, protocol-model/spec/economics.md), docs.near.org validator and gas pages, NEAR Foundation and NEAR One posts on the Oct 2025 halving, all read 11 Nov 2026.
