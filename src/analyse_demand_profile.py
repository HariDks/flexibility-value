"""Does the answer survive a factory that does not run flat out all year?

Decision 7 held demand constant at 10 MW, 24 hours a day, 365 days a year. Real
plants stop: most take an annual maintenance turnaround, and many run five days
a week rather than seven. This tests five profiles against the base case.

The point is not that one profile is right. It is that **stopping cuts both
ways**, and the two directions pull against each other:

* Idle hours are hours you do not have to buy power in — and if they fall in
  expensive hours, that helps the inflexible plant more than the battery,
  because the battery was already avoiding them.
* But **capacity charges do not stop when the plant does.** They are billed on
  the peak you set while running, and a plant that runs less spreads the same
  fixed charge over less heat. That is exactly the mechanism this whole study
  is about, so a shutdown should make it worse, not better.

    python src/analyse_demand_profile.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS,
                    SA_PEAK_WINDOW, MISO_ECO_USD_MWH, MISO_EITE_USD_MWH,
                    MISO_DEMAND_USD_KW_MONTH, MISO_RRCR_DEMAND_USD_KW,
                    MISO_SUMMER_MONTHS, MISO_TCR_DEMAND_USD_KW,
                    miso_network_cost, sa_network_cost, spain_network_cost,
                    spain_periods)

P = Path(__file__).resolve().parents[1] / "data" / "processed"
RATED, ST, RATE = 10.0, 120.0, 4.0
LOSS = 1 - (1 - 0.01) ** (1 / 24)
YEAR = 2025
SHUTDOWN_WEEKS = 2


def load(stem: str, col: str, tz: str, yr: int = YEAR) -> pd.Series:
    d = pd.read_csv(P / f"{stem}_{yr}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


# ------------------------------------------------------------------ profiles

def shutdown_mask(idx: pd.DatetimeIndex, start_month: int,
                  weeks: int = SHUTDOWN_WEEKS) -> np.ndarray:
    """True during a maintenance turnaround starting on the 1st of a month."""
    start = pd.Timestamp(year=idx[0].year, month=start_month, day=1,
                         tz=idx.tz)
    return (idx >= start) & (idx < start + pd.Timedelta(weeks * 7, unit="D"))


def profile(idx: pd.DatetimeIndex, weekends: bool = True,
            shutdown_month: int | None = None,
            hours: tuple[int, int] | None = None) -> np.ndarray:
    """Hourly heat demand in MWh.

    weekends        False stops the plant on Saturday and Sunday
    shutdown_month  month a two-week turnaround begins, None for no turnaround
    hours           (start, end) restricts to a shift, e.g. (6, 22)
    """
    d = np.full(len(idx), RATED)
    if not weekends:
        d[idx.dayofweek >= 5] = 0.0
    if hours is not None:
        d[~((idx.hour >= hours[0]) & (idx.hour < hours[1]))] = 0.0
    if shutdown_month is not None:
        d[shutdown_mask(idx, shutdown_month)] = 0.0
    return d


PROFILES = {
    "continuous 24/7/365": dict(),
    "+ 2-week turnaround": dict(shutdown_month=8),
    "five-day week": dict(weekends=False),
    "five-day + turnaround": dict(weekends=False, shutdown_month=8),
    "day shift, five-day": dict(weekends=False, hours=(6, 22)),
}


# ------------------------------------------------------------------- markets

def spain(dem: np.ndarray, s: pd.Series) -> tuple[float, float, float]:
    idx, pr = s.index, s.to_numpy()
    per = spain_periods(idx)
    eff = pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    total = dem.sum()
    cap = np.where(np.isin(per, (4, 5, 6)), RATE, 1) * RATED
    ch = schedule(eff, dem, ST, cap, horizon=24, loss_per_hour=LOSS)
    inflex = (dem * pr).sum() / total + spain_network_cost(
        dem, idx, total).total_per_mwh
    n = spain_network_cost(ch, idx, total)
    return inflex, (ch * pr).sum() / total + n.total_per_mwh, n.capacity_per_mwh


def south_australia(dem: np.ndarray, s: pd.Series) -> tuple[float, float, float]:
    idx, pr = s.index, s.to_numpy()
    total = dem.sum()
    blk = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
           & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    ch = schedule(pr + SA_ENERGY_AUD_MWH, dem, ST,
                  np.where(blk, 0.0, RATE * RATED), horizon=6,
                  loss_per_hour=LOSS)
    inflex = (dem * pr).sum() / total + sa_network_cost(
        dem, idx, total).total_per_mwh
    n = sa_network_cost(ch, idx, total)
    return inflex, (ch * pr).sum() / total + n.total_per_mwh, n.capacity_per_mwh


def miso(dem: np.ndarray, s: pd.Series) -> tuple[float, float, float]:
    idx, pr = s.index, s.to_numpy()
    total = dem.sum()
    ch = schedule(pr, dem, ST, RATE * RATED, horizon=24, loss_per_hour=LOSS)
    inflex = (dem * pr).sum() / total + miso_network_cost(
        dem, idx, total, utility_supplied=True, riders=True).total_per_mwh

    # TMEP bills demand on the agreed Baseline Demand of 10 MW, whether or not
    # the plant is running that month - a fixed charge, so a shutdown spreads it
    # over less heat.
    cap_fixed = 282.0 * 12
    for m in range(1, 13):
        rr = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                      else "winter"]
        rr += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap_fixed += RATED * 1000 * rr
    flex = ((ch * pr).sum() + ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)
            + cap_fixed) / total
    return inflex, flex, cap_fixed / total


MARKETS = [
    ("Spain (EUR)", spain, lambda: load("prices_spain", "price_eur_mwh",
                                        "Europe/Madrid")),
    ("South Australia (AUD)", south_australia,
     lambda: load("prices_sa", "price_aud_mwh", "Australia/Adelaide")),
    ("MISO under TMEP (USD)", miso, lambda: load("prices_miso",
                                                 "price_usd_mwh", "US/Central")),
]


def main() -> None:
    print(f"Five demand profiles, {YEAR}, everything else at the base case\n")
    print("  A 10 MW plant running flat out delivers 87,600 MWh of heat a year.")
    print("  Each profile below delivers less, and the tariff notices.\n")

    series = {name: get() for name, _, get in MARKETS}
    idx0 = series["Spain (EUR)"].index
    for label, kw in PROFILES.items():
        d = profile(idx0, **kw)
        print(f"  {label:<24}{d.sum():>9,.0f} MWh"
              f"{100 * d.sum() / (len(d) * RATED):>8.0f}% utilisation")

    for mkt, fn, _ in MARKETS:
        s = series[mkt]
        print(f"\n\n{'=' * 74}\n{mkt}\n{'=' * 74}\n")
        print(f"  {'profile':<24}{'inflexible':>12}{'flexible':>11}"
              f"{'saving':>9}{'of which capacity':>20}")
        base = None
        for label, kw in PROFILES.items():
            dem = profile(s.index, **kw)
            try:
                inflex, flex, cap = fn(dem, s)
            except RuntimeError as exc:
                print(f"  {label:<24}{'infeasible':>12}   {exc.args[0][:38]}")
                continue
            sv = 100 * (inflex - flex) / inflex
            base = sv if base is None else base
            print(f"  {label:<24}{inflex:>12.2f}{flex:>11.2f}{sv:>8.1f}%"
                  f"{cap:>16.2f}/MWh")
        print(f"\n  Saving at the base case {base:.1f}%; "
              f"the spread across profiles is what matters.")

    # --------------------------------------------------- turnaround timing
    print(f"\n\n{'=' * 74}")
    print("Does it matter WHEN the plant shuts down?")
    print(f"{'=' * 74}\n")
    print(f"  A two-week turnaround starting on the 1st of each month.\n")
    print(f"  {'market':<24}" + "".join(f"{m:>6}" for m in
                                        ("Jan", "Mar", "May", "Jul", "Sep", "Nov"))
          + f"{'range':>9}")
    for mkt, fn, _ in MARKETS:
        s = series[mkt]
        vals = {}
        for m in range(1, 13):
            dem = profile(s.index, shutdown_month=m)
            try:
                inflex, flex, _ = fn(dem, s)
            except RuntimeError:
                continue
            vals[m] = 100 * (inflex - flex) / inflex
        shown = [vals.get(m) for m in (1, 3, 5, 7, 9, 11)]
        rng = max(vals.values()) - min(vals.values())
        print(f"  {mkt:<24}"
              + "".join(f"{v:>5.1f}%" if v is not None else f"{'—':>6}"
                        for v in shown)
              + f"{rng:>8.1f}pt")

    print("\n  A small range means the timing of the turnaround is not a")
    print("  decision this analysis is sensitive to.")


if __name__ == "__main__":
    main()
