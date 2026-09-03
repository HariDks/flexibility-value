# Network fees and price access, by market

**Step 4, complete.** Every rate below comes from a primary published source.
Two claims made earlier in the research and later disproven are recorded at the
bottom, so the reasoning is not repeated by accident.

---

## The mechanism

Network charges have two components that behave completely differently:

| Component | Charged on | Effect |
|---|---|---|
| **Energy charge** | every MWh delivered | Hits both buyers equally. Compresses the percentage saving; favours neither. |
| **Capacity / demand charge** | peak kW or kVA drawn | Hits the battery far harder — it takes the same energy through far fewer hours, so its peak is several times a normal factory's. |

**Whether flexibility pays is decided by the *design* of the capacity charge,
not its level.** A charge that knows what time it is can be dodged by a
flexible load. A charge that does not, cannot.

---

## Results

Delivered cost per MWh of heat, 12h tank, on published rates and with the
forward visibility each market actually provides:

| Market | Visibility | Factory | Battery | Saving |
|---|---|---|---|---|
| Spain | 24h (day-ahead) | EUR 76.10 | EUR 48.36 | **+36.5%** |
| South Australia | 6h (no day-ahead) | AUD 120.12 | AUD 61.16 | **+49.1%** |
| MISO | 24h (day-ahead) | USD 62.47 | USD 63.80 | **−2.1%** |

---

## Spain — tariff 6.1TD

**Access:** yes. Retail competition exists and indexed (*tarifa indexada*)
supply contracts referencing the OMIE hourly price are a standard product.

**Rates**, transport plus distribution tolls (*peajes*) from CNMC resolution of
4 December 2024, [BOE-A-2024-26218](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-26218),
plus system charges (*cargos*) from Orden TED/1487/2024,
[BOE-A-2024-27289](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-27289):

| | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---|---|---|---|---|
| Power, peajes EUR/kW/yr | 23.669 | 12.514 | 4.696 | 3.309 | 0.070 | 0.062 |
| Power, cargos EUR/kW/yr | 1.178 | 0.590 | 0.428 | 0.428 | 0.428 | 0.196 |
| Energy, peajes EUR/MWh | 27.10 | 11.89 | 4.73 | 2.74 | 0.12 | 0.03 |
| Energy, cargos EUR/MWh | 2.58 | 1.91 | 1.03 | 0.52 | 0.33 | 0.21 |

**Calendar:** seasons are high (Jan, Feb, Jul, Dec), medium-high (Mar, Nov),
medium (Jun, Aug, Sep), low (Apr, May, Oct). On weekdays the peak block is
09:00–14:00 and 18:00–22:00, taking the season's higher period; 00:00–08:00 is
always P6, as are all weekends and national holidays. **P1 therefore exists only
on weekdays in January, February, July and December** — about 800 hours a year.

Contracted power is set per period and must be non-decreasing, P1 ≤ P2 ≤ … ≤ P6,
so contracting *more* in the cheap late periods is explicitly permitted.

**Result:** the tariff-aware battery contracts 10 MW in P1–P3 (the same as the
factory) and 60 MW in P4–P6, cutting capacity cost from EUR 21.72 to 8.00/MWh.
It pays *more* for energy than a naive battery — EUR 37.48 against 33.06 —
because refusing peak bands means missing some genuinely cheap hours. It gives
up 4.50 on power to save 13.70 on the connection.

---

## South Australia — SA Power Networks, Sub Transmission

**Access:** yes, but there is no day-ahead market to buy in. The NEM is a
real-time spot market; the price is set as it happens.

**Rates.** SA Power Networks publishes only the current year's price list, so
the 2025-26 schedule covering the data year is not retrievable. Both bracketing
published years were run:

| Vintage | Code | Energy AUD/MWh | Peak $/kVA/day | Anytime $/kVA/day | Flexible |
|---|---|---|---|---|---|
| 2024-25 | STN | 15.30 | 0.1584 | 0.0449 | 0.0225 |
| 2026-27 | STR | 25.00 | 0.1737 | 0.0274 | 0.0137 |

Peak Demand is measured **only inside 17:00–21:00** (outside the Adelaide CBD);
Anytime Demand on the largest draw at any hour. The Flexible variant, introduced
1 July 2025, charges Anytime Demand at half rate for controllable load.

