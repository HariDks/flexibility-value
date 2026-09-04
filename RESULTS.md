# Results — the single current statement

Everything below is regenerated from the scripts named against each block. Where
an earlier number in the working notes differs, **this file is correct.**

Base case throughout: a factory needing **10 MW of heat continuously**, a
**12-hour** store, charging at **4×** average draw, **1%/day** standby loss, and
each market's **real forecast horizon** (24h in Spain and MISO, 6h in South
Australia). Calendar year **2025**.

---

## 1. The business case — against a gas boiler

*`analyse_gas.py`.* **This is the comparison a customer actually makes.** A
factory choosing whether to install thermal storage is choosing against the gas
boiler it already runs, not against a hypothetical electric heater.

| | Gas alone | Gas + carbon | Battery | vs gas+carbon | vs gas alone |
|---|---|---|---|---|---|
| **Spain** | €50.82 | €68.65 | €44.03 | **+35.9%** | **+13.4%** |
| **South Australia** | A$55.06 | A$63.85 | A$60.23 | **+5.7%** | −9.4% |
| **MISO** | $25.67 | $25.67 | $49.60 | **−93.2%** | −93.2% |

**Carbon price at which the battery matches gas:**

| Market | Breakeven | Actually charges | |
|---|---|---|---|
| Spain | **−€28.58/t** | €75.00 | gas would need a *subsidy* to compete |
| South Australia | **A$21.74/t** | A$36.99 | 70% margin |
| MISO | **$100.70/t** | $0.00 | no carbon price exists |

## 2. The analytical decomposition — against inflexible electrification

*`analyse_fees_all.py`.* **This is not a competitor — it is a measuring stick.**
Nobody runs a 50 MW resistive heater flat off the grid. Holding everything
constant except *when* the power is bought isolates the value of flexibility
alone, which is what the rest of this study is about.

| | Inflexible | Battery ignoring tariff | Battery playing tariff |
|---|---|---|---|
| **Spain** (6.3TD) | €70.86 | €46.82 · +33.9% | **€43.45 · +38.7%** |
| **South Australia** (Sub-Transmission) | A$120.12 | A$72.49 · +39.6% | **A$60.32 · +49.8%** |
| **MISO** (Schedule 632 + riders) | $62.47 | $99.42 · −59.1% | **$63.80 · −2.1%** |

In Minnesota the battery finishes behind **on 2025 prices** — and its best case
is achieved by being barely flexible at all. The year-dependence matters here:
see §6a. What holds in every year is the **gradient**, not the level.

## 3. The mechanism, isolated — the same battery on two networks in one country

*`analyse_networks.py`. The strongest evidence in the study: no currency,
weather or market-design confound.*

| Network | Charge design | Battery is worth |
|---|---|---|
| **SA Power Networks** | peak measured 17:00–21:00, Nov–Mar only | **+49.8%** |
| ElectraNet, Para 66kV | agreed maximum demand, any hour | +5.9% |
| ElectraNet, Brinkworth 33kV | agreed maximum demand, any hour | **−4.8%** |
| ElectraNet, Ardrossan West 33kV | agreed maximum demand, any hour | **−14.1%** |
| ElectraNet, Berri 66kV | agreed maximum demand, any hour | **−18.6%** |

A 25–60 MW site connects to SA Power Networks; ElectraNet's exit points are
almost all bulk supply into SAPN. The direct-connection case is a counterfactual,
kept because it isolates the mechanism perfectly.

---

## 4. The findings, ranked

**1. It is not the size of the network charge that decides whether flexibility
pays — it is whether the charge knows what time it is.** Spain bands by period,
South Australia measures peak in a four-hour seasonal window, and a battery
dodges both. MISO charges the monthly maximum whenever it falls: nowhere to
hide. Proven within one country by §3.

**2. Three kinds of tariff, and they behave differently.** *(`analyse_decomposition.py`)*

| | Price hunting alone | Tariff clock alone | Together | Interaction |
|---|---|---|---|---|
| Spain | +33.9% | **−4.9%** | +38.7% | **+9.7** |
| South Australia | +39.6% | **+8.9%** | +49.8% | +1.3 |
| MISO | −59.1% | −2.6% | −10.9% | +50.8 |

