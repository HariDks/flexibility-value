# Every decision made, and why

**44 decisions.** Each is tagged:

- **[P] Published** — taken from a source; the answer is not mine
- **[T] Tested** — swept across a range, so no single value is claimed
- **[J] Judgment** — my call. These are the ones to be able to defend

Counts: **10 published, 16 tested, 18 judgment.**

Nearly half are judgment calls. Most are about *scope and framing* rather
than about numbers — but they are still mine, and the honest count matters
more than a flattering one.

---

## A. Scope — 5 decisions

**1. Measure the value of flexibility, not build a siting map. [J]**
Three alternatives were considered and rejected: an ISO-level opportunity map
(blocked by commercially-gated pricing-node geolocation, and it duplicated a
deal Antora had already closed), a curtailment statistic (one slide, not a
project), and a 45X tax-credit model (wrong audience). Flexibility value is the
number underneath every argument Antora makes, and nobody had published it.

**2. Three markets: Spain, South Australia, MISO. [J]**
Spain and South Australia because the contact was actively researching them.
MISO because it is where Antora's real project is, and because it is
wind-driven rather than solar — so the comparison tests what is general.

**3. Every year each source publishes, not one. [J]**
Ended at 25 market-years. A single year would have presented a trend as a
market property — Spain's saving runs 12.5% to 37.9% across eight years.

**4. Price storage as an arbitrage asset only. [T]**
The firming case is now priced too, from published auctions. The physics needs
no simulation — an N-hour tank rides through an N-hour interruption — so the
question is who pays for depth, and the answer is nobody past four hours.
Arbitrage pays up to the forecast horizon and exactly zero after it. MISO's
capacity auction pays $217/MW-day (2025/26) and $126.19 (2026/27), worth
$9.04 and $5.26 per MWh of heat, and **requires only four consecutive hours** —
so a 100-hour tank earns what a 4-hour tank earns. Spain's SRAD pays €56.43/MW
per assigned hour over 4,371 hours, but only for metered reduction, and the
battery is drawing its full rating in just 32.6% of the risk hours, putting the
realistic value at €9-15/MWh rather than €28. The NEM has no capacity market at
all. **The 24-to-164-hour wedge is unpaid everywhere.** See `notes/firmness.md`.

**5. Operating cost only, no capital. [J]**
Connection capex scales with charge rate and would push against fast charging.
This is a real gap and is flagged rather than hidden.

## B. The modelled plant — 7 decisions

**6. 10 MW of heat, continuously. [J]**
Round numbers, easy to sanity-check, and large enough to sit in industrial
tariff classes. Savings are ratios, so scale mostly cancels — but tariff class
and scheme eligibility depend on size, so results do not transfer to a very
different plant.

**7. Demand is constant, 24/7/365. [T]**
Now tested against a two-week turnaround, a five-day week, and a five-day day
shift. The saving holds: Spain 34.1-37.9%, MISO 47.6-52.1%, South Australia
49.9-66.9% — and in South Australia every intermittent profile beats the base
case, so continuous operation was the conservative assumption. The turnaround's
timing changes the answer by at most 2.5 points across all twelve months.
**What does move is the capacity charge: at 48% utilisation it is 2.1x higher
per MWh in all three markets**, because a fixed charge spread over less output
costs more per unit. Both buyers pay it, so the saving is unmoved and the bill
is not. See `notes/demand-profile.md`.

**8. 12-hour storage as base case. [T]**
Tested 4h to 168h. Chosen because the median gap without cheap power is 8–13
hours — measured, not assumed.

**9. Charge rate 4× average draw. [T]**
Tested 2×/4×/6×. Not a claim about Antora's hardware. The energy balance sets
it: 12h of storage serving constant heat needs ~2× if charging spreads over the
other 12 hours, ~4× to concentrate into 6, ~6× into 4. It is a choice about how
tightly to concentrate charging.

**10. Standby loss 1%/day. [T]**
Tested 0–10%/day; effect is 0.1–1.9 points. Immaterial because heat sits in the
tank for only 5–8 hours.

**11. Tank starts empty. [T]**
Tested empty/half/full. Irrelevant over 8,760 hours except where a hard
availability constraint binds from hour one, which is why the wind test starts
it full.

