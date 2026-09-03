# Two different sizing questions

This study prices storage as an **arbitrage** asset: how much does a tank pay
for itself by shifting *when* power is bought. On that basis returns diminish
past roughly 12-24 hours.

That is not the only reason to build storage, and it is a narrower question than
the one a real product answers. Antora publicly describes **multi-day** storage
built to turn intermittent power into always-on supply — longer than this
study's base case, and for a different purpose.

Their own wording, from [antora.com/technology](https://www.antora.com/technology):

> "**MULTI-DAY THERMAL STORAGE** — The carbon blocks store energy at temperatures
> up to 2,400°C… Carbon's high thermal conductivity enables ultra-fast charging
> that rapidly soaks up the cheapest hours of electricity generation… Energy is
> discharged **around the clock** as heat."

and from [antora.com](https://www.antora.com/):

> "Reliable — **Multi-day storage delivers always-on heat and power** where
> downtime is not an option."

> "1 **Intermittent, Low-Cost Energy** → 2 Energy Stored as Heat in Carbon Blocks
> → 3 **Always-on Heat and Power at Any Scale**"

**No specific hour figure is used anywhere in this study**, because none was
found in a citable public source. "Multi-day" is what Antora states, and it is
enough: it is already several times this study's 12-hour base case.

**Both answers are correct; they answer different questions.**

- **~12 hours** — how much storage pays for itself by buying cheaper
- **Multi-day** — how much storage it takes to make an intermittent supply firm

## The same public data gives both

Length of stretches with no cheap power available, where "cheap" is each
market's own 30th percentile for 2025:

| Market | Median gap | 90th pct | 99th pct | Longest |
|---|---|---|---|---|
| Spain | **11h** | 42h | **164h** | 301h |
| South Australia | **13h** | 42h | **139h** | 187h |
| MISO | **8h** | 24h | **99h** | 350h |

The **median** gap is 8-13 hours — which is why a 12-hour tank captures most of
the arbitrage value, confirmed here independently of the cost model.

The **99th percentile** is 99-164 hours. A supplier promising firm heat has to
cover that, and no amount of arbitrage logic gets you there.

## This model does not price firmness at all

Two consequences worth stating in any write-up:

1. **The diminishing-returns finding applies to arbitrage only.** It should not
   be read as "do not build longer than 24 hours." It means longer storage does
   not pay for itself *on price shifting* — a different claim.

2. **A deep store cannot use its depth on price signals anyway.** Tested
   directly: against MISO's 24-hour published horizon, no tank size up to 336
   hours could be operated against a hard availability constraint. Depth is
   unusable for price optimisation beyond the forecast horizon — which is
   independent evidence, from public data, that multi-day depth exists for
   firmness rather than arbitrage.

Storage duration in practice is therefore set by the **availability promised to
the customer**, and the arbitrage value is what you collect along the way.

## A terminology note

"Duration" means **usable stored energy divided by discharge power** — how long
it can keep supplying. It is *not* how long the store can sit idle without
losing heat. Standing thermal loss is a separate parameter entirely.

This study's loss sensitivity (immaterial below ~10%/day) addresses the second;
nothing here bears on the first.