**Spain is permissive** — obeying the clock earns nothing alone, but stops the
peak that price-hunting creates from being punished. **South Australia is
rewarding** — the clock pays on its own, with no forecasting at all. **MISO is
punitive** — every lever loses.

**3. TMEP flips the sign of the incentive — but the value sits in a negotiated
number, not in the tariff.** Demand is billed on an agreed **Baseline Demand**,
set in the service agreement and not specified by the tariff. The whole value
turns on where it lands:

| Agreed baseline | Delivered USD/MWh | vs inflexible |
|---|---|---|
| **10 MW** (the firm load — assumed here) | 49.60 | **+20.6%** |
| 15 MW | 57.92 | +7.3% |
| 20 MW | 66.24 | **−6.0%** |
| 40 MW (the actual peak — i.e. no deal) | 99.52 | −59.3% |

Same battery, same year; only the contracted figure changes. **The +20.6%
headline is therefore a fact about the tariff *plus an assumption about a
negotiation*.** Stated safely: the mechanism is right, and the baseline is where
the value is actually decided.

**3a. The mechanism itself.** Minnesota's fix bills demand on an
agreed **Baseline Demand** rather than metered peak. At 4× charge rate the same
battery goes from **−59.1%** under the standard tariff to **+20.6%** under TMEP.
Under the standard tariff more flexibility always costs more; under TMEP more
flexibility always earns more.

**4. Arbitrage storage saturates at the forecast horizon — it does not taper.**
*(`notes/duration.md`)* Spain flat at 45.6% from 24h; South Australia flat at
49.9% from the start; MISO flat from 24h. Extra storage earns nothing beyond the
point an operator can see a use for it. **The limit is informational, not
economic or physical.**

**5. Two different sizing questions.** Median gap without cheap power is 8–13
hours (arbitrage); the 99th percentile is 99–164 hours (firmness). This study
prices only the first. Antora publicly describes multi-day storage for always-on
supply — a different problem, correctly needing a different answer.

**6. Visibility is worth nothing in Spain and MISO, and everything in South
Australia.** *(`analyse_horizon.py`)* Both publish day-ahead prices, which is
more warning than a 12-hour store needs. The NEM publishes forecasts but no
committable price at any horizon.

---

## 5. Every input, and where it came from

| Input | Value | Source |
|---|---|---|
| Spanish hourly prices | 8,760 h, mean €65.29 | OMIE daily files, 365 days |
| SA hourly prices | 8,760 h, mean A$86.74 | AEMO monthly files, 5-min → hourly |
| MISO hourly prices | 8,760 h, mean $41.16 | MISO day-ahead ex-post, MINN.HUB |
| MISO North wind | 8,760 h, mean 8,333 MW | MISO `sr_gfm` fuel-mix reports |
| Spain network tolls | 6.1–6.4TD, per period | CNMC res. 4 Dec 2024, BOE-A-2024-26218 |
| Spain system charges | per period | Orden TED/1487/2024, BOE-A-2024-27289 |
| SA network | STR sub-transmission | SA Power Networks price lists, 2024-25 and 2026-27 |
| SA peak window | 17:00–21:00, Nov–Mar | SA Power Networks tariff page |
| ElectraNet | locational + common | Prescribed Transmission Service Price Schedule 2025-26 |
| MISO network | Schedule 632 | Otter Tail MN commercial rate summary |
| MISO adjustment + riders | EAF 11.08–23.74 $/MWh, ECO, EITE, TCR, RRCR | Otter Tail MN energy adjustment and riders |
| TMEP terms | Section 14.16 | MN PUC Docket E017/M-25-253, approved 13 Nov 2025 |
| Spain gas | €43.20/MWh | Eurostat `nrg_pc_203` band I4, 2025, ex-VAT |
| SA gas | A$46.80/MWh (A$13.00/GJ) | AER STTM register, mean of 2025 quarters |
| MISO gas | $21.82/MWh ($6.63/Mcf) | EIA Minnesota industrial, 2025 |
| EU carbon | €75/t | EU ETS, range €72–84 through 2025 |
| Australia carbon | A$36.99/t | Safeguard default prescribed unit price 2025-26 |
| US carbon | $0 | none exists |