**The rate-year mismatch is immaterial:** saving comes out 49.5% on 2024-25
rates against 49.1% on 2026-27. The changes offset.

**Why it wins despite having no day-ahead market.** The advantage splits in two:

- **The tariff half is robust.** Avoiding the 17:00–21:00 window needs a clock,
  not a forecast. Capacity cost holds at AUD 6.85/MWh at *any* visibility — and
  is *below* the normal factory's 8.38, because the factory cannot dodge
  dinnertime and the battery can.
- **The energy half is fragile.** Power cost runs from −AUD 1.29 under perfect
  foresight to AUD 29.31 at six hours. All the erosion is here.

South Australia wins on **tariff design**, not on price-chasing.

| Visibility | 3h | 4h | 5h | 6h | 8h | 12h | tank-limited |
|---|---|---|---|---|---|---|---|
| Saving | infeasible | infeasible | 42.4% | 49.1% | 57.5% | 71.2% | 74.6% |

Below five hours the strategy is infeasible — the battery cannot fill up before
a four-hour blackout it can see coming. **That floor is set by the tariff, not
the market.**

---

## MISO — Otter Tail Power, Minnesota Schedule 632

**Access: no.** Minnesota has no retail choice. Otter Tail is vertically
integrated under cost-of-service regulation by the Minnesota PUC, and retail
customers cannot pick a supplier. **The only route to hourly MISO pricing is a
specially filed tariff** — which is exactly what the TMEP rider is, and why it
needed three state commissions to approve it.

**Rates.** Schedule 632 Transmission Service, from Otter Tail's published
Minnesota commercial rate summary — **plus** the Energy Adjustment and riders,
which that summary explicitly excludes and which turn out to be large:

- Customer charge USD 253.00/month, facilities charge nil
- **Billing demand: USD 12.74/kW/month June–September, 9.97 October–May, on
  the maximum in each calendar month**
- Base energy 20.10 USD/MWh summer, 22.00 winter
- **Energy Adjustment Factor** (Large General Service, non-TOD), the fuel and
  purchased-energy true-up: **11.08 to 23.74 USD/MWh** by month in 2025
- Volumetric riders: ECO 5.78, EITE 0.45 USD/MWh
- Demand riders: Transmission Cost Recovery 1.03 USD/kW, Renewable Resource
  0.413 USD/kW to June then 0.038

A customer buying its own energy at MISO prices avoids the base energy charge,
the Energy Adjustment and the supply-side Renewable Resource rider, but still
pays the demand charge, the demand riders and the volumetric public-policy
riders.

**There is no time-of-day structure in the demand charge at all**, so a flexible
load has nothing to respond to and its burstiness is charged for regardless.
The demand charge scales linearly with charge rate while the energy saving
flattens, so there is no interior optimum:

| Charge rate | 1.5x | 2x | 2.5x | 3x | 4x | 6x |
|---|---|---|---|---|---|---|
| Delivered USD/MWh | 63.80 | 69.25 | 76.06 | 83.54 | 99.42 | 132.24 |
| vs factory | −2.1% | −10.9% | −21.8% | −33.7% | −59.1% | −111.7% |

**The best a battery can do under the standard tariff is break even — and only
by being barely flexible.** At 1.5x it draws 15 MW to the factory's 10 and comes
out 2.1% behind. Every increment of real flexibility costs more in demand charge
than it saves in energy. Flexibility is not rewarded here at any setting.

That is the case for TMEP, on the utility's own published numbers: not that
Minnesota power is expensive, but that the standard tariff gives a flexible load
no way to be paid for being flexible.

Xcel's interruptible tariff, which cuts demand charges in exchange for
curtailment rights, is a second precedent for paying flexible load differently.

---

## The policy conclusion

It is not the level of the charge that decides whether flexibility pays — it is
whether the charge knows what time it is.

- Spain bands its charges by period → a battery dodges the expensive ones.
- South Australia measures peak demand in a four-hour window → a battery avoids
  it entirely, and beats the factory on network cost.
- MISO charges the monthly maximum whenever it falls → nowhere to hide.

**Recommendation: put a clock on the demand charge.** That single change is
worth more to a flexible load than any subsidy, and it costs the network
nothing it was actually trying to recover.

