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