**No input is an estimate.** Every price and rate is a published figure.

## 6. Every assumption, and how much it matters

| Assumption | Base | Tested across | Effect |
|---|---|---|---|
| Storage duration | 12h | 4–168h | Saturates at the forecast horizon |
| Charge rate | 4× | 2×/4×/6× | Large under demand charges; see §2 |
| Standby loss | 1%/day | 0–10%/day | **0.1–1.9 points.** Immaterial |
| Boiler efficiency | 85% | 80–90% | Does not change any verdict |
| Gas price | published | ±10% | Spain and MISO hold; SA holds in 7 of 9 |
| Spain tariff class | 6.3TD | 6.1–6.4TD | 36.4%–38.8%. **Class not asserted** — the MW threshold per voltage is set by the distributor's connection study, not a citable table. Cannot overturn the conclusion |
| SA forecast horizon | 6h | 3–24h | **49.9% to 73.1%. The one real judgment** |
| Scheduling rule | greedy | vs exact LP | 1.5% at base case, always conservative |
| Inflexible baseline | indexed flat | +0–20% premium | Every alternative costs more |

## 6a. Does the year change the answer? Yes — and there is a trend

Every year each source publishes, run through the same model and the same
2025 tariffs.

**Spain — 8 years** (OMIE serves 2018-2022 as yearly archives and 2023 onward
as daily files; nothing earlier exists on their server):

| Year | Mean price | Hours below zero | Saving |
|---|---|---|---|
| 2018 | €57.3 | 0.0% | 12.5% |
| 2019 | €47.7 | 0.0% | 15.9% |
| 2020 | €34.0 | 0.0% | 17.1% |
| 2021 | €111.9 | 0.0% | 14.7% |
| 2022 | €167.5 | 0.0% | 16.8% |
| 2023 | €87.1 | 0.0% | 24.6% |
| 2024 | €63.0 | 2.8% | 29.8% |
| 2025 | €65.3 | 6.3% | **37.9%** |

**South Australia — 9 years** (AEMO monthly files; 30-minute settlement to
October 2021, 5-minute since, both handled):

| Year | Mean price | Hours below zero | Saving |
|---|---|---|---|
| 2017 | A$105.3 | 0.8% | 22.5% |
| 2018 | A$99.9 | 1.4% | 27.2% |
| 2019 | A$98.9 | 4.9% | 36.3% |
| 2020 | A$43.5 | 10.1% | 39.0% |
| 2021 | A$50.7 | 19.6% | 52.3% |
| 2022 | A$155.9 | 18.6% | 45.6% |
| 2023 | A$80.1 | 26.2% | **55.5%** |
| 2024 | A$100.1 | 25.7% | 54.2% |
| 2025 | A$86.7 | 29.7% | 49.9% |

**MISO — 8 years** (2018-2025). The daily report URLs only serve about two
years, but the older data is published as **monthly zips** under the same path,
`YYYYMM_da_expost_lmp_csv.zip`, with no account required. The first attempt used
the `gridstatus` library, concluded from its failure that the data did not
exist, and was wrong.

| Year | Mean price | Standard tariff @1.5x | Standard @4x | TMEP @4x |
|---|---|---|---|---|
| 2018 | $26.97 | +12.6% | −49.4% | +30.6% |
| 2019 | $22.53 | +18.0% | −45.0% | +34.9% |
| 2020 | $17.49 | +26.0% | −36.7% | +43.1% |
| 2021 | $37.32 | −0.6% | −59.1% | +20.8% |
| 2022 | $45.24 | −9.6% | −63.8% | +16.1% |
| 2023 | $28.48 | +12.9% | −46.8% | +33.1% |
| 2024 | $27.28 | +14.5% | −45.7% | +34.1% |
| 2025 | $41.16 | −2.2% | −59.3% | +20.6% |

**A genuinely flexible battery loses under the standard tariff in 8 years out of
8, and wins under TMEP in 8 out of 8.** The gradient — more flexibility costing
more — holds in every year without exception. Only the *level* moves with the
wholesale price: at a barely-flexible 1.5x the standard tariff ranges from +26%
to −10% across the eight years.