---

## Corrections — claims made during research and later disproven

1. **"Spain's tariff periods are misaligned with its solar."** Wrong. Having
   pulled the actual calendar, P1 exists only on January, February, July and
   December weekdays, and April–May — the battery's two best months — contain no
   P1 or P2 at all. The Spanish tariff is defensible design; the problem was the
   naive battery wandering into peak bands for no benefit.

2. **"South Australia's Anytime Demand charge is the worst case of the three."**
   Wrong, and backwards. Most of SA's demand charge sits in Peak Demand, measured
   in a narrow evening window a battery trivially avoids. SA is the *best* of the
   three. MISO's time-blind monthly demand charge is the worst by a wide margin.

3. **Cargos estimated at EUR 8–20/MWh.** Wrong by five to ten times; the
   published values are EUR 0.21–2.58/MWh. Spain deliberately keeps regulated
   charges low for high-voltage industry.

---

## Where each market's saving actually comes from

Two levers are available to a battery: **hunt cheap prices**, and **obey the
tariff clock**. Isolating them — the tariff-only case uses a flat price signal,
so the battery has no price preference at all but still plans around the bands:

| Market | Price hunting alone | Tariff clock alone | Together | Interaction |
|---|---|---|---|---|
| Spain | +21.1% | **+0.0%** | +36.5% | **+15.3** |
| South Australia | +27.6% | **+16.1%** | +49.1% | +5.4 |
| MISO | −137.6% | **−54.5%** | −64.0% | +128.1 |

The three markets are three different kinds of tariff:

- **Spain — permissive.** Obeying the clock is worth *nothing* on its own: a
  battery with no price preference buys just-in-time and pays exactly what the
  factory pays. But it nearly doubles what price-hunting is worth, 21.1% to
  36.5%. The tariff does not reward flexibility; it *permits* it, by not
  punishing the peak that price-hunting creates.
- **South Australia — rewarding.** The clock pays 16.1% by itself, with no
  forecasting whatsoever, because avoiding the 17:00–21:00 window directly cuts
  the largest charge. Price-hunting then adds on top.
- **MISO — punitive.** Every lever loses. Even a slow, price-blind battery is
  54.5% worse off than a normal factory. There is no window to avoid and no
  band to prefer, so flexibility has nothing to respond to and its burstiness
  is charged for regardless.

### The MISO baseline, now closed out

An earlier version of this file put the MISO factory at USD 36.32 and the
battery 64% behind. That used the rate summary alone, which excludes the Energy
Adjustment and riders. With both included the factory pays **USD 62.47** and the
battery's best case is **63.80, or 2.1% behind** — a wash, not a rout.

The qualitative finding survives and is now defensible: flexibility earns
nothing in Minnesota at any charge rate, and the only way to avoid losing is to
stop being flexible. The earlier −64% headline was an artefact of an
understated baseline and should not be quoted.

---

## TMEP, read from the tariff itself

Otter Tail Section 14.16, Thermal Market Energy Pricing. Approved by the
Minnesota PUC 13 November 2025, Docket No. E017/M-25-253, effective 1 January
2026. Source: `otpco.com/media/40nlwdts/mn_1416.pdf`.

**The clause that does the work:**

> *"Demand: A Customer's monthly bill for Demand shall be determined by
> multiplying the Customer's **Baseline Demand** by the Demand rate provided in
> the Large General Service rate schedule applicable to the Customer."*

Demand is billed on an agreed **Baseline Demand** — "a representation of its
typical pattern of electricity consumption", fixed in the service agreement —
**not on metered peak.** Energy above baseline settles at the MISO LMP at a
customer-specific CP Node, and is explicitly exempt from the Energy Adjustment
Rider.

That is exactly the fix this analysis said was needed, and it is a single clause.

### What it does to the numbers

| Charge rate | Schedule 632 | TMEP |
|---|---|---|
| 1.5x | −2.1% | **+11.2%** |
| 2x | −10.9% | **+15.8%** |
| 3x | −33.7% | **+19.6%** |
| 4x | −59.1% | **+20.8%** |
| 6x | −111.7% | **+21.5%** |

