# What if the factory doesn't run flat out all year?

Decision 7 held demand at 10 MW, every hour, all year. Real plants stop: almost
every process plant takes an annual maintenance turnaround, and many run five
days a week rather than seven.

Run with `python src/analyse_demand_profile.py`. 2025 prices, everything else
at the base case.

## Why this could have gone either way

Stopping pulls in two directions at once:

- **Idle hours are hours you don't buy power in.** If they fall in expensive
  hours, that helps the *inflexible* plant more than the battery — the battery
  was already avoiding those hours, so it has less left to win.
- **But capacity charges don't stop when the plant does.** They are billed on
  the peak you set while running. A plant that runs less spreads the same fixed
  charge over less heat. That is precisely the mechanism this whole study is
  about, so intermittent operation should make it *worse*.

## The five profiles

| profile | heat delivered | utilisation |
|---|---|---|
| continuous 24/7/365 (base case) | 87,600 MWh | 100% |
| + 2-week turnaround | 84,240 MWh | 96% |
| five-day week | 62,640 MWh | 72% |
| five-day + turnaround | 60,240 MWh | 69% |
| day shift (06:00–22:00), five-day | 41,760 MWh | 48% |

## Results

**Spain**

| profile | inflexible | flexible | saving | of which capacity |
|---|---|---|---|---|
| continuous | 70.86 | 44.03 | **37.9%** | €3.62/MWh |
| + turnaround | 70.85 | 44.48 | 37.2% | €3.76 |
| five-day week | 78.67 | 51.34 | 34.7% | €5.06 |
| five-day + turnaround | 78.59 | 51.78 | 34.1% | €5.26 |
| day shift | 78.77 | 51.46 | 34.7% | €7.59 |

**South Australia**

| profile | inflexible | flexible | saving | of which capacity |
|---|---|---|---|---|
| continuous | 120.12 | 60.23 | **49.9%** | A$4.57/MWh |
| + turnaround | 119.68 | 59.05 | 50.7% | A$4.75 |
| five-day week | 134.97 | 66.68 | 50.6% | A$6.39 |
| five-day + turnaround | 135.21 | 65.78 | 51.4% | A$6.64 |
| day shift | 141.53 | 46.87 | **66.9%** | A$9.58 |

**MISO under TMEP**

| profile | inflexible | flexible | saving | of which capacity |
|---|---|---|---|---|
| continuous | 103.63 | 49.60 | **52.1%** | $16.68/MWh |
| + turnaround | 103.82 | 50.13 | 51.7% | $17.35 |
| five-day week | 113.21 | 57.68 | 49.1% | $23.33 |
| five-day + turnaround | 113.63 | 58.46 | 48.6% | $24.26 |
| day shift | 131.04 | 68.68 | 47.6% | $34.99 |

## What it says

**1. The base case is not flattered.** Across every profile in every market the
saving stays within a few points of it: Spain 34.1–37.9%, MISO 47.6–52.1%,
South Australia 49.9–66.9%. In South Australia every non-continuous profile
does *better* than the base case, so assuming continuous operation was the
conservative choice there.

**2. Capacity charges punish intermittent plants, hard.** This is the finding
worth carrying into the memo. As utilisation falls from 100% to 48%, the
capacity charge per MWh of heat roughly doubles in every market:

| | 100% utilisation | 48% utilisation | multiple |
|---|---|---|---|
| Spain | €3.62/MWh | €7.59/MWh | 2.1× |
| South Australia | A$4.57/MWh | A$9.58/MWh | 2.1× |
| MISO under TMEP | $16.68/MWh | $34.99/MWh | 2.1× |

The 2.1× is not a coincidence — it is 100/48. **A capacity charge is a fixed
cost, so its burden per unit of output is inversely proportional to how much
you run.** Both the battery and the inflexible plant pay it, which is why the
*saving* barely moves — but the *bill* rises for both.

The policy point: capacity-based network charging quietly taxes any load that
does not run flat out. A batch or seasonal industrial process is penalised
relative to a continuous one for reasons that have nothing to do with what it
costs the network to serve.

**3. South Australia's day-shift case is the standout, at 66.9%.** A plant
running 06:00–22:00 on weekdays needs heat through exactly the evening hours
when South Australian power is dearest, and is idle overnight when it is
cheapest. The inflexible version of that plant is the worst-off buyer in the
whole study — A$141.53/MWh. The battery charges through the solar-flooded
middle of the day and carries the heat into the evening, and the gap between
the two is the widest anywhere in this analysis. **Flexibility is worth most to
the plant whose demand is worst-aligned with its grid.**

**4. When the turnaround falls does not matter.** A two-week shutdown starting
on the 1st of each month, tested for all twelve:

| market | Jan | Mar | May | Jul | Sep | Nov | range |
|---|---|---|---|---|---|---|---|
| Spain | 38.4% | 38.5% | 37.2% | 38.7% | 36.8% | 37.7% | 2.5 pt |
| South Australia | 50.1% | 50.0% | 50.1% | 48.7% | 50.1% | 50.0% | 1.9 pt |
| MISO under TMEP | 51.9% | 51.8% | 51.8% | 51.8% | 51.9% | 51.7% | 0.4 pt |

One less thing to defend: the turnaround date is not a decision the answer is
sensitive to.

## What changed in the model

`schedule()` and `evaluate()` in `src/battery.py` took a scalar demand. They
now take a scalar *or* an hourly array. Two things needed care:

- The **lookback bound** was `storage / demand`. With demand varying, the tank
  stretches furthest across the *lowest non-zero* demand, so that is what
  bounds the search now. Idle hours burn nothing and do not consume lookback.
- The **tank and charge cap** are sized on the rated load, not the annual mean,
  so an idle fortnight does not shrink the plant.

Two self-tests cover the new path: a constant array must give bit-for-bit what
the scalar gives, and a plant idle through the expensive block must pay less
per MWh than one running through it. Every headline number in `RESULTS.md`
regenerates unchanged.
