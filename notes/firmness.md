# What does firmness cost, and does anything pay for it?

Decision 4 priced storage as an arbitrage asset only and said reliability value
and multi-day firming were "not modelled". This models the economics of them.

Run with `python src/analyse_firmness.py`.

## Why this needs no reliability simulation

The physics is trivial: **a tank holding N hours of heat rides through an
N-hour interruption.** There is no distribution to estimate and no outage model
to build — duration *is* the answer.

What is not trivial, and is what an analyst actually needs, is the economics:
**who pays for hour 25 through hour 100?** That question is answerable entirely
from published auction results, and the answer is nobody.

## 1. What the energy market pays for depth

The marginal value of each extra MWh of tank, per year, at each market's real
forecast horizon:

**Spain** (24-hour horizon)

| tank | cost/MWh | worth of the step | per extra MWh of tank |
|---|---|---|---|
| 4h | €58.92 | | |
| 8h | €50.47 | €740,086/yr | €18,502 |
| 12h | €44.03 | €564,410/yr | €14,110 |
| 24h | €38.56 | €478,913/yr | €3,991 |
| 48h | €38.56 | **€0** | **€0** |
| 96h | €38.56 | €0 | €0 |
| 168h | €38.56 | €0 | €0 |

**MISO under TMEP** (24-hour horizon)

| tank | cost/MWh | worth of the step | per extra MWh of tank |
|---|---|---|---|
| 4h | $55.58 | | |
| 8h | $51.75 | $335,897/yr | $8,397 |
| 12h | $49.60 | $188,562/yr | $4,714 |
| 24h | $47.82 | $155,274/yr | $1,294 |
| 48h+ | $47.82 | **$0** | **$0** |

**South Australia** (6-hour horizon) saturates immediately: 8h and 168h both
deliver at A$60.23. A 4-hour tank is **infeasible** — the strategy blocks
charging for the four-hour evening peak window, and a four-hour tank cannot
bridge its own blackout. That is a nice incidental result: *the tariff sets a
minimum viable tank size.*

## 2. What capacity and demand-response products pay

**MISO Planning Resource Auction**, annualised, Local Resource Zones 1–7
(Zone 1 is Minnesota and the Dakotas):

| planning year | $/MW-day | 10 MW earns | per MWh of heat |
|---|---|---|---|
| 2025/26 | $217.00 | $792,050/yr | **$9.04** |
| 2026/27 | $126.19 | $460,594/yr | **$5.26** |

Source: MISO's own results postings. 2025/26 cleared summer $666.50, fall
$91.60 (North/Central), winter $33.20, spring $69.88. 2026/27 cleared summer
$424.30 for LRZ 1–7, fall $33.92, winter $35.97, spring $7.61.

**The duration MISO requires is four consecutive hours** — "the expected
minimum runtime for these resources", from MISO's own LMR whitepaper (January
2025).

**Spain, SRAD** (Servicio de Respuesta Activa de la Demanda). Availability is
auctioned per MW per assigned hour; activation is paid separately at the
balancing price.

| auction | €/MW-h | assigned hours | 10 MW earns | per MWh of heat |
|---|---|---|---|---|
| 2025 | €56.43 | 4,371 | €2,466,555 | €28.16 |
| 2026 H1 | €65.00 | 2,279 | €1,481,350 | €33.82 |

Source: Red Eléctrica's ESIOS result notes for the auctions of 14 November 2024
and 28 November 2025. The notes give the price as "€/MW"; that it is per
assigned *hour* is confirmed by 56.43 × 4,371 = €246,655/MW-year, which is the
annual figure quoted in the trade press.

**Those SRAD figures are an upper bound and must not be quoted bare.** SRAD pays
for a *reduction against a metered baseline*, and a load can only shed what it
is drawing. Measured over the 4,371 dearest hours of 2025, the battery is
drawing its full 10 MW in only **32.6%** of them and averages **5.42 MW**. So
the realistic range is roughly **€9.18 to €15.25 per MWh of heat, not €28.16**.
A battery actually paid to be available would reschedule itself to be drawing
when called, which is not modelled here — so the true figure sits somewhere
inside that range and above its floor.

**The NEM has no capacity market.** It is energy-only. A flexible load
monetises itself through the spot price, which this study already counts, or
through the Wholesale Demand Response Mechanism, which also settles at the spot
price. **South Australia pays nothing extra for firmness.**

## 3. The wedge nobody pays for

Stretches with no cheap power available, 2025, cheap being each market's own
30th percentile:

| market | median | 99th percentile | longest |
|---|---|---|---|
| Spain | 11h | 164h | 301h |
| South Australia | 13h | 139h | 187h |
| MISO | 8h | 99h | 350h |

**Three numbers answer three different questions:**

| | |
|---|---|
| **4 hours** | what MISO's capacity market requires — and pays for |
| **24 hours** | where arbitrage value stops, set by the day-ahead horizon |
| **99–164 hours** | what covering the 99th-percentile stretch takes |

**Everything between 24 and 164 hours earns nothing from any market in this
study.** It is bought by the customer's own requirement for heat that does not
stop.

### What that unpaid depth costs

Going from a 24-hour tank to a 100-hour one is 760 MWh of extra storage on a
10 MW plant. Annualised at 8% over 20 years:

| storage capex | extra capex | annualised | per MWh of heat |
|---|---|---|---|
| $5/kWh | $3.8m | $387,220 | $4.42 |
| $10/kWh | $7.6m | $774,440 | $8.84 |
| $20/kWh | $15.2m | $1,548,880 | $17.68 |
| $50/kWh | $38.0m | $3,872,200 | $44.20 |

Storage capex is not sourced here — it is Antora's number, not a published one
— so it is swept rather than assumed, the same treatment given to connection
capex and the carbon price.

**Read as a breakeven: the customer must value uninterrupted heat at more than
the last column for the extra depth to pay.** That value is the cost of
stopping the plant, which is site-specific and is not asserted here.

## What this settles, and what it does not

**Settled.** Firmness is not priced by any of the three markets beyond four
hours. The energy market pays for depth up to the forecast horizon and exactly
nothing after it; MISO's capacity market pays the same for a 4-hour tank as for
a 100-hour one; the NEM pays nothing at all. **A multi-day product is sold to
the customer's reliability requirement, not to the grid's.**

**The policy point.** This is a market-design gap, and it is the sharpest one in
the study. Long-duration storage delivers reliability that the system values —
that is the entire rationale for capacity mechanisms — but every product on
offer is written in MW, with a duration floor low enough that depth beyond four
hours is invisible to it. **A capacity product that paid for duration, not just
for power, would change what gets built.** MISO is already moving that way in
its accreditation reforms; the point is that the *product* has not followed.

**Not settled.** What firm heat is worth to an industrial customer. That is the
missing term, it is the largest one, and no public source has it. It is a good
question to ask Antora rather than to answer for them — see
`notes/open-questions.md`.

**Boundary.** Everything here is about what markets *pay*. Whether Antora's
hardware qualifies as a MISO Load Modifying Resource or a Spanish SRAD provider
is a tariff-eligibility question this study does not settle, and the numbers
above should be read as what the products pay, not as revenue Antora can bank.
