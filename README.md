# flexibility-value

What is a thermal battery's ability to wait for cheap electricity actually worth
— and what decides whether any of it reaches the bill?

A study across three electricity markets: **Spain**, **South Australia**, and the
**US Midwest (MISO)**, using published 2025 hourly prices and published network
tariffs throughout.

**Read [`PROJECT_PLAN.md`](PROJECT_PLAN.md) first** for scope and the list of
things deliberately not being done.

## The findings

**It is not the size of the network charge that decides whether flexibility
pays — it is whether the charge knows what time it is.** Spain bands its charges
by period, South Australia measures peak demand in a four-hour window, and a
battery dodges both. MISO charges the monthly maximum whenever it falls, so
there is nowhere to hide and flexibility is actively penalised.

The clearest proof is inside a single country: the same battery in South
Australia is worth **+49.8% on SA Power Networks** and **−4.8% to −18.6%
connected directly to ElectraNet**. No currency, weather or market-design
confound — only the design of the demand charge.

**Against gas**, the second policy variable appears. The carbon price at which
delivered heat from a battery matches a gas boiler is **EUR 19/t in Spain**
(actual: 75), **AUD 42 in South Australia** (actual: 37), and **USD 101 in
Minnesota** (actual: zero).

Detail and sources: [`notes/fees.md`](notes/fees.md),
[`notes/gas-counterfactual.md`](notes/gas-counterfactual.md),
[`notes/wind-coincidence.md`](notes/wind-coincidence.md),
[`notes/resolution.md`](notes/resolution.md).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Running it

Data first — each step caches, so re-running is cheap:

```bash
python src/fetch_omie.py --year 2025      # Spain, one file per day
python src/load_omie.py --year 2025
python src/fetch_aemo.py --year 2025      # South Australia, monthly files
python src/load_aemo.py  --year 2025
python src/fetch_miso.py --year 2025      # MISO prices, via gridstatus
python src/load_miso.py  --year 2025
python src/fetch_miso_wind.py --year 2025 # MISO fuel mix, for the wind rule
python src/load_miso_wind.py  --year 2025
```

Then the analysis, in any order:

```bash
python src/battery.py                # self-test: reproduces a known answer
python src/plot_step1.py             # Spain: year heatmap, extreme weeks
python src/plot_all_markets.py       # SA and MISO: the same visual QA
python src/analyse_spain.py          # first result, energy price only
python src/analyse_all.py            # all three, energy price only
python src/analyse_horizon.py        # what price visibility is worth
python src/analyse_spain_tariff.py   # Spain with the network bill
python src/analyse_fees_all.py       # all three with the network bill
python src/analyse_decomposition.py  # price-hunting vs tariff clock
python src/analyse_gas.py            # the commercial counterfactual
python src/analyse_networks.py       # SA Power Networks vs ElectraNet
python src/analyse_wind.py           # TMEP's wind-coincidence condition
python src/analyse_robustness.py     # five robustness checks
```

## Layout

```
src/battery.py     the charging model, with a self-test
src/tariff.py      every published tariff, with its source cited inline
src/fetch_*.py     data collection, cached
src/load_*.py      tidy hourly series, with data-quality checks
src/analyse_*.py   the analyses above
notes/             findings, sources, and corrections
explainer/         an interactive explainer of the mechanism
data/, output/     downloaded and generated (not committed)
```

## Reading the results critically

- Every rate comes from a published source, cited in `src/tariff.py`.
- Where an input could not be sourced, the claim is scoped rather than
  estimated — see the forward-premium note in `notes/fees.md`.
- Assumptions that move the answer are swept, not asserted: charge rate,
  storage duration, standby loss, tariff class, forward visibility.
- Claims made during the work and later disproven are recorded in
  `notes/fees.md` rather than quietly deleted.

The one input that remains a judgment is **South Australia's usable forward
visibility**. AEMO publishes 5-minute pre-dispatch an hour ahead and 30-minute
pre-dispatch to ~40 hours, but these are deterministic point forecasts with no
confidence intervals — not, as in Spain and MISO, a price you can commit at. The
NEM has no day-ahead market, so there is no committable price at any horizon.
The usable horizon is therefore a forecasting capability rather than a market
fact. Six hours is the base case; `analyse_robustness.py` reports the range.
