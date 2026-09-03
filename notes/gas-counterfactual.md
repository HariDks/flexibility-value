# The commercial counterfactual: battery versus gas

The flat-electric comparison used elsewhere is the **flexibility-value**
counterfactual — it isolates what timing is worth, and it is a benchmark, not a
competitor. Nobody proposes running a 50 MW resistive heater flat off the grid.

This is the **commercial** counterfactual: what a customer actually chooses
between. Gas at 85% boiler efficiency, plus the carbon price an industrial
emitter genuinely faces.

## Inputs

| Market | Gas price | Source | Carbon price |
|---|---|---|---|
| Spain | EUR 37.40/MWh | industrial delivered, Oct 2025 | EUR 75/t (EU ETS, EUR 72–84 through 2025) |
| South Australia | AUD 43.56/MWh (A$12.10/GJ) | Adelaide STTM 2025 | AUD 36.99/t (Safeguard default prescribed unit price 2025-26) |
| MISO | USD 21.82/MWh ($6.63/Mcf) | EIA Minnesota industrial 2025 | none |

Gas combustion 0.202 tCO2 per MWh of gas burnt.

## Result — cost of delivered heat, 2025

| Market | Gas, no carbon | Carbon adder | Gas, with carbon | Battery (4x, 12h) | Battery vs gas+carbon |
|---|---|---|---|---|---|
| Spain | 44.00 | 17.82 | 61.82 | **48.55** | **+21.5%** |
| South Australia | 51.25 | 8.79 | 60.04 | **61.15** | −1.9% |
| MISO | 25.67 | 0.00 | 25.67 | **49.60** | −93.2% |

**Without a carbon price the battery loses in all three markets** — by 10% in
Spain, 19% in South Australia, 93% in Minnesota.

**With one, Spain flips to a clear win and South Australia to a near-tie.**
Minnesota has no carbon price at all and cheap gas, so nothing closes it.

## The cleanest statement of the result

The carbon price at which delivered heat from a thermal battery matches gas:

| Market | Breakeven carbon price | Actual | |
|---|---|---|---|
| Spain | **EUR 19.16/t** | EUR 75.00 | already ~4x above |
| South Australia | **AUD 41.69/t** | AUD 36.99 | 11% short |
| MISO | **USD 100.70/t** | USD 0.00 | no price exists |

Spain clears its breakeven several times over. South Australia is within about
a tenth of it. Minnesota would need a carbon price higher than almost anywhere
in the world, because its gas is very cheap and its tariff punishes flexibility.

## Sensitivity — charge rate and storage duration

Charge rate as a multiple of average thermal load. The energy balance sets the
floor: 12h of storage serving constant heat needs ~2x if charging spreads over
the other 12 hours, ~4x to concentrate into 6 hours, ~6x into 4 hours. So the
multiple is a *design choice about how tightly to concentrate charging*, not a
property of the technology.

**Spain (EUR/MWh)** — gas with carbon 61.82

| charge | 6h | 12h | 24h | 48h |
|---|---|---|---|---|
| 2x | 61.35 | 57.22 | 54.87 | 54.87 |
| 4x | 59.29 | **48.55** | 42.91 | 42.91 |
| 6x | 60.10 | 48.50 | 40.37 | 40.37 |

**South Australia (AUD/MWh)** — gas with carbon 60.04

| charge | 6h | 12h | 24h | 48h |
|---|---|---|---|---|
| 2x | infeasible | infeasible | infeasible | infeasible |
| 4x | 61.15 | **61.15** | 61.15 | 61.15 |
| 6x | 61.19 | 61.19 | 61.19 | 61.19 |

**MISO under TMEP (USD/MWh)** — gas 25.67

| charge | 6h | 12h | 24h | 48h |
|---|---|---|---|---|
| 2x | 54.57 | 52.70 | 52.05 | 52.05 |
| 4x | 53.34 | **49.60** | 47.82 | 47.82 |
| 6x | 53.21 | 49.14 | 46.53 | 46.53 |

### Two structural findings fall out of that grid

**In South Australia, storage duration does not matter at all.** Every duration
gives the same answer, because with only ~6 hours of forward price visibility
the battery cannot plan further ahead than that however large its tank. **The
useful tank size is capped by information, not by economics** — a direct
consequence of the NEM having no day-ahead market. Building beyond about six
hours in South Australia buys nothing until forecasting improves.

