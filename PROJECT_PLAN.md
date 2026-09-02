# What Is Flexibility Worth?

**A charging-cost study of thermal batteries across three electricity markets.**

Working document. If a decision changes, change it here first.

---

## 1. Why this exists

This is a sample project to bring to a conversation with a policy analyst at
**Antora Energy**. Antora builds thermal batteries: they turn cheap electricity
into stored heat and deliver that heat to industrial customers around the clock.

The goal is **not** to tell Antora something they don't know. They know their own
economics far better than any public-data project could. The goal is to
demonstrate that the analysis is something I can do independently, that my
judgment lands in the same place theirs does, and to earn a specific,
well-informed conversation.

The contact is currently researching **Australia and Spain** as potential
markets. That is why this study is international rather than US-only.

---

## 2. The whole idea in one page

A factory needs heat all day. It has two ways to buy the electricity that makes
that heat:

- **A normal factory** buys power as it burns it. It pays roughly the average
  price, whatever that turns out to be.
- **A thermal battery** buys power early and stores the heat. It can wait for the
  cheap hours and skip the expensive ones.

The difference between those two bills is **the value of flexibility**. That
number is the core of every argument Antora makes to regulators, grid operators,
and customers.

**The twist, and the point of the memo:** electricity bills are not just the
price of power. A network fee is charged per unit delivered no matter when you
bought it. That fee is set by regulators, it differs enormously by country, and
it eats a large share of the advantage. So how much flexibility is worth depends
less on how wild the prices are and more on how big that fee is — which makes
this a policy question, not an engineering one.

An interactive explainer of this mechanism lives in `explainer/`.

---

## 3. Locked decisions

Do not revisit these without editing this section.

| Decision | Value | Why |
|---|---|---|
| **Markets** | Spain (OMIE), South Australia (AEMO, SA1), US Midwest (MISO, Minnesota Hub) | Spain and Australia are where the contact is looking. MISO is the calibration case. |
| **Period** | One full recent calendar year, same year for all three | Seasonality is most of the story; a partial year distorts it. |
| **Factory** | 10 MW of heat, constant, every hour | ~240 MWh/day, ~87,600 MWh/year. Round numbers, easy to sanity-check. |
| **Charge rate cap** | 40 MW (4× demand) | Battery can buy four hours' worth in one hour. |
| **Storage sizes tested** | 4, 8, 12, 24, 48 hours of demand | Shows where savings stop growing. |
| **Charging rules** | (a) perfect foresight (b) trailing-percentile rule | The gap between them is the value of forecasting. |
| **Headline metric** | Cost per MWh of heat delivered — reported energy-only *and* delivered (with fee) | The gap between the two is the finding. |
| **Deliverable** | One chart + three pages | Sized to be read, not admired. |

**Presentation order is not build order.** Build Spain first (easiest data).
Present **MISO first**, explicitly framed as a check against a market Antora knows
well, then Spain and Australia as the contribution.

---

## 4. The six steps

Each step ends with something that exists. Do not start the next one until the
current one produces its checkpoint.

### Step 1 — Look at Spanish prices *(half a day)*
Download one year of hourly Spanish day-ahead prices from OMIE. Do no modelling.

Look at the year in two stages — zoom out, then zoom in:

**1a. The whole year, in one picture.** A heatmap: 365 columns (day of year) ×
24 rows (hour of day), each cell coloured by price. Read off it:

- which months are genuinely the extremes — **measured, not assumed**
- how many hours tall the cheap midday band is, and how that changes by season
  (this is the storage-sizing intuition)
- whether the pattern is consistent day to day (a clean band means forecasting is
  worth little; a speckled one means it is worth a lot — this predicts Step 5)
- weekends, as faint vertical striping every seven columns

**1b. Two weeks in detail.** Line charts of one week from each extreme month
*that the heatmap identified*. Colour cannot show precision, so this is where the
exact trough depth, trough width, and any absurd values get read.

Also worth producing, and likely a memo figure: average price by hour of day, one
line per month, twelve lines on one chart. Do not lead with it — averaging hides
the day-to-day variability that 1a exists to reveal.

**Data checks, all of which a plot catches and a table does not:**
- exactly 8,760 hours (8,784 in a leap year); one 23-hour and one 25-hour day at
  the clock changes
- **the clock is right** — if the midday crash appears at 3am, the timestamps are
  wrong. This is the most common and most damaging bug in energy data, and it
  would silently corrupt every number downstream
- no absurd values that are parsing errors rather than real scarcity pricing

**Checkpoint:** the heatmap and two week-plots on screen, extreme months chosen
from evidence, and confidence the data is what I think it is.
**Guard:** if the plot looks wrong, stop and fix the data. Do not model bad data.

*(Revised from "plot April and December" — those were assumed to be the extremes.
Plotting the full year measures which months actually are.)*