**The sign of the gradient flips.** Under the standard tariff every increment of
flexibility costs more than it earns, so the best strategy is to stop being
flexible. Under TMEP every increment *earns* more, so the best strategy is to be
as flexible as the equipment allows.

Same battery, same market, same prices, same year. One tariff makes flexibility
a liability; the other makes it an asset. The difference is which number the
demand charge is multiplied by.

### Other terms worth knowing

- **Availability:** new greenfield only, Demand ≥ 25 MW, **load factor < 50%**,
  entire thermal load registered as a MISO load modifying resource, no
  behind-the-meter generation except emergency backup.
- **The coincidence condition:** service must be taken "coincident with and not
  to exceed the hourly generating output of a nearby specifically identified
  wind and/or solar generation resource that is not owned by the Company."
  **This is a real constraint not modelled here** — the battery may only charge
  when a named wind farm is generating, and only up to its output. It would cut
  the saving below the figures above.
- **Day-ahead prices are provided.** The Company makes day-ahead thermal market
  prices available by 16:00 the preceding day, and the customer nominates its
  expected hourly load by 07:00. So the 24h visibility assumed for MISO is
  correct, and is a tariff obligation rather than a market feature.
- **Curtailable** to Firm Demand at the Company's sole discretion, with the
  customer liable for costs of failing to curtail.
- Customer charge USD 282.00/month; minimum one-year term.
- **NITS** (Network Integration Transmission Service) charges are added to the
  price and are **not modelled here** — another reason the figures above are an
  upper bound.

---

## Robustness checks

### How close is the greedy to optimal?

The scheduling rule is a greedy heuristic, chosen for explainability. The exact
minimum-cost schedule was solved as a linear program (tank level as the
variable, which keeps the constraint matrix bidiagonal; solves in under a
second) and compared. Gaps expressed against the **factory's bill**, because at
large tanks the battery's own bill approaches zero and percentages of it become
meaningless:

| Tank | Spain | South Australia | MISO |
|---|---|---|---|
| 4h | 0.0% | 0.1% | 0.0% |
| **12h (base case)** | **0.2%** | **0.7%** | **0.2%** |
| 24h | 0.9% | 1.9% | 0.8% |
| 48h | 3.0% | 3.6% | 1.3% |

**At the 12-hour base case the greedy is within about half a percent of optimal.**
The claim that it is "good enough" is now measured rather than asserted. It
degrades at large tanks — another reason the 48h figures were always the weakest
in the set — and it always errs the same way, costing more than optimal, so
every saving reported is a floor.

Switching to the exact solver would be cheap. It is not done because the greedy
is explainable to a non-technical reader in two sentences and the difference at
the size that matters is half a percent.

### Does the Spanish tariff class change the conclusion?

6.1TD covers 1–30 kV, and a load of this size may connect higher. All four
industrial classes, 2025 peajes plus cargos:

| Class | Factory | Battery | Saving |
|---|---|---|---|
| 6.1TD (1–30 kV) | 76.10 | 48.36 | **36.5%** |
| 6.2TD | 72.35 | 44.79 | 38.1% |
| 6.3TD (30–72.5 kV) | 70.86 | 43.45 | 38.7% |
| 6.4TD (>72.5 kV) | 69.14 | 41.65 | 39.8% |

Higher voltages are cheaper for both buyers, and the saving *rises* with
voltage. **Whichever class is correct, the answer is 36.5–39.8%, and the
reported 36.5% is the most conservative available.** The Spanish half of the
connection-voltage risk is closed.

The Australian half is not: if a load this size connects at transmission level
it leaves SA Power Networks' network entirely, and the peak-window structure
that produces the Australian result may not apply. That still needs checking.

### Does the choice of baseline factory matter?

The baseline factory buys at hourly prices and consumes flat, so it pays the
realised annual average. A real industrial customer is more likely on a
**fixed-price contract**, which is priced off the forward curve and embeds a
risk premium over the realised average.

That means the chosen baseline is the **cheapest inflexible option available** —
any real alternative costs more, and every euro more makes the battery look
better:

| Risk premium | Spain | South Australia |
|---|---|---|
| 0% (as reported) | 36.5% | 49.1% |
| 5% | 39.1% | 50.9% |
| 10% | 41.5% | 52.5% |
| 20% | 45.8% | 55.5% |

