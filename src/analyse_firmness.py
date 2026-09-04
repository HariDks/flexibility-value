"""What does firmness cost, and does anything actually pay for it?

Decision 4 priced storage as an arbitrage asset only and said reliability value
and multi-day firming were "not modelled". This models the economics of them.

The physics of firmness is trivial and needs no simulation: a tank holding N
hours of heat rides through an N-hour interruption. The hard question is
economic — **who pays for hour 25 through hour 100?** — and that is answerable
entirely from published prices.

Three things are computed:

1. **What the energy market pays for depth.** The marginal value of each extra
   hour of storage, at each market's real forecast horizon. It goes to zero.

2. **What capacity and demand-response products pay**, from the auctions
   themselves, together with the duration each one actually requires.

3. **The wedge neither pays for** — and what the customer would have to value
   firm heat at to cover it, swept across storage capital costs rather than
   assuming one.

    python src/analyse_firmness.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS,
                    SA_PEAK_WINDOW, MISO_ECO_USD_MWH, MISO_EITE_USD_MWH,
                    MISO_DEMAND_USD_KW_MONTH, MISO_RRCR_DEMAND_USD_KW,
                    MISO_SUMMER_MONTHS, MISO_TCR_DEMAND_USD_KW,
                    sa_network_cost, spain_network_cost, spain_periods)

P = Path(__file__).resolve().parents[1] / "data" / "processed"
DEMAND, RATE, YEAR = 10.0, 4.0, 2025
LOSS = 1 - (1 - 0.01) ** (1 / 24)
ANNUAL_MWH = 8760 * DEMAND
SIZES = (4, 8, 12, 24, 48, 96, 168)
CRF = 0.1019                      # 8% over 20 years, the study's middle case

# ---------------------------------------------------------------------------
# Published prices for capacity and demand response. Every figure below is
# quoted from the market operator's own results posting.
# ---------------------------------------------------------------------------

# MISO Planning Resource Auction, annualised, North/Central (Local Resource
# Zones 1-7, which includes Zone 1 — Minnesota and the Dakotas).
#   2025/26: summer $666.50, fall $91.60, winter $33.20, spring $69.88
#            -> annualised $217/MW-day
#            https://cdn.misoenergy.org/2025 PRA Results Posting 20250529...pdf
#   2026/27: summer $424.30 (LRZ 1-7), fall $33.92, winter $35.97,
#            spring $7.61 -> annualised $126.19/MW-day
#            misoenergy.org 2026 news release
MISO_PRA_USD_MW_DAY = {"2025/26": 217.00, "2026/27": 126.19}

# MISO requires a Load Modifying Resource to sustain its reduction for at least
# four consecutive hours — "the expected minimum runtime for these resources",
# MISO LMR whitepaper, January 2025.
MISO_LMR_MIN_HOURS = 4

# Spain, Servicio de Respuesta Activa de la Demanda (SRAD). Availability is
# auctioned at a marginal price per MW per assigned hour; activation is paid
# separately at the balancing price.
#   2025 (auction 14 Nov 2024): 1,148 MW assigned over 4,371 hours at
#        56.43 EUR/MW  ->  EUR 246,655 per MW-year
#   2026 H1 (auction 28 Nov 2025): 1,725 MW over 2,279 hours at 65 EUR/MW
#   https://api.esios.ree.es/documents/2530/download
#   https://api.esios.ree.es/documents/3689/download
SRAD = {"2025": (56.43, 4371), "2026 H1": (65.00, 2279)}
SRAD_RESPONSE_MIN = 15            # minutes, the required response time


def load(stem: str, col: str, tz: str) -> pd.Series:
    d = pd.read_csv(P / f"{stem}_{YEAR}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


# ------------------------------------------- 1. what depth earns on arbitrage

def spain_cost(st_h: float, s: pd.Series) -> float:
    idx, pr = s.index, s.to_numpy()
    per = spain_periods(idx)
    eff = pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    cap = np.where(np.isin(per, (4, 5, 6)), RATE, 1) * DEMAND
    ch = schedule(eff, DEMAND, st_h * DEMAND, cap, horizon=24,
                  loss_per_hour=LOSS)
    d = len(pr) * DEMAND
    return (ch * pr).sum() / d + spain_network_cost(ch, idx, d).total_per_mwh


def sa_cost(st_h: float, s: pd.Series) -> float:
    idx, pr = s.index, s.to_numpy()
    blk = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
           & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, st_h * DEMAND,
                  np.where(blk, 0.0, RATE * DEMAND), horizon=6,
                  loss_per_hour=LOSS)
    d = len(pr) * DEMAND
    return (ch * pr).sum() / d + sa_network_cost(ch, idx, d).total_per_mwh


def miso_cost(st_h: float, s: pd.Series) -> float:
    idx, pr = s.index, s.to_numpy()
    ch = schedule(pr, DEMAND, st_h * DEMAND, RATE * DEMAND, horizon=24,
                  loss_per_hour=LOSS)
    cap_fixed = 282.0 * 12
    for m in range(1, 13):
        rr = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                      else "winter"]
        rr += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap_fixed += DEMAND * 1000 * rr
    d = len(pr) * DEMAND
    return (((ch * pr).sum()
             + ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)
             + cap_fixed) / d)


MARKETS = [
    ("Spain (EUR)", spain_cost, lambda: load("prices_spain", "price_eur_mwh",
                                             "Europe/Madrid")),
    ("South Australia (AUD)", sa_cost,
     lambda: load("prices_sa", "price_aud_mwh", "Australia/Adelaide")),
    ("MISO under TMEP (USD)", miso_cost,
     lambda: load("prices_miso", "price_usd_mwh", "US/Central")),
]


def gap_stats(s: pd.Series) -> dict[str, float]:
    """Length of stretches with no cheap power, cheap being the 30th pct."""
    cheap = s <= s.quantile(0.30)
    runs, n = [], 0
    for c in cheap.to_numpy():
        if c:
            if n:
                runs.append(n)
            n = 0
        else:
            n += 1
    if n:
        runs.append(n)
    r = np.array(runs)
    return {"median": float(np.median(r)), "p99": float(np.percentile(r, 99)),
            "max": float(r.max())}


def shed_availability(s: pd.Series, hours: int) -> dict[str, float]:
    """How much could the battery actually shed if called?

    SRAD pays for a *reduction* against a metered baseline, so a battery can
    only deliver what it happens to be drawing at the time. This measures that
    over the dearest `hours` hours of the year — the plausible risk window in
    which a system operator would call the service.
    """
    idx, pr = s.index, s.to_numpy()
    per = spain_periods(idx)
    eff = pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    cap = np.where(np.isin(per, (4, 5, 6)), RATE, 1) * DEMAND
    ch = schedule(eff, DEMAND, 12 * DEMAND, cap, horizon=24, loss_per_hour=LOSS)
    risk = pr >= np.sort(pr)[-hours]
    return {"share_at_rating": float((ch[risk] >= DEMAND - 1e-6).mean()),
            "mean_draw": float(ch[risk].mean())}


def main() -> None:
    series = {m: get() for m, _, get in MARKETS}

    print("=" * 76)
    print("1. WHAT THE ENERGY MARKET PAYS FOR DEPTH")
    print("=" * 76)
    print("\n  Delivered cost per MWh of heat at each tank size, and what the")
    print("  extra hours between one size and the next are worth per year.\n")

    for mkt, fn, _ in MARKETS:
        s = series[mkt]
        costs = {}
        for h in SIZES:
            try:
                costs[h] = fn(h, s)
            except RuntimeError:
                # Too small to be operable at all. South Australia's strategy
                # blocks charging for four hours every summer evening, so a
                # four-hour tank cannot bridge its own peak window.
                costs[h] = None
        print(f"  {mkt}")
        print(f"    {'tank':>6}{'cost/MWh':>11}{'extra hours':>13}"
              f"{'worth/yr':>13}{'per extra hour':>16}")
        prev_h = None
        for h in SIZES:
            if costs[h] is None:
                print(f"    {h:>4}h{'infeasible':>11}"
                      f"   cannot bridge the blocked peak window")
                continue
            if prev_h is None or costs[prev_h] is None:
                print(f"    {h:>4}h{costs[h]:>11.2f}")
            else:
                gain = (costs[prev_h] - costs[h]) * ANNUAL_MWH
                per = gain / ((h - prev_h) * DEMAND)     # per MWh of extra tank
                print(f"    {h:>4}h{costs[h]:>11.2f}{h - prev_h:>12}h"
                      f"{gain:>13,.0f}{per:>15,.0f}/MWh")
            prev_h = h
        print()

    print("  The last column is what an extra MWh of tank earns per year from")
    print("  price arbitrage. It reaches zero at each market's forecast")
    print("  horizon and stays there. Depth beyond that earns nothing here.\n")

    # ----------------------------------------------------------------------
    print("=" * 76)
    print("2. WHAT CAPACITY AND DEMAND-RESPONSE PRODUCTS PAY")
    print("=" * 76)
    print("\n  A 10 MW flexible load, if fully accredited. Published auction")
    print("  results, not estimates.\n")

    print("  MISO Planning Resource Auction, annualised, Local Resource Zones 1-7")
    print(f"    {'year':<12}{'$/MW-day':>11}{'10 MW earns/yr':>17}"
          f"{'per MWh of heat':>18}")
    for yr, price in MISO_PRA_USD_MW_DAY.items():
        rev = DEMAND * price * 365
        print(f"    {yr:<12}{price:>11.2f}{rev:>17,.0f}"
              f"{rev / ANNUAL_MWH:>17.2f}")
    print(f"    duration required: {MISO_LMR_MIN_HOURS} consecutive hours\n")

    print("  Spain SRAD, availability payment (activation paid separately)")
    print(f"    {'auction':<12}{'EUR/MW-h':>11}{'hours':>8}{'10 MW earns':>15}"
          f"{'per MWh of heat':>18}")
    for yr, (price, hours) in SRAD.items():
        rev = DEMAND * price * hours
        scale = ANNUAL_MWH if yr == "2025" else ANNUAL_MWH / 2
        print(f"    {yr:<12}{price:>11.2f}{hours:>8,}{rev:>15,.0f}"
              f"{rev / scale:>17.2f}")
    print(f"    response required: {SRAD_RESPONSE_MIN} minutes; no duration "
          f"floor is set by the\n    auction, and reduction is measured "
          f"against a metered baseline\n")

    # That last point is the binding one, so it is measured rather than noted.
    av = shed_availability(series["Spain (EUR)"], SRAD["2025"][1])
    top = DEMAND * SRAD["2025"][0] * SRAD["2025"][1] / ANNUAL_MWH
    print("    Those figures are an UPPER BOUND and should not be quoted bare.")
    print("    A load can only shed what it is drawing. Over the 4,371 dearest")
    print(f"    hours of 2025 the battery is drawing its full 10 MW in only")
    print(f"    {100 * av['share_at_rating']:.1f}% of them, and averages "
          f"{av['mean_draw']:.2f} MW.")
    print(f"    So the realistic range is roughly "
          f"{top * av['share_at_rating']:.2f} to "
          f"{top * av['mean_draw'] / DEMAND:.2f} per MWh of heat, not "
          f"{top:.2f}.")
    print("    A battery paid to be available would also reschedule itself to")
    print("    be drawing when called, which this does not model.\n")

    print("  The NEM has no capacity market. It is energy-only: a flexible load")
    print("  monetises itself through the spot price, which this study already")
    print("  counts, or through the Wholesale Demand Response Mechanism, which")
    print("  also settles at the spot price. So South Australia pays nothing")
    print("  extra for firmness beyond what is already in these numbers.\n")

    # ----------------------------------------------------------------------
    print("=" * 76)
    print("3. THE WEDGE NOBODY PAYS FOR")
    print("=" * 76)
    print("\n  How long a stretch must firm heat cover? From the same price")
    print("  data, stretches with no cheap power available:\n")
    print(f"  {'market':<24}{'median':>9}{'99th pct':>11}{'longest':>10}")
    for mkt, _, _ in MARKETS:
        g = gap_stats(series[mkt])
        print(f"  {mkt:<24}{g['median']:>8.0f}h{g['p99']:>10.0f}h"
              f"{g['max']:>9.0f}h")

    print("\n  So three different numbers answer three different questions:\n")
    print(f"    {MISO_LMR_MIN_HOURS:>4} hours   what MISO's capacity market "
          f"requires, and pays for")
    print("      24 hours   where arbitrage value stops, set by the day-ahead"
          " horizon")
    print("   99-164 hours   what covering the 99th-percentile stretch takes")
    print("\n  Everything between 24 hours and 164 hours earns nothing from any")
    print("  market in this study. It is bought by the customer's own")
    print("  requirement for heat that does not stop.\n")

    print("  What that unpaid depth costs, going from a 24-hour tank to a")
    print("  100-hour one — 760 MWh of extra storage on a 10 MW plant:\n")
    print(f"  {'storage capex':<18}{'extra capex':>14}{'annualised':>13}"
          f"{'per MWh of heat':>18}")
    for c in (5, 10, 20, 50):
        capex = 760 * 1000 * c
        print(f"  {f'{c}/kWh':<18}{capex:>14,.0f}{capex * CRF:>13,.0f}"
              f"{capex * CRF / ANNUAL_MWH:>17.2f}")

    best = max(MISO_PRA_USD_MW_DAY.values()) * DEMAND * 365 / ANNUAL_MWH
    print(f"\n  Against that, the most any market here pays for capacity is")
    print(f"  {best:.2f} per MWh of heat — and it pays that for a 4-hour tank")
    print(f"  just as readily as for a 100-hour one.\n")

    print("  Read as a breakeven: the customer must value uninterrupted heat")
    print("  at more than the figures in the last column for the extra depth")
    print("  to pay. That value is site-specific — it is the cost of stopping")
    print("  the plant — and is not asserted here.")


if __name__ == "__main__":
    main()
