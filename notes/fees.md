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
