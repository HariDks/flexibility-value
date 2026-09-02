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
| MISO | 24h (day-ahead) | USD 36.32 | USD 59.58 | **−64.0%** |

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

**Rates** (Otter Tail's published Minnesota commercial rate summary, Schedule
632 Transmission Service; excludes tax, fuel adjustments and riders):

- Customer charge USD 253.00/month, facilities charge nil
- **Billing demand: USD 12.74/kW/month June–September, 9.97 October–May,
  charged on the maximum in each calendar month**
- Energy 20.10 USD/MWh summer, 22.00 winter (bundled — includes supply)

**There is no time-of-day structure in the demand charge at all.** Nothing about
*when* a peak occurs reduces it, so a flexible load has no way to respond. The
battery pays USD 29.88–59.72/MWh in demand charges alone — more than the entire
wholesale price of the power — and ends up 64% to 138% *more expensive* than a
normal factory.

**This is the thesis, proven on the utility's own published rates.** Flexibility
in Minnesota is not merely unrewarded; it is actively penalised. Cheap
electricity is abundant, and access to it is scarce.

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