### Step 2 — Run the model on Spain *(half a day)*
Port the charging logic from the explainer (`explainer/flexibility-worth.html`,
the `schedule()` function) to Python. Run it over the full year.

**Checkpoint:** one real number — cost per MWh for the battery vs. the normal
factory in Spain. From here on, everything is refinement.

### Step 3 — Add Australia and MISO *(one day)*
Same model, different price files. South Australia from AEMO; MISO Minnesota Hub
via the `gridstatus` library.

**Checkpoint:** one tidy table of prices covering all three markets, and three
sets of results.
**Guard:** hub/regional prices only. **No nodal analysis.** See §6.

### Step 4 — Find the real network fees *(two days — the hard part)*
For each market, establish what an industrial consumer actually pays on top of
the wholesale price, and whether they can access hourly wholesale pricing at all.
This is document reading, not coding.

**Checkpoint:** `notes/fees.md` with a defensible number per market, the source
for each, and an honest confidence rating.
**Guard:** if a country's fee structure genuinely cannot be established from
public documents, **write that down as a finding**. Do not invent a number.

### Step 5 — Make the battery guess *(half a day)*
Add the second charging rule: buy when the price falls below the Nth percentile
of a trailing window, with a forced top-up when storage runs low. Run both rules.

**Checkpoint:** the foresight gap, quantified, per market.

### Step 6 — Write it up *(one day)*
One chart: savings on the y-axis, storage size on the x-axis, one line per
market, solid for energy-only and dashed for delivered cost. The gap between
solid and dashed carries the argument.

Three pages: what I did, the number, why the markets differ, what I left out,
and — most importantly — **the questions this raised for their team.**

**Checkpoint:** a memo someone could read in five minutes.

---

## 5. Definition of done

- [ ] Three markets, one full year each, one model
- [ ] Results at five storage sizes, under two charging rules
- [ ] A defensible fee number per market, each with a source and a confidence note
- [ ] One chart that carries the argument without narration
- [ ] Three pages, including a section of questions for Antora
- [ ] Every assumption stated plainly enough that someone could disagree with it

---

## 6. Out of scope — deliberately

Named here because each one is tempting and each one would sink the timeline.

- **Nodal analysis and node geolocation.** Pricing-node coordinates are not
  published; the mapping is a commercial product. Hub and regional prices only.
  This study measures price *shape*, not siting, so nodes are not needed.
- **A siting or opportunity map.** That was an earlier idea. It is a different
  project.
- **Proper optimisation (LP/MILP).** The greedy rule is correct enough and
  explainable. Explainability matters more here than the last 2% of accuracy.
- **45X tax credit modelling.** Different topic, different audience.
- **More than three markets.** Three is enough to show a pattern.
- **Real-time vs day-ahead market layers.** Day-ahead prices only. Note it as a
  limitation.
- **Polishing past one week.** The project buys a better conversation. It is not
  a publication.

---

## 7. Context worth not forgetting

**Antora has already run this play.** The Big Stone Energy Storage Project is a
5 GWh thermal battery next to POET's ethanol biorefinery in Big Stone City, South
Dakota, in Otter Tail Power's MISO territory, charging on curtailed local wind.

Otter Tail filed a **Thermal Market Energy Pricing (TMEP)** rider — hourly MISO
pricing at the point of interconnection, conditional on nearby wind actually
generating. Approved by the South Dakota PUC in July 2025, then North Dakota and
Minnesota.

Its eligibility rules are a useful reality check on my assumptions: minimum
25 MW, load factor below 50%, a contractual tie to a nearby renewable resource,
and registration with MISO as a load-modifying resource.

**Why this matters to the memo:** Antora did not get hourly wholesale prices at
Big Stone because power there was cheap. They got them because a utility filed a
tariff and three regulators approved it. Cheap electricity is abundant; *access
to it* is scarce. That is the thesis.

**Before the conversation:** verify Big Stone and TMEP details against the primary
PUC filings, not press coverage. Being wrong about their flagship project in
front of their policy team is the one unrecoverable error.

---

## 8. Open questions

- Which calendar year? Needs to be complete and available in all three markets.
- Does MISO Minnesota Hub or a different hub better represent the Big Stone area?
- Is the Australian comparison better served by South Australia (most extreme) or
  Victoria (larger industrial base)? Currently South Australia.
- What is the right industrial fee benchmark in Spain — which tariff class
  applies to a load of this size?

---

## 9. Honest limitations to state in the memo

1. **The battery knows the future** in the foresight case. Real operators guess.
   Step 5 quantifies this rather than hiding it.
2. **Day-ahead prices only.** Real participation involves day-ahead and real-time
   layers.
3. **One fee number per market** stands in for a stack of charges that varies by
   customer and connection voltage.
4. **Adding a large flexible load changes prices.** A study of a load this size is
   a snapshot of an equilibrium it would partly disturb.
