# flexibility-value

What is a thermal battery's ability to wait for cheap electricity actually worth
— and what decides whether any of it reaches the bill?

A study across three electricity markets: **Spain**, **South Australia**, and the
**US Midwest (MISO)**, built entirely from published hourly prices and published
network tariffs. **25 market-years**: Spain 2018–2025, South Australia 2017–2025,
MISO 2018–2025.

**[`RESULTS.md`](RESULTS.md) is the single source of truth.** Where any other
file, note or commit message disagrees with it, it is correct. Every number in
it regenerates from `src/results.py` and the analysis scripts.

## The finding

**It is not the size of the network charge that decides whether flexibility
pays — it is whether the charge knows what time it is.**

A charge levied per unit of energy is neutral. A charge levied on your peak
punishes a battery, which by design draws hard in short bursts. But a peak
charge measured *inside a stated window* can simply be avoided, while one
measured at your worst moment, whenever it falls, cannot.

**A battery can dodge a window. It cannot dodge "whenever."**

The cleanest evidence sits inside one country, where two network operators bill
the same load two different ways:

| 2025, South Australia | saving |
|---|---|
| **SA Power Networks** — peak measured 17:00–21:00, November to March | **+49.9%** |
| **ElectraNet** — agreed maximum demand, any hour, all year (best of four locations) | **+20.7%** |

Same prices, same weather, same year, same battery, same currency. SA Power
Networks beats the best ElectraNet location **by 19 to 44 points in every one of
nine years**.

## What flexibility is worth

Against an inflexible electrification counterfactual — the same factory buying
the same power as it burns it:

| | range | trend |
|---|---|---|
| **Spain** (6.3TD, 24h visibility) | 12.5% → 37.9% over 8 years | +3.2 pts/yr |
| **South Australia** (Sub-Transmission, 6h visibility) | 22.5% → 55.5% over 9 years | +3.9 pts/yr |
| **MISO** (Schedule 632 + riders) | **negative in all 8 years** | — |
| **MISO under TMEP** | **positive in all 8 years** | — |

MISO is the control case: a time-blind demand charge takes more than the cheap
power saves. Otter Tail's **Thermal Market Energy Pricing** tariff bills demand
on an agreed *Baseline Demand* instead of the metered peak, and flips the sign.

## Against gas — the comparison a customer actually makes

2025, the year for which gas and carbon prices were sourced:

| | gas + carbon | battery | | carbon price where they tie | actually charged |
|---|---|---|---|---|---|
| **Spain** | €68.65 | €44.03 | **+35.9%** | **−€28.58/t** | €75.00 |
| **South Australia** | A$63.85 | A$60.23 | **+5.7%** | **A$21.74/t** | A$36.99 |
| **MISO** | $25.67 | $49.60 | **−93.2%** | **$100.70/t** | $0.00 |

Spain's breakeven is negative: gas would need to be *paid* to emit before it
caught up. MISO's gas is cheap enough that no carbon price in prospect closes
the gap.

## Reading this critically

- **Every rate is published and cited inline** in `src/tariff.py`.
- **[`DECISIONS.md`](DECISIONS.md) lists all 44 decisions** made in the work,
  tagged published / tested / judgment, with the 18 judgment calls marked and
  the three most challengeable named.
- **Assumptions that move the answer are swept, not asserted**: charge rate,
  storage duration, standby loss, tariff class, forward visibility, demand
  profile, pricing point, TMEP baseline.
- **Where an input could not be sourced, the question is inverted** rather than
  guessed — the answer is the threshold at which it would change the conclusion.
  That is why connection capex reads "it would have to exceed €293–493/kW" and
  the carbon comparison reads as a breakeven.
- **Fourteen claims made during the work and later overturned are logged** in
  [`RESULTS.md`](RESULTS.md) §8 rather than quietly deleted. Several made the
  result more conservative.

The largest remaining judgment is **South Australia's usable forward
visibility**. The NEM has no day-ahead market, so there is no committable price
at any horizon; AEMO publishes deterministic pre-dispatch forecasts with no
confidence intervals. Six hours is the base case and the answer runs 49.9% to
73.1% across the tested range. `analyse_forecast_skill.py` measures what real
published forecasts actually deliver: **37% of perfect foresight at 6 hours,
54% at 8, 80% at 12.**

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Running it

Data first — every step caches, so re-running is cheap. Prices are not
committed (115 MB); these rebuild them.

```bash
python src/fetch_omie.py --year 2025            # Spain, one file per day
python src/load_omie.py  --year 2025
python src/fetch_aemo.py --year 2025 --region SA1
python src/load_aemo.py  --year 2025 --region SA1
python src/fetch_miso.py --year 2025            # 2023+, via gridstatus
python src/fetch_miso_archive.py --start 2018 --end 2022   # older years
python src/load_miso.py  --year 2025
```

Then the analysis:

```bash
python src/battery.py                  # self-test: reproduces a known answer
python src/results.py                  # every headline number, every year
python src/analyse_gas.py              # the commercial counterfactual
python src/analyse_networks.py         # SA Power Networks vs ElectraNet
python src/analyse_decomposition.py    # price-hunting vs tariff clock
python src/analyse_robustness.py       # greedy vs exact LP, and four more
python src/analyse_horizon.py          # what price visibility is worth
python src/analyse_forecast_skill.py   # what REAL forecasts deliver
python src/analyse_nodes.py            # does the pricing point matter?
python src/analyse_demand_profile.py   # weekends, turnarounds, shift patterns
python src/analyse_firmness.py         # what capacity markets pay for depth
python src/analyse_connection_capex.py # the connection-cost break-even
python src/analyse_wind.py             # TMEP's wind-coincidence condition
```

## Layout

```
RESULTS.md         the single current statement of every number
DECISIONS.md       all 44 decisions, with the judgment calls marked
PROJECT_PLAN.md    scope, and what is deliberately not being done
src/battery.py     the charging model, with self-tests
src/tariff.py      every published tariff, source cited inline
src/fetch_*.py     data collection, cached
src/load_*.py      tidy hourly series, with data-quality checks
src/analyse_*.py   the analyses above
notes/             findings and sources, one file per question
explainer/         an interactive explainer of the mechanism
data/, output/     downloaded and generated (not committed)
```

## Method

No econometrics — the counterfactual here is constructible, so it does not need
to be estimated. The machinery is an inventory-scheduling heuristic benchmarked
against an exact linear program (1.5% from optimal at the base case, and always
conservative), a factorial decomposition with interaction terms, run-length
analysis for storage sizing, and breakeven inversion wherever an input could not
be sourced.
