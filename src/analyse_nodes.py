"""Does the answer depend on which pricing point we picked?

Decision 24 chose Spain's national price, SA1, and MINN.HUB, and never tested
any of them. Two of the three are now testable:

* **MISO** publishes 2,464 pricing points. MINN.HUB was picked as the hub
  nearest Big Stone, but **OTP.OTP** — Otter Tail Power's own load zone — is
  the settlement point a load on Otter Tail's system would actually pay, and
  Otter Tail is the utility whose Schedule 632 and TMEP tariff this study
  models. Compared against every MISO hub.

* **The NEM** settles at a single price per region, so there is no node
  question inside South Australia. The comparable question is whether South
  Australia's result is a property of *its prices* or of *its tariff*. So the
  SA Power Networks tariff is held fixed and each region's prices are swapped
  in. Anything that survives is the tariff; anything that moves is the prices.

* **Spain** has one national day-ahead price, so there is nothing to vary.

Everything else is held at the base case: 12 hours of storage, 4x charge rate,
1%/day standby loss, published tariffs at 2025 values.

    python src/analyse_nodes.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS, SA_PEAK_WINDOW,
                    MISO_DEMAND_USD_KW_MONTH, MISO_ECO_USD_MWH,
                    MISO_EITE_USD_MWH, MISO_RRCR_DEMAND_USD_KW,
                    MISO_SUMMER_MONTHS, MISO_TCR_DEMAND_USD_KW,
                    miso_network_cost, sa_network_cost)

ROOT = Path(__file__).resolve().parents[1]
P, NODES = ROOT / "data" / "processed", ROOT / "data" / "raw" / "miso_nodes"
DEMAND, ST, RATE = 10.0, 120.0, 4.0
LOSS = 1 - (1 - 0.01) ** (1 / 24)
NEM_REGIONS = ["SA1", "NSW1", "QLD1", "VIC1", "TAS1"]


# ---------------------------------------------------------------- MISO nodes

def miso_year(year: int) -> dict[str, pd.Series]:
    """Every pricing point available for one year, hourly, in local time."""
    files = sorted(NODES.glob("nodes_*.csv"))
    files = [f for f in files
             if str(year - 1) in f.name[6:10] or f.name[6:10] == str(year)
             or f.name[6:10] == str(year + 1)]
    files = [f for f in files if abs(int(f.name[6:10]) - year) <= 1]
    if not files:
        return {}
    raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    raw["ts"] = pd.to_datetime(raw["Interval Start"], utc=True).dt.tz_convert(
        "US/Central")
    start = pd.Timestamp(f"{year}-01-01", tz="US/Central")
    end = pd.Timestamp(f"{year + 1}-01-01", tz="US/Central")
    raw = raw[(raw.ts >= start) & (raw.ts < end)]

    out = {}
    for loc, g in raw.groupby("Location"):
        s = (g.sort_values("ts").drop_duplicates("ts", keep="first")
             .set_index("ts")["LMP"])
        if len(s) >= 8700 and s.isna().sum() == 0:
            out[loc] = s
    return out


def miso_costs(prices: np.ndarray, idx: pd.DatetimeIndex) -> tuple[float, float]:
    """Delivered cost per MWh under the standard tariff, and under TMEP."""
    d = len(prices) * DEMAND
    flat = np.full(len(prices), DEMAND)
    ch = schedule(prices, DEMAND, ST, RATE * DEMAND, horizon=24,
                  loss_per_hour=LOSS)

    base = miso_network_cost(flat, idx, d, utility_supplied=True, riders=True)
    inflex = (flat * prices).sum() / d + base.total_per_mwh
    flex = ((ch * prices).sum() / d
            + miso_network_cost(ch, idx, d, utility_supplied=True,
                                riders=True).total_per_mwh)

    # TMEP bills demand on an agreed Baseline Demand, taken as 10 MW.
    cap_fixed = 282.0 * 12
    for m in range(1, 13):
        rr = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                      else "winter"]
        rr += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap_fixed += DEMAND * 1000 * rr
    tmep = (((ch * prices).sum()
             + ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)
             + cap_fixed) / d)
    return (100 * (inflex - flex) / inflex, 100 * (inflex - tmep) / inflex)


def run_miso() -> None:
    years = sorted({int(f.name[6:10]) for f in NODES.glob("nodes_*.csv")})
    years = [y for y in years if len(miso_year(y)) > 1]
    if not years:
        print("No node data — run fetch_miso_nodes.py first.\n")
        return

    print("=" * 78)
    print("MISO — nine pricing points, same tariff, same battery")
    print("=" * 78)
    print("\nFlexibility saving vs the inflexible electric counterfactual, "
          "under TMEP\n")

    rows: dict[str, dict[int, float]] = {}
    std: dict[str, dict[int, float]] = {}
    for y in years:
        for loc, s in miso_year(y).items():
            a, b = miso_costs(s.to_numpy(), s.index)
            std.setdefault(loc, {})[y] = a
            rows.setdefault(loc, {})[y] = b

    order = sorted(rows, key=lambda l: -np.mean(list(rows[l].values())))
    print(f"  {'pricing point':<16}" + "".join(f"{y:>9}" for y in years)
          + f"{'mean':>9}")
    for loc in order:
        vals = [rows[loc].get(y) for y in years]
        mark = "  <- used" if loc == "MINN.HUB" else (
            "  <- Otter Tail" if loc == "OTP.OTP" else "")
        print(f"  {loc:<16}"
              + "".join(f"{v:>8.1f}%" if v is not None else f"{'—':>9}"
                        for v in vals)
              + f"{np.mean([v for v in vals if v is not None]):>8.1f}%" + mark)

    print("\n\nSame nine points under the STANDARD tariff (no TMEP)\n")
    print(f"  {'pricing point':<16}" + "".join(f"{y:>9}" for y in years)
          + f"{'mean':>9}")
    for loc in order:
        vals = [std[loc].get(y) for y in years]
        print(f"  {loc:<16}"
              + "".join(f"{v:>8.1f}%" if v is not None else f"{'—':>9}"
                        for v in vals)
              + f"{np.mean([v for v in vals if v is not None]):>8.1f}%")

    print("\n  Every point negative under the standard tariff means the finding")
    print("  is about the tariff, not about where in MISO you stand.\n")


# ---------------------------------------------------------------- NEM regions

def run_nem(year: int = 2025) -> None:
    print("=" * 78)
    print(f"The NEM — five regions, SA Power Networks tariff held fixed, {year}")
    print("=" * 78)
    print("\n  The NEM settles one price per region, so there is no node choice")
    print("  inside South Australia. What can be tested is whether the result")
    print("  comes from SA's prices or from SA's tariff — so the tariff is")
    print("  held fixed and only the prices change.\n")

    print(f"  {'region':<10}{'neg. hrs':>10}{'spread':>10}"
          f"{'inflexible':>12}{'flexible':>10}{'saving':>9}")
    out = {}
    for r in NEM_REGIONS:
        f = P / (f"prices_sa_{year}.csv" if r == "SA1"
                 else f"prices_nem_{r}_{year}.csv")
        if not f.exists():
            continue
        d = pd.read_csv(f)
        d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(
            "Australia/Adelaide")
        s = d.set_index("ts")["price_aud_mwh"]
        pr, idx = s.to_numpy(), s.index
        tot = len(pr) * DEMAND

        blk = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
               & np.isin(idx.month, list(SA_PEAK_MONTHS)))
        flat = np.full(len(pr), DEMAND)
        ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, ST,
                      np.where(blk, 0.0, RATE * DEMAND), horizon=6,
                      loss_per_hour=LOSS)

        inflex = (flat * pr).sum() / tot + sa_network_cost(
            flat, idx, tot).total_per_mwh
        flex = (ch * pr).sum() / tot + sa_network_cost(
            ch, idx, tot).total_per_mwh
        sv = 100 * (inflex - flex) / inflex
        out[r] = sv

        # Mean daily spread: the screening statistic the study proposes.
        day = pd.Series(pr, index=idx).groupby(idx.date)
        spread = (day.max() - day.min()).mean()
        neg = 100 * (pr < 0).mean()
        print(f"  {r:<10}{neg:>9.1f}%{spread:>10.0f}{inflex:>12.2f}"
              f"{flex:>10.2f}{sv:>8.1f}%")

    if out:
        print(f"\n  Range across regions: {min(out.values()):.1f}% "
              f"to {max(out.values()):.1f}%. South Australia is "
              f"{'the highest' if out.get('SA1') == max(out.values()) else 'not the highest'}.")
    print()


def main() -> None:
    run_nem()
    run_miso()
    print("Spain has a single national day-ahead price, so there is no")
    print("pricing-point choice to test.")


if __name__ == "__main__":
    main()
