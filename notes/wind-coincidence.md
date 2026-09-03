# TMEP's wind-coincidence condition: how binding?

TMEP requires the customer to "take service coincident with and not to exceed
the hourly generating output of a nearby specifically identified wind and/or
solar generation resource that is not owned by the Company."

Output for one named plant is not public, so **MISO North-region hourly wind
generation** stands in — North covers Minnesota and the Dakotas, where Big Stone
sits. Source: MISO's `sr_gfm` generation fuel mix reports, 365 days of 2025,
8,760 hours with no gaps.

**Caveat that matters:** a region is far smoother than a single farm. Regional
wind never hit zero in 2025 (minimum 95 MW against a mean of 8,333). A single
plant does. So this proxy **understates** how binding the condition is.

## The wind resource itself

Mean 8,333 MW, range 95 to 18,351. Windiest hour of the day is **00:00**,
calmest is **10:00** — the nocturnal pattern that matches MISO's 03:00 price
trough exactly.

Wind and price are negatively correlated at **−0.324**. Mean price is
**USD 30.72/MWh when wind is in its top quartile** against **53.14 in the
bottom**. So charging on wind and charging on price mostly want the same hours.
That is why the condition turns out to be survivable.

## Two readings of the condition, and they differ enormously

### A. Applied to the whole load — infeasible

If the battery may draw **only** what the paired farm is producing, the schedule
cannot be made feasible at any storage size tested, up to 720 hours. The reason
is the length of the lulls:

| Paired farm size | Mean output | Hours below the factory's 10 MW | Longest unbroken run |
|---|---|---|---|
| 1x battery's annual energy | 10.0 MW | 52% | **229 h** |
| 2x | 20.0 MW | 26% | **121 h** |
| 3x | 30.0 MW | 15% | 65 h |
| 5x | 50.0 MW | 7% | 35 h |
| 8x | 80.0 MW | 3% | 25 h |

A 121-hour lull cannot be bridged by any thermal store anyone would build. Under
this reading the product does not work.

### B. Applied as TMEP actually bills it — a 1-2% haircut

The tariff bills in **two tiers**: energy up to the agreed Baseline Demand at the
utility's own rate, and energy above it at MISO prices. Modelled that way — firm
service always available to 10 MW, extra draw capped by the paired farm's output:

| Paired farm size | Cost USD/MWh | Cost of the condition | Hours constrained |
|---|---|---|---|
| 1x battery annual energy | 56.61 | 6.1% | 100% |
| 2x | 54.66 | **2.4%** | 74% |
| 3x | 54.08 | **1.3%** | 52% |
| 5x | 53.69 | 0.6% | 32% |
| 8x | 53.50 | 0.2% | 18% |

For reference: TMEP price-following with no wind condition is USD 53.37/MWh,
against USD 62.47 for the inflexible electrification counterfactual.

## The finding

**The two-tier structure is not incidental — it is what makes wind-pairing
physically possible at all.** Applied to the whole load the condition is
unsatisfiable; applied only to the incremental market-priced portion it costs
one to two percent at a realistically sized farm.

This is exactly the physical-versus-commercial distinction that needed checking.
It resolves in favour of the commercial reading, and the tariff's own bill
determination is the evidence.

**Remaining uncertainty:** the regional proxy is smoother than a single plant,
so the real haircut is larger than 1-2% — how much larger depends on the named
resource, which is project-specific. The direction of the finding is unaffected:
under reading B the condition is a cost, not a barrier.