**The direction is unambiguous, so the reported figures are a floor.**

**The exact premium could not be sourced and should not be estimated.** Pinning
it down needs the Cal-2025 Iberian forward settlement price against the realised
average, and OMIP's historical settlement archive is not publicly retrievable.
Rather than put a made-up premium in the memo, the honest move is to **scope the
claim**: what is reported is the value of *timing*, measured against the
cheapest inflexible option available — an indexed customer paying the realised
average. A fixed-price customer pays more, so the figures are a floor, and the
memo says exactly that and no more.

Separately, the baseline choice affects *framing*: this measures flexibility
against inflexible electricity, not electric heat against gas. That distinction
belongs in the memo, and which frame the audience uses is worth confirming.

---

## The Australian connection-voltage question, closed

**Does a 25–60 MW load sit under SA Power Networks' tariff, or connect straight
to transmission?** This was the last open risk in the analysis.

**Answer: SA Power Networks, and the modelling is right.** ElectraNet's
Prescribed Transmission Service Price Schedule for 2025-26 lists its exit
points, and they are overwhelmingly **bulk supply points into SA Power
Networks' own network** (Adelaide suburbs, Para subsystem, Port Pirie) plus a
handful of legacy directly-connected loads — SA Water's pumping stations at
3.3–11 kV. An industrial site of this size connects to SA Power Networks at
33/66 kV.

Two things follow, and both matter:

1. **No transmission cost is missing.** SA Power Networks' published rates are
   **NUoS = DUoS + TUoS**, so ElectraNet's transmission charge is already inside
   the STR rates used throughout.
2. **The counterfactual is worth stating anyway**, because it proves the thesis
   inside a single country.

### If the same load connected directly to ElectraNet

ElectraNet bills capacity on **agreed maximum demand, every day of the year,
with no peak window** — structurally identical to MISO's monthly maximum.
All-in capacity is 203.2 $/MW/day non-locational and common-service, plus a
locational component from 50 to 207, with 31.56 $/MWh of energy charges
(ex-GST; the published schedule is GST-inclusive).

| Network | Charge design | Battery result |
|---|---|---|
| **SA Power Networks** | Peak Demand measured 17:00–21:00 only | **+49.1%** |
| ElectraNet, Para 66kV | Agreed maximum demand, any hour | +5.9% |
| ElectraNet, Brinkworth 33kV | Agreed maximum demand, any hour | **−4.8%** |
| ElectraNet, Ardrossan West 33kV | Agreed maximum demand, any hour | **−14.1%** |
| ElectraNet, Berri 66kV | Agreed maximum demand, any hour | **−18.6%** |

**Same country, same prices, same year, same battery.** Connected to a network
whose charge knows what time it is, flexibility is worth 49%. Connected to one
whose charge does not, it is worth between +6% and −19% depending only on where
you stand.

This is the strongest form of the argument available: it removes every
confound. No currency difference, no market-design difference, no weather. Only
the structure of the demand charge changes, and it changes the sign of the
answer.

---

## QA pass — three checks that had not been run

### 1. South Australia and MISO price data were never inspected visually

Step 1's whole purpose was catching data errors by eye, and it had only been run
on Spain. Both other markets now have the same year-heatmap.

Both pass, and both are physically right: South Australia shows a pale midday
solar band and a dark evening band sitting exactly where SA Power Networks
measures peak demand; MISO shows a pale overnight band (wind) with winter and
summer evening peaks. No gaps, no duplicates, no repeated-value days. Clock
changes land correctly in both hemispheres — Adelaide's 25-hour day in April and
23-hour in October, Minnesota's the other way round.

South Australia has 25 hours above 20x its median price, up to AUD 11,841. These
are genuine scarcity events, not errors.

### 2. Is full peak-window avoidance actually optimal in South Australia?

It had been assumed. Tested by sweeping how much draw to allow inside the window:

| Allowance inside the window | Delivered AUD/MWh |
|---|---|
| **0x demand** | **60.23** |
| 0.5x | 63.57 |
| 1x | 66.16 |
| 2x | 72.79 |
| 4x | 87.00 |

Monotonic, so zero is optimal. The assumption holds.