**12. No electrical-to-thermal conversion loss. [J]**
Resistive heating is very close to 100% efficient, so omitting it changes
nothing material.

## C. The scheduling model — 6 decisions

**13. A simple greedy rule, not an optimiser. [T]**
Measured against the exact optimum: within 1.5% at the base case, and always
erring the same way — costing more, never less. Kept because it explains in one
sentence, and every saving is therefore a floor.

**14. Foresight and search window are the same quantity. [J]**
Deciding to buy at hour *j* for a shortfall at hour *h* requires knowing
*h − j* hours ahead. So capping the search caps the forecast horizon exactly.
This is a modelling insight, not an assumption, and it made the visibility
analysis possible.

**15. Horizons: 24h Spain, 24h MISO, 6h South Australia. [J]**
Spain and MISO publish day-ahead prices, so 24h is a market fact. **South
Australia's 6h is the single largest judgment in the project** — the NEM has no
day-ahead market and publishes forecasts with no confidence intervals. The
result runs 49.9% at 6h to 73.1% at 24h. Reported as a range.

**16. Spain's "cheap bands" are P4–P6. [T]**
Tested every combination. P4–P6 and P3–P6 both give 38.7%, and both are the
maximum; narrower or wider is worse.

**17. South Australia draws nothing in the peak window. [T]**
Tested allowances from 0× to 4×. Cost rises monotonically from 60.20 to 87.00,
so zero is optimal.

**18. MISO's only lever is charge rate. [P]**
Not a choice — Schedule 632 has no time structure to exploit, so there is
nothing else to vary.

## D. Counterfactuals — 4 decisions

**19. Inflexible benchmark buys at hourly prices and consumes flat. [T]**
Tested against a 0–20% forward risk premium. This is the *cheapest* inflexible
option that exists, so every real alternative costs more and the reported
savings are floors.

**20. Gas boiler is the business case; inflexible-electric is the measuring
stick. [J]**
Nobody runs a 50 MW resistive heater flat off the grid. The electric comparison
isolates the value of timing; the gas comparison is the choice a customer
actually faces. Both are reported, gas first.

**21. Boiler efficiency 85%. [T]**
Tested 80–90%. Deliberately generous to gas — being generous to the alternative
is the conservative direction.

**22. No forward risk premium is claimed. [J]**
The Cal-2025 Iberian forward settlement is not publicly retrievable. Rather than
invent one, the claim is scoped: this measures timing value against the cheapest
inflexible option.

## E. Data handling — 6 decisions

**23. Hourly resolution everywhere. [T]**
Measured cost: hourly averaging understates South Australia's saving by 3–12
points depending on tank size, and leaves the inflexible bill untouched. Kept
because it is the only granularity all three markets share, it is the actual
commitment unit in Spain and MISO, and it errs against the argument.

**24. Price points: Spain national, SA1, MINN.HUB. [T]**
Now tested. MISO publishes 2,464 pricing points including **OTP.OTP**, the load
zone of Otter Tail Power itself — the settlement point a load on that system
actually pays, and so a better answer than the nearest hub. Over four years
MINN.HUB is out by **0.1 points** against it, and all nine MISO hubs span
48.7–52.7%. Under the standard tariff every point is negative in every year
(36 of 36), so the MISO finding is a property of the tariff, not the node.
The NEM settles one price per region, so there is no node choice inside South
Australia; holding the SAPN tariff fixed and swapping regions gives 22.6%
(Tasmania) to 49.9% (South Australia). **The mechanism holds everywhere; SA is
the best case, and should be quoted as the top of a range.** See
`notes/nodes.md`. Spain has one national price, so nothing to vary.

**25. Local time, not market time. [P]**
Australia's market runs on Sydney winter time year-round while Adelaide shifts;
MISO runs a fixed −05:00 clock while Minnesota shifts. Both converted. Getting
this wrong would put the solar trough at the wrong hour and corrupt everything
downstream silently.

**26. Aggregate to hourly from 15-min, 5-min and 30-min natives. [P]**
Spain switched to 15-minute pricing on 1 October 2025; the NEM to 5-minute in
October 2021. Both handled, with interval-ending converted to
interval-beginning.

