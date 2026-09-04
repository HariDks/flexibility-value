# Does the answer depend on which pricing point we picked?

Decision 24 chose Spain's national price, SA1, and MINN.HUB — and never tested
any of them. This is that test.

Run with `python src/analyse_nodes.py`. Everything else is held at the base
case: 12 hours of storage, 4× charge rate, 1%/day standby loss, published
tariffs at 2025 values.

**Spain** settles one national day-ahead price, so there is nothing to vary.

---

## MISO — nine pricing points

MISO publishes 2,464 pricing points. MINN.HUB was picked as the published hub
nearest Big Stone City. But MISO also publishes **`OTP.OTP`** — the load zone
of **Otter Tail Power itself**, the utility whose Schedule 632 and TMEP tariff
this study models. For a *load*, the load zone is the settlement point; a hub
is a trading construct. So OTP.OTP is the right answer and MINN.HUB was the
approximation.

Four years, chosen to span the period: 2018 and 2020 and 2022 from the monthly
archives, 2025 from the daily reports.

### Saving vs the inflexible electric counterfactual, under TMEP

| pricing point | 2018 | 2020 | 2022 | 2025 | mean |
|---|---|---|---|---|---|
| **OTP.OTP** (Otter Tail's own zone) | 51.4% | 56.2% | 52.0% | 50.9% | **52.7%** |
| **MINN.HUB** (what the study used) | 51.5% | 55.5% | 51.3% | 52.1% | **52.6%** |
| ILLINOIS.HUB | 50.7% | 53.5% | 45.5% | 51.7% | 50.3% |
| LOUISIANA.HUB | 51.7% | 53.3% | 44.0% | 50.4% | 49.9% |
| MS.HUB | 51.8% | 53.3% | 44.2% | 50.2% | 49.9% |
| ARKANSAS.HUB | 50.4% | 53.4% | 44.1% | 50.2% | 49.5% |
| TEXAS.HUB | 50.2% | 53.8% | 43.7% | 49.9% | 49.4% |
| INDIANA.HUB | 49.8% | 52.5% | 43.5% | 49.6% | 48.9% |
| MICHIGAN.HUB | 49.0% | 52.7% | 43.4% | 49.5% | 48.7% |

**MINN.HUB was a good proxy.** Against the correct settlement point it is out
by **0.1 points** on the four-year mean, and never by more than 1.2 points in
any single year. The whole nine-point range spans 48.7% to 52.7% — four points
across a market 1,500 miles wide.

### The same nine points under the standard tariff, without TMEP

| pricing point | 2018 | 2020 | 2022 | 2025 | mean |
|---|---|---|---|---|---|
| OTP.OTP | −48.4% | −56.9% | −31.1% | −31.5% | −42.0% |
| MINN.HUB | −48.6% | −56.4% | −31.8% | −34.3% | −42.8% |
| ILLINOIS.HUB | −45.7% | −52.7% | −25.8% | −36.8% | −40.3% |
| LOUISIANA.HUB | −39.1% | −53.5% | −27.5% | −38.3% | −39.6% |
| MS.HUB | −41.6% | −54.2% | −28.5% | −42.4% | −41.7% |
| ARKANSAS.HUB | −46.9% | −54.8% | −29.2% | −43.2% | −43.5% |
| TEXAS.HUB | −45.0% | −50.3% | −28.4% | −40.2% | −41.0% |
| INDIANA.HUB | −43.8% | −52.2% | −23.9% | −34.8% | −38.7% |
| MICHIGAN.HUB | −44.6% | −51.5% | −26.1% | −35.3% | −39.4% |

**Negative in 36 cases out of 36.** Nine pricing points, four years, every one
a loss without TMEP and every one a gain with it. **The MISO finding is about
the tariff, not about where in MISO you stand.** That is the strongest form the
claim can take, and it is now tested rather than assumed.

---

## The NEM — five regions, one tariff

The NEM settles a single price per region, so there is no node choice *inside*
South Australia. The comparable question is different and more useful: **is the
South Australian result a property of its prices or of its tariff?**

So the SA Power Networks tariff is held fixed and each region's prices are
swapped in. Anything that survives is the tariff; anything that moves is the
prices. (This is a thought experiment — a Tasmanian factory does not pay SAPN —
but it is the only way to separate the two.)

2025, base case throughout:

| region | negative hours | mean daily spread | inflexible | flexible | saving |
|---|---|---|---|---|---|
| **SA1** | 29.7% | A$393 | 120.12 | 60.23 | **49.9%** |
| VIC1 | 23.7% | A$282 | 111.30 | 62.65 | 43.7% |
| NSW1 | 12.3% | A$431 | 136.73 | 78.56 | 42.5% |
| QLD1 | 18.6% | A$311 | 118.27 | 70.04 | 40.8% |
| TAS1 | 3.7% | A$159 | 129.42 | 100.15 | 22.6% |

### What this says

**The mechanism is not South Australian.** Every region gains, and the floor is
22.6% — in Tasmania, a hydro system with almost no negative pricing. Give a
flexible load a time-aware demand charge and it wins everywhere in the NEM.

**But the size of the win is.** South Australia is the best of the five, by
6 points over the runner-up and 27 over the worst. **So SA numbers should be
quoted as the top of a range, not as a typical result** — the study has been
using the most flexibility-friendly grid in the country.

### A correction to the screening rule

Headline finding 4 says flexibility value tracks **intraday spread**, not price
level. Across time within one market, that held. Across five regions at one
time, **raw spread ranks them wrong**: New South Wales has the *largest* mean
daily spread of any region (A$431) and only the third-best saving.

Testing four candidate statistics against the five regions' savings:

| statistic | rank correlation with saving |
|---|---|
| mean price level | −0.30 |
| mean daily spread (max − min) | +0.50 |
| daily mean minus the six cheapest hours | +0.70 |
| **that gap as a % of the mean price** | **+0.90** |

**The refined rule: how far the cheap hours sit below the day's average, as a
fraction of the average.** Not the peak-to-trough range.

The reason is that max − min is set by *spikes*, and a battery does not sell
into spikes — it only buys cheap. New South Wales has violent evening peaks
that inflate its spread without making its cheap hours any cheaper relative to
its own average. South Australia's cheap hours sit 109% below its daily mean
(it goes negative 30% of the time); Tasmania's sit 40% below.

The original claim survives in substance — **level does not matter, movement
does** — but "movement" has to be measured as the depth of the cheap hours, not
the height of the expensive ones. This is a sharper rule and it costs nothing
to apply: both numbers come from the same price file.