### 3. The peak window definition was wrong — and it is load-bearing

Sensitivity first, because it shows why this mattered. Assuming the window is
16:00–20:00 when the charge actually falls on 17:00–21:00 costs **39 percentage
points** — the saving collapses from 49% to 10%. Assuming a *wider* window makes
the schedule infeasible outright. An hour's error here is not a rounding issue.

So the definition was checked against SA Power Networks' own tariff page, which
says:

> *"Peak demand is measured as the highest daily average demand during the last
> 12 months **November to March**: CBD 11am–5pm, Rest of South Australia
> 5pm–9pm. Peak demand values are billed all year round."*

Two corrections follow:

- **Peak Demand is measured November to March only**, though billed year round.
  The model had been blocking the window on all 365 days.
- **It is the highest daily *average* over the window**, not the highest
  instant — a softer constraint than modelled.

Corrected, the South Australian saving moves from 49.1% to **49.9%**, and the
delivered cost from AUD 61.15 to 60.23. **Real error, immaterial effect** — the
battery wants the midday solar trough anyway, so giving up evening hours costs
little either way. `sa_network_cost` now implements the seasonal window and the
daily-average measure.


---

## South Australia's forward visibility — stated as the judgment it is

AEMO publishes **5-minute pre-dispatch one hour ahead** and **30-minute
pre-dispatch to the end of the next market day, up to ~40 hours**. So forecasts
exist far beyond the six hours assumed here.

But they are **deterministic point forecasts with no published confidence
intervals**, and — the structural point — the NEM has no day-ahead market, so
**there is no price a buyer can commit at, at any horizon**. In Spain and MISO
the day-ahead price is a number you contract at. In the NEM it is a projection.

The usable horizon is therefore a **forecasting capability**, not a market fact.
Six hours is a judgment about how far ahead a competent operator can act on NEM
forecasts, and the result is sensitive to it:

| Visibility | 3h | 5h | 6h | 8h | 12h | 24h | tank-limited |
|---|---|---|---|---|---|---|---|
| Saving | infeasible | infeasible | **49.9%** | 58.0% | 69.7% | 73.1% | 73.1% |

(At a 4x charge rate. With 6x the minimum feasible visibility drops to 5h — a
faster charger needs less warning to clear the peak-window blackout.)

**Report as a range.** The honest claim is that South Australian flexibility is
worth 50% at a conservative reading of forecast quality and up to 73% at a
generous one, and that improving the forecast is worth more there than anywhere
else in the study — because it is the binding constraint. That is itself a
finding: in South Australia, storage duration is irrelevant and forecasting
capability is everything.


---

## Correction: the greedy-vs-optimal gap, measured on the real problem

An earlier robustness check put the gap between the simple scheduling rule and
the exact optimum at 0.2-0.7%. **That was measured without the tariff caps in
play.** With them the gap is larger, because the caps create more opportunities
for a myopic rule to commit early and block a better opportunity later.

Like for like — both given unlimited foresight, both on the Spanish tariff-aware
caps:

| Tank | Simple rule | Exact | Gap (of the inflexible bill) |
|---|---|---|---|
| 6h | 54.25 | 52.44 | 2.6% |
| **12h (base case)** | **43.90** | **42.81** | **1.5%** |
| 24h | 37.82 | 36.55 | 1.8% |
| 48h | 34.25 | 31.47 | 3.9% |

Still entirely one-directional — the simple rule always costs more, never less —
so every saving reported remains a floor. But 1.5% at the base case, not 0.5%.

### What the 48-hour gap actually consists of

Reported at 48h the total gap looked like 9.8%. Decomposed:

| | EUR/MWh |
|---|---|
| simple rule, 24h foresight (what is reported) | 38.38 |
| simple rule, unlimited foresight | 34.25 |
| exact, unlimited foresight | 31.47 |

**5.8 points of that 9.8 is the foresight limit, and imposing it is correct.**
Spain publishes prices 24 hours ahead; a 48-hour tank cannot be planned with 24
hours of information. Only 3.9 points is the scheduling rule being simple.

So the large-tank weakness is mostly **a finding, not an error**: storage
duration is capped by available information in Spain too, at 24 hours rather than
South Australia's six. It is an independent argument for the 12-hour base case.
