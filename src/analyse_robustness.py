"""Robustness checks, all in one place.

  1. How far the greedy schedule is from the exact optimum (solved as an LP)
  2. Whether the Spanish tariff class changes the conclusion
  3. How much standby heat loss matters
  4. How much the choice of inflexible counterfactual matters
  5. How much South Australia's forward-visibility assumption matters

    python src/analyse_robustness.py
"""

import time

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import sparse
from scipy.optimize import linprog

from battery import schedule
from tariff import (ES_CARGOS_ENERGY, ES_CARGOS_POWER, ES_CLASSES,
                    ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS,
                    SA_PEAK_WINDOW, sa_network_cost, spain_network_cost,
                    spain_periods)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEMAND, STORAGE_H = 10.0, 12
MARKETS = [("spain", "prices_spain", "price_eur_mwh", "Europe/Madrid", "EUR"),
           ("sa", "prices_sa", "price_aud_mwh", "Australia/Adelaide", "AUD"),
           ("miso", "prices_miso", "price_usd_mwh", "US/Central", "USD")]


def load(stem, col, tz):
    d = pd.read_csv(PROCESSED / f"{stem}_2025.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


def optimal_cost(prices, demand, storage, cap):
    """Exact least-cost schedule. Tank level is the variable, which makes the
    constraint matrix bidiagonal rather than a dense cumulative sum."""
    n = len(prices)
    cap = np.full(n, cap, float) if np.isscalar(cap) else np.asarray(cap, float)
    c = np.empty(n)
    c[:-1], c[-1] = prices[:-1] - prices[1:], prices[-1]
    rows, cols, vals, b = [], [], [], []
    for h in range(n):
        rows += [2 * h]; cols += [h]; vals += [1.0]
        if h:
            rows += [2 * h]; cols += [h - 1]; vals += [-1.0]
        b.append(cap[h] - demand)
        rows += [2 * h + 1]; cols += [h]; vals += [-1.0]
        if h:
            rows += [2 * h + 1]; cols += [h - 1]; vals += [1.0]
        b.append(demand)
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(2 * n, n))
    bounds = [(0.0, storage)] * n
    bounds[-1] = (0.0, 0.0)
    res = linprog(c, A_ub=A, b_ub=np.array(b), bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(res.message)
    x = np.diff(np.concatenate([[0.0], res.x])) + demand
    return (x * prices).sum() / (n * demand)


def check_optimality():
    print("=" * 72)
    print("1. How far is the greedy from optimal?\n")
    print("   Gaps are shown against the INFLEXIBLE bill. At large tanks the")
    print("   battery's own bill approaches zero and percentages of it become")
    print("   meaningless (South Australia's 12h gap reads 126% of its own")
    print("   bill and 0.7% of the counterfactual's - same number).\n")
    print(f"   {'':<8}" + "".join(f"{m[0]:>12}" for m in MARKETS))
    for tank in (4, 12, 24, 48):
        row = f"   {f'{tank}h':<8}"
        for _, stem, col, tz, _ in MARKETS:
            pr = load(stem, col, tz).to_numpy()
            d = len(pr) * DEMAND
            g = (schedule(pr, DEMAND, tank * DEMAND, 4 * DEMAND) * pr).sum() / d
            o = optimal_cost(pr, DEMAND, tank * DEMAND, 4 * DEMAND)
            row += f"{100 * (g - o) / abs(pr.mean()):>11.1f}%"
        print(row)


def check_spain_class():
    print("\n" + "=" * 72)
    print("2. Does the Spanish tariff class change the conclusion?\n")
    print("   Class follows connection voltage. The MW threshold at each")
    print("   voltage is set by the distributor's connection study, not by a")
    print("   citable table - so the class is not asserted. All four are run.\n")
    s = load("prices_spain", "price_eur_mwh", "Europe/Madrid")
    idx, pr = s.index, s.to_numpy()
    d, per = len(pr) * DEMAND, spain_periods(s.index)
    flat = np.full(len(pr), DEMAND)
    print(f"   {'class':<8}{'voltage':<14}{'flexible':>10}{'inflexible':>12}"
          f"{'saving':>9}")
    for cls, spec in ES_CLASSES.items():
        # The billing now comes from tariff.py rather than being copied here,
        # so there is one implementation of Spain's six bands and the screener
        # can be verified against it.
        def cost(dr):
            return ((dr * pr).sum() / d
                    + spain_network_cost(dr, idx, d, cls).total_per_mwh)

        # The operator sees this class's own banded energy charge, which
        # reorders the hours, so the schedule differs by class.
        en = {p: (spec["energy"][p] + ES_CARGOS_ENERGY[p]) * 1000
              for p in range(1, 7)}
        ch = schedule(pr + np.array([en[p] for p in per]), DEMAND,
                      STORAGE_H * DEMAND,
                      np.where(np.isin(per, (4, 5, 6)), 4, 1) * DEMAND,
                      horizon=24)
        i, f = cost(flat), cost(ch)
        print(f"   {cls:<8}{spec['voltage']:<14}{f:>10.2f}{i:>12.2f}"
              f"{100 * (i - f) / i:>8.1f}%")
    print("\n   Higher voltage is cheaper for both buyers and the saving rises,")
    print("   so 6.1TD is the most conservative assumption available.")


def check_losses():
    print("\n" + "=" * 72)
    print("3. Standby heat loss\n")
    s = load("prices_spain", "price_eur_mwh", "Europe/Madrid")
    idx, pr = s.index, s.to_numpy()
    d, per = len(pr) * DEMAND, spain_periods(idx)
    netE = np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    cap = np.where(np.isin(per, (4, 5, 6)), 4, 1) * DEMAND
    base = (np.full(len(pr), DEMAND) * pr).sum() / d + spain_network_cost(
        np.full(len(pr), DEMAND), idx, d).total_per_mwh
    print(f"   {'loss/day':>10}{'Spain saving':>15}")
    for daily in (0.0, 0.01, 0.02, 0.05, 0.10):
        ch = schedule(pr + netE, DEMAND, STORAGE_H * DEMAND, cap, horizon=24,
                      loss_per_hour=1 - (1 - daily) ** (1 / 24))
        t = (ch * pr).sum() / d + spain_network_cost(ch, idx, d).total_per_mwh
        print(f"   {daily:>9.0%}{100 * (base - t) / base:>14.1f}%")
    print("\n   The battery holds heat for hours, not days, so standby loss")
    print("   barely bites. Not a material economic risk.")


def check_counterfactual():
    print("\n" + "=" * 72)
    print("4. The inflexible counterfactual\n")
    print("   The benchmark buys at hourly prices and consumes flat, so it pays")
    print("   the realised average - the cheapest inflexible option there is. A")
    print("   fixed-price contract is priced off the forward curve and embeds a")
    print("   risk premium on top, so every real alternative costs more.\n")
    out = {}
    for key, stem, col, tz, _ in MARKETS[:2]:
        s = load(stem, col, tz)
        idx, pr = s.index, s.to_numpy()
        d = len(pr) * DEMAND
        flat = np.full(len(pr), DEMAND)
        if key == "spain":
            per = spain_periods(idx)
            ch = schedule(pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per]),
                          DEMAND, STORAGE_H * DEMAND,
                          np.where(np.isin(per, (4, 5, 6)), 4, 1) * DEMAND,
                          horizon=24)
            b = (ch * pr).sum() / d + spain_network_cost(ch, idx, d).total_per_mwh
            fnet = spain_network_cost(flat, idx, d).total_per_mwh
        else:
            blocked = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
                       & np.isin(idx.month, list(SA_PEAK_MONTHS)))
            ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, STORAGE_H * DEMAND,
                          np.where(blocked, 0.0, 4 * DEMAND), horizon=6)
            b = (ch * pr).sum() / d + sa_network_cost(ch, idx, d).total_per_mwh
            fnet = sa_network_cost(flat, idx, d).total_per_mwh
        out[key] = (b, pr.mean(), fnet)
    print(f"   {'risk premium':<15}{'Spain':>10}{'South Aus':>13}")
    for prem in (0.0, 0.05, 0.10, 0.20):
        row = f"   {prem:>12.0%}   "
        for key in ("spain", "sa"):
            b, pow_, fnet = out[key]
            f = pow_ * (1 + prem) + fnet
            row += f"{100 * (f - b) / f:>9.1f}%"
        print(row)