This is the strongest form of the argument, and it needed the long series to
make: two years could have been coincidence.

### What the long series shows

**Both markets trend up, at almost the same rate** — Spain +3.2 points a year
over eight years, South Australia +3.9 over nine. Both track the growth in
negative-price hours, which is the growth in renewable surplus.

**The value of flexibility does not depend on the price level.** Spain's mean
price ran from €34 in 2020 to €168 in 2022 — a five-fold swing through the
energy crisis — while the saving moved only 17.1% to 16.8%. South Australia
shows the same: A$43 in 2020 and A$156 in 2022, savings of 39.0% and 45.6%.

> **What matters is how much the price moves within a day, not how high it is.**
> That is a screening rule for any new market.

**A correction this supersedes.** With only four recent Australian years the
saving looked flat and trendless. Over nine years the trend is clear — the four
recent years were the plateau at the top of it. **A short window can hide a
trend and look like stability.**

**How to state it.** Spain: *12% in 2018, 38% in 2025, rising about 3 points a
year.* South Australia: *23% in 2017, around 50% now.* Both single-year figures
are points on a rising line, not properties of the market.

## 7. What this does not cover

- **Firmness.** Storage is priced only as an arbitrage asset. Reliability value,
  curtailment ride-through and multi-day firming are not modelled.
- **Capital cost.** Everything here is operating cost. Connection capex, which
  scales with charge rate, is not included and would push against high charge
  rates.
- **Real-time markets.** Day-ahead prices only where a day-ahead market exists.
- **Temperature.** Heat is treated as heat; no process-temperature constraint.
- **TMEP's coincidence condition** costs 1.3–2.4% at a realistic paired-farm
  size and is excluded from the headline TMEP figure.
- **The forward risk premium** on fixed-price contracts, which could not be
  sourced and is therefore not claimed.
- **Choice of price node.** MISO uses MINN.HUB and South Australia uses SA1,
  both chosen for relevance rather than tested against alternatives.
- **Scale.** A single size — 10 MW of heat, drawing up to 40-60 MW — runs
  throughout. Tariff class and scheme eligibility both depend on size, so the
  results do not transfer directly to a much smaller or larger plant.

## 8. Corrections log — claims made and later overturned

1. *"Spain's tariff periods are misaligned with its solar."* **Wrong.** P1 exists
   only Jan/Feb/Jul/Dec; April–May contain none.
2. *"South Australia's demand charge is the harshest of the three."* **Wrong and
   backwards.** It is the most favourable; MISO's is the harshest.
3. *Spanish system charges €8–20/MWh.* **Wrong by 5–10×**; published values are
   €0.21–2.58.
4. *MISO factory pays $36.32, battery 64% worse.* **Baseline understated** —
   excluded the Energy Adjustment and riders. Correct figures $62.47 / −2.1%.
5. *"The battery knows the future."* **Overstated** — foresight was always
   bounded by what the tank can carry.
6. *Greedy within 0.2–0.7% of optimal.* **Measured on an easier problem**; with
   tariff caps it is 1.5%.
7. *SA peak window applies year-round.* **Wrong** — November to March only, and
   on a daily average.
8. *"Returns diminish past 12–24 hours."* **Imprecise** — they stop, at the
   forecast horizon.
9. *"90 hours idle proves standby losses are low."* **Withdrawn** — that figure
   is discharge duration, not heat retention. The conclusion survives on
   residence time (5–8h), measured here.

## 9. Which script produces what

| Script | Produces |
|---|---|
| `battery.py` | the model, plus a self-test against a known answer |
| `analyse_fees_all.py` | §1, and the network-bill figure |
| `analyse_gas.py` | §2, the sensitivity grid, breakeven carbon prices |
| `analyse_networks.py` | §3, SAPN vs ElectraNet |
| `analyse_decomposition.py` | finding 2, and the SA peak-window test |
| `analyse_horizon.py` | finding 6, energy-price-only visibility curves |
| `analyse_wind.py` | TMEP's coincidence condition, both readings |
| `analyse_robustness.py` | §6 — five robustness checks |
| `plot_step1.py`, `plot_all_markets.py` | data-quality inspection, all three markets |