**27. Day-ahead prices where a day-ahead market exists. [P]**
Spain and MISO have one; the NEM does not, so South Australia uses real-time
spot. This is a market-design difference, not a data choice.

**28. Tariffs held at 2025 values across all price years. [J]**
So that only prices vary. Mixing tariff vintages would confound price trends
with tariff changes.

## F. Tariffs — 7 decisions

**29. Spain: 6.3TD as base, all four classes reported. [T]**
Class follows connection voltage, and the megawatt threshold at each voltage is
set by the distributor's connection study, not a citable table. **So the class
is not asserted.** The saving is 36.4% on 6.1TD through 38.8% on 6.4TD.

**30. Include Spain's system charges as well as network tolls. [P]**
Two separate BOE instruments. Omitting the second would understate the bill.

**31. South Australia: Sub-Transmission (STR). [P]**
The class for a 25–60 MW site at 33/66 kV, per SA Power Networks' own
large-business definition (minimum 5,000 kVA).

**32. Both SA tariff vintages run. [T]**
The 2025-26 schedule is not published. Both bracketing years give 49.5% and
49.1%, so the mismatch is immaterial.

**33. ElectraNet kept as a counterfactual. [J]**
A site this size connects to SA Power Networks; ElectraNet's exit points are
almost all bulk supply into SAPN. Kept because it isolates the mechanism inside
one country with no confounds.

**34. MISO: Schedule 632 plus the Energy Adjustment and every rider. [P]**
The published rate summary excludes both and says so. Including them moved the
inflexible baseline from $36.32 to $62.47 — the single largest correction in the
project.

**35. TMEP Baseline Demand = 10 MW. [T]**
The tariff does not specify it; it is set in the service agreement. Tested
10–40 MW: the result runs +20.6% to −59.3%. **The headline is a fact about the
tariff plus an assumption about a negotiation**, and is labelled as such.

## G. Gas and carbon — 4 decisions

**36. Gas prices per market, annual, published. [P]**
Eurostat band I4 for Spain (the band matching ~371,000 GJ/yr), the AER STTM
register for Adelaide, EIA Minnesota industrial for MISO. Two earlier
single-month estimates were replaced; both had understated gas, which had
understated the battery.

**37. Carbon price each market's emitters actually face. [P]**
EU ETS €75/t, Australia's Safeguard default prescribed unit price A$36.99/t,
zero for the US.

**38. Gas emissions 0.202 tCO2 per MWh burnt. [P]**
Standard inventory figure.

**39. Report a breakeven carbon price, not just a comparison. [J]**
Deriving the price at which the two match removes dependence on the assumed
carbon price — only which side of the line it falls on matters.

## H. Presentation — 5 decisions

**40. Percentages, not absolute currency. [J]**
Three currencies. Converting would add an exchange-rate assumption that changes
numbers without improving the argument.

**41. Ranges and trends, not single years. [J]**
"12% in 2018, 38% in 2025, rising about 3 points a year" is both truer and
stronger than any single figure.

**42. "Inflexible electrification counterfactual", never "normal factory". [J]**
The second invites an obvious objection — no real plant obtains process heat
that way. The name should say it is a benchmark.

**43. Report the two-networks result as a gap, not a sign flip. [J]**
The dramatic "+50% versus −19%" compared two different charge rates. What
survives at a consistent 4× is that SA Power Networks beats the best ElectraNet
location by 19–44 points in every one of nine years.

**44. Keep a corrections log. [J]**
Twelve claims made during the work and later overturned, recorded rather than
quietly deleted. If someone finds an error, the answer is that twelve were
found, every one is logged, and each made the result more conservative.

---

## The three that matter most if challenged

**South Australia's 6-hour visibility (15).** The largest judgment. Moves the
answer from 49.9% to 73.1%. Defence: report the range, and say plainly that the
NEM publishes forecasts but no committable price at any horizon.

**The TMEP baseline (35).** Turns a +20.6% into a −6.0% if it lands at 20 MW.
Defence: the mechanism is the finding; the baseline is where value is
negotiated, and that is itself the useful point.

**Charge rate (9).** Drives the whole demand-charge result and the two-networks
sign. Defence: it is swept, the energy balance justifies the range, and the
base case is the middle of it.