**South Australia also has a minimum charge rate.** At 2x the schedule is
infeasible: the battery cannot fill up before the four-hour peak-window blackout
it must avoid. The tariff sets a floor on how fast you must be able to charge.

Neither of these appears anywhere else, and neither is about prices.

---

## How solid are the inputs?

Mixed, and worth being explicit.

**Well sourced.** Minnesota gas ($6.63/Mcf — EIA's published annual industrial
price for the state, right customer class, right year). Australian carbon
(A$36.99/t — the Safeguard Mechanism's official default prescribed unit price
for 2025-26). US carbon (zero). Gas emissions factor (0.202 tCO2/MWh, standard
inventory figure).

**Estimated, and two are weak.** Spain's gas price is an **October 2025** figure
applied to the whole year. Australia's is a **September 2025** Adelaide STTM
figure, also annualised — and it is a *wholesale hub* price, so it understates
what a factory actually pays once transport and margin are added. Neither annual
series could be retrieved: Eurostat's `nrg_pc_203` and the AER's gas price
register both need interactive queries rather than a fetchable file.

**Assumed.** Boiler efficiency 85% (industrial steam boilers run 80-90%), and
the EU carbon price at EUR 75/t, chosen from a sourced range of 72-84.

## What that uncertainty does to the conclusions

Breakeven carbon price — the price at which gas costs the same as the battery —
across gas prices ±25% and boiler efficiency 80/90%:

| Market | Breakeven range | Actual | Verdict |
|---|---|---|---|
| Spain | −57 to +57 | **EUR 75** | wins in every combination |
| MISO | 61 to 140 | **USD 0** | loses in every combination |
| South Australia | −31 to +107 | **AUD 37** | **flips** with the assumptions |

**Spain and MISO are robust.** No combination of the weak inputs changes either
answer, and neither is close. With the corrected 6.3TD tariff class Spain's
battery matches gas at a carbon price near **zero** — competitive on fuel cost
alone, before any climate policy.

**South Australia is genuinely marginal and should not be quoted precisely.**
Reporting it as "0.3% behind gas" implies a confidence the inputs do not
support. The defensible statement is that South Australia sits close to the
line and where it falls depends on the delivered gas price, which could not be
sourced.

Two mitigations worth noting. The breakeven framing does not use the assumed
carbon price at all — it derives what is needed and compares. And the weak
inputs mostly understate gas, which works against the battery, so Spain and
South Australia are if anything better than shown.

---

## Spain's gas price, closed properly

The October-2025 figure has been replaced with the real annual series, pulled
from **Eurostat `nrg_pc_203`** via its open API — band **I4** (100,000–999,999
GJ/yr, the right size: our factory burns about 371,000 GJ), averaged across both
half-years of 2025, excluding VAT.

| Band | 2025-S1 | 2025-S2 | 2025 average |
|---|---|---|---|
| I3 (10,000–99,999 GJ) | 0.0513 | 0.0508 | 0.0510 |
| **I4 (100,000–999,999 GJ)** | **0.0472** | **0.0393** | **0.0432** |
| I5 (1,000,000–3,999,999 GJ) | 0.0481 | 0.0390 | 0.0435 |

**EUR 43.20/MWh**, against the EUR 37.40 previously assumed — gas is **16% more
expensive** than estimated, so the battery looks better, not worse.

### What it does to the Spanish result

| | Before (estimate) | After (Eurostat) |
|---|---|---|
| Gas, no carbon price | 44.00 | **50.82** |
| Gas with EU ETS | 61.82 | **68.65** |
| Battery | 44.03 | 44.03 |
| **Battery vs gas alone** | dead level | **13.4% cheaper** |
| **Battery vs gas + carbon** | 28.8% cheaper | **35.9% cheaper** |
| **Breakeven carbon price** | ~0 | **−EUR 28.58/t** |

A negative breakeven means gas would need a **subsidy** of about EUR 29 per
tonne of CO2 to match the battery. In Spain, on published 2025 prices and the
correct tariff class, **thermal storage beats gas outright — climate policy is
upside, not the thing holding it up.**

### South Australia — still open

The Adelaide STTM annual average could not be retrieved: the AER's register is
unreachable programmatically, AEMO's data page returns 403, and nemweb keeps
only 30 days live. On the September-2025 estimate the breakeven is AUD 37.78/t
against an actual 36.99 — about 2% short, which is well inside the uncertainty.
**Still too close to call, and the delivered gas price decides it.**