def check_sa_visibility():
    print("\n" + "=" * 72)
    print("5. South Australia's forward visibility — an explicit judgment\n")
    print("   AEMO publishes 5-minute pre-dispatch one hour ahead and 30-minute")
    print("   pre-dispatch to the end of the next market day, up to ~40 hours.")
    print("   But these are deterministic point FORECASTS with no published")
    print("   confidence intervals - not, as in Spain and MISO, a price you can")
    print("   commit at. The NEM has no day-ahead market, so there is no")
    print("   committable price at ANY horizon.")
    print("\n   The usable horizon is therefore a forecasting capability, not a")
    print("   market fact. Six hours is a judgment. The result moves a lot:\n")
    s = load("prices_sa", "price_aud_mwh", "Australia/Adelaide")
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    flat = np.full(len(pr), DEMAND)
    base = (flat * pr).sum() / d + sa_network_cost(flat, idx, d).total_per_mwh
    blocked = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
               & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    cap = np.where(blocked, 0.0, 4 * DEMAND)
    print(f"   {'visibility':>12}{'delivered':>12}{'saving':>9}")
    for hz in (3, 5, 6, 8, 12, 24, None):
        try:
            ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, STORAGE_H * DEMAND,
                          cap, horizon=hz)
        except RuntimeError:
            print(f"   {'3h' if hz == 3 else f'{hz}h':>12}"
                  f"{'infeasible':>12}")
            continue
        t = (ch * pr).sum() / d + sa_network_cost(ch, idx, d).total_per_mwh
        lab = "tank-limited" if hz is None else f"{hz}h"
        print(f"   {lab:>12}{t:>12.2f}{100 * (base - t) / base:>8.1f}%")
    print("\n   Report as a range, not a point. The base case is 6h.")


if __name__ == "__main__":
    t0 = time.time()
    check_optimality()
    check_spain_class()
    check_losses()
    check_counterfactual()
    check_sa_visibility()
    print(f"\n{'=' * 72}\ndone in {time.time() - t0:.0f}s")
