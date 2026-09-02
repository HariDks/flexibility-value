# Network fees and price access, by market

**Step 4.** Research in progress. Confidence ratings are honest — anything marked
low must not go in the memo as a number without a primary source.

---

## The headline finding: the fee is not one number

The plan assumed "one stylized non-energy adder per market, in currency per MWh."
**That assumption is wrong, and wrong in a way that matters.** Network charges in
all three markets have two components that behave completely differently:

| Component | Charged on | Effect on the comparison |
|---|---|---|
| **Energy charge** | every MWh delivered | Hits both buyers equally. Compresses the percentage saving; favours neither. |
| **Capacity / demand charge** | peak kW or kVA drawn | **Hits the battery far harder.** It draws its power in bursts, so its peak is several times a normal factory's for the same annual energy. |

This is the real mechanism, and it is sharper than "fees eat the saving." A
thermal battery buys the same energy through a much smaller number of hours, so
under a demand-based tariff it pays for a much bigger connection. **Whether
flexibility pays is therefore decided by the *design* of the network tariff, not
by its level.**

It also explains why the Big Stone deal needed a bespoke tariff rather than a
discount.

---

## Spain

**Can an industrial load buy at hourly wholesale prices?** Yes. Spain has retail
competition and indexed ("tarifa indexada") supply contracts referencing the OMIE
hourly price are a standard product. *Confidence: medium-high.*

**What is charged on top?** Access tolls (*peajes*, network) plus system charges
(*cargos*), under a **six-period structure P1–P6** that applies to **both** the
energy term (€/kWh) and the power term (€/kW/year).

For 6.1TD (high voltage 1–30 kV, contracted power above 450 kW), 2026 values:

- Power term: **23.95 €/kW/year in P1** down to **0.063 €/kW/year in P6**
- Energy term: **0.0268 €/kWh in P1** down to **0.000029 €/kWh in P6**

Set annually by CNMC resolution and a TED ministerial order.
*Confidence: medium — figures are from secondary sources and need checking
against the BOE before use.*

**The wrinkle, and it is the interesting one.** Contracted power is set per
period and must be non-decreasing, P1 ≤ P2 ≤ … ≤ P6. So contracting *more* power
in the cheap late-night period is explicitly allowed — the structure is built to
reward off-peak loading, and standard advice to Spanish industry is literally
"shift flexible consumption to P6."

But **P6 is 00:00–08:00 on weekdays, plus all weekends and holidays**, while
P1/P2 sit in "central day hours, roughly 09:00–21:00" in high season.

**Spain's cheap wholesale hours are at midday** — that is where the solar crash
lands, and the model buys at 14:00. So the hours the *energy market* says are
cheapest fall inside the periods the *network tariff* prices as peak.

> The tariff's time periods were drawn around an old demand curve. Solar moved
> the surplus to the middle of the day. The network tariff has not followed.

If that holds up against primary sources it is a concrete, actionable policy
finding, and the single best thing in the memo.
*Confidence: medium on the mechanism, low on the exact hour boundaries — the
P1–P6 calendar varies by season and must be taken from the BOE.*

---

## South Australia

**Can an industrial load buy at spot prices?** Yes, and there is no day-ahead
market to buy in — the NEM is real-time spot. Large loads can be market
participants or buy via a retailer on a pass-through contract.
*Confidence: medium.*

**What is charged on top?** SA Power Networks charges **all large business
customers on a demand tariff**. Two charging parameters: **Anytime Demand** and
**Peak Demand**. The large-business threshold is 5,000 kVA.

**Anytime Demand is charged on maximum demand whenever it occurs** — which is
precisely the structure that punishes a bursty charging profile. This is the
worst case for a thermal battery of the three markets.

**But there is a live reform.** From **1 July 2025** SA Power Networks introduced
**flexible connections**: Flexible Demand is charged at **50% of Anytime Demand**,
with a narrower window for measuring Peak Demand. That is a tariff explicitly
designed to reward controllable load — directly relevant to Antora, and a good
precedent to be able to cite.
*Confidence: medium on structure, low on rates — the $/kVA figures are in the
AER pricing proposal and have not been extracted yet.*

---

## MISO / Minnesota

**Can an industrial load buy at hourly wholesale prices?** **No — not by
default.** Minnesota has no retail choice. Otter Tail is a vertically integrated
utility under cost-of-service regulation by the Minnesota PUC; retail customers
cannot pick a supplier.

The **only** route to hourly MISO pricing is a specially filed tariff. That is
exactly what the **TMEP rider** is, and why it needed approval from three state
commissions before Big Stone could operate.

**This is the thesis of the memo, confirmed.** In MISO the binding constraint is
not the price of power or the size of the fee — it is that the transaction is not
available at all without a regulator's permission. Cheap electricity is
abundant; *access* to it is scarce.
*Confidence: high on the access finding, which is the important one.*

**What is charged on top?** Otter Tail's Minnesota commercial and industrial
rates are split by voltage (secondary / primary / transmission) and by season
(summer June–September, winter October–May), with demand charges plus riders.
Xcel's interruptible tariff cuts demand charges in exchange for curtailment
rights — another precedent for paying flexible load differently.
*Confidence: low on rates — needs the primary tariff sheets.*

---

## Still to do

- [ ] Spain: pull the P1–P6 hour calendar and 2025 rates from the BOE, not blogs
- [ ] Spain: confirm which tariff class applies at ~40 MW (6.1TD is 1–30 kV;
      a load this size may sit at a higher voltage class)
- [ ] South Australia: extract $/kVA rates from the AER pricing proposal
- [ ] MISO: get Otter Tail's primary tariff sheets, and the TMEP filing itself
- [ ] All: re-run the model with a two-part fee and see what survives
