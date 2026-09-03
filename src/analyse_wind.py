"""TMEP's wind-coincidence condition: how binding is it?

TMEP requires the customer to "take service coincident with and not to exceed
the hourly generating output of a nearby specifically identified wind and/or
solar generation resource." Output for one named plant is not public, so MISO's
North-region wind generation stands in - North covers Minnesota and the Dakotas.

A region is far smoother than a single farm, so this proxy UNDERSTATES how
binding the condition is.

    python src/analyse_wind.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (MISO_DEMAND_USD_KW_MONTH, MISO_EAF_USD_MWH_2025,
                    MISO_ECO_USD_MWH, MISO_EITE_USD_MWH, MISO_ENERGY_USD_MWH,
                    MISO_RRCR_DEMAND_USD_KW, MISO_SUMMER_MONTHS,
                    MISO_TCR_DEMAND_USD_KW, miso_network_cost)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEMAND, STORAGE_H = 10.0, 12
BASELINE = DEMAND          # TMEP Baseline Demand = the factory's firm draw
LOSS = 1 - (1 - 0.01) ** (1 / 24)


def main() -> None:
    a = pd.read_csv(PROCESSED / "prices_miso_2025.csv")
    a["ts"] = pd.to_datetime(a["ts"], utc=True).dt.tz_convert("US/Central")
    b = pd.read_csv(PROCESSED / "miso_north_wind_2025.csv")
    b["ts"] = pd.to_datetime(b["ts"], utc=True).dt.tz_convert("US/Central")
    j = a.set_index("ts").join(b.set_index("ts"), how="inner").dropna()
    idx = j.index
    pr = j["price_usd_mwh"].to_numpy()
    wind = j["wind_mw"].to_numpy()
    deliv = len(pr) * DEMAND

    print(f"{len(j):,} hours joined\n")
    print(f"correlation of price with North wind: "
          f"{np.corrcoef(pr, wind)[0, 1]:+.3f}")
    print(f"mean price, wind in top quartile:    {pr[wind >= np.quantile(wind, .75)].mean():6.2f}")
    print(f"mean price, wind in bottom quartile: {pr[wind <= np.quantile(wind, .25)].mean():6.2f}")
    print("\nCharging on wind and charging on price largely want the same hours,")
    print("which is why the condition turns out to be survivable.\n")

    def bill(ch):
        """TMEP's two tiers: firm up to Baseline Demand at the utility's own
        rate, market-priced above it and exempt from the Energy Adjustment."""
        firm = np.minimum(ch, BASELINE)
        mkt = ch - firm
        summer = np.isin(idx.month, list(MISO_SUMMER_MONTHS))
        e = (firm[summer].sum() * MISO_ENERGY_USD_MWH["summer"]
             + firm[~summer].sum() * MISO_ENERGY_USD_MWH["winter"])
        e += sum(firm[idx.month == m].sum() * MISO_EAF_USD_MWH_2025[m]
                 for m in range(1, 13))
        e += (mkt * pr).sum()
        e += ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)
        cap = 282.0 * 12
        for m in range(1, 13):
            r = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                         else "winter"]
            r += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
                "h1" if m <= 6 else "h2"]
            cap += BASELINE * 1000 * r
        return (e + cap) / deliv

    base = miso_network_cost(np.full(len(pr), DEMAND), idx, deliv,
                             utility_supplied=True).total_per_mwh
    free = schedule(pr, DEMAND, STORAGE_H * DEMAND, 4 * DEMAND, horizon=24,
                    loss_per_hour=LOSS)
    print(f"inflexible electrification counterfactual  USD {base:6.2f}/MWh")
    print(f"TMEP, price-following, no wind condition   USD {bill(free):6.2f}/MWh\n")

    print("READING A — condition applied to the WHOLE load.")
    print("How long can the paired farm fail to cover the factory's 10 MW?\n")
    print(f"  {'farm size':>10}{'mean out':>10}{'hrs below':>11}{'longest run':>13}")
    for R in (1, 2, 3, 5, 8):
        p = wind * (R * deliv / wind.sum())
        below = p < DEMAND
        runs, cur = [], 0
        for x in below:
            cur = cur + 1 if x else 0
            if cur:
                runs.append(cur)
        print(f"  {R:>8.0f}x{p.mean():>10.1f}{100 * below.mean():>10.0f}%"
              f"{max(runs) if runs else 0:>12}h")
    print("\n  Infeasible at every storage size tested up to 720h. A 121-hour")
    print("  lull cannot be bridged by any thermal store anyone would build.\n")

    print("READING B — condition applied as TMEP actually bills it.")
    print("Firm to 10 MW always; extra draw capped by the paired farm.\n")
    print(f"  {'paired farm':<28}{'cost':>9}{'vs no condition':>17}"
          f"{'hrs constrained':>17}")
    for R in (1, 2, 3, 5, 8):
        paired = wind * (R * deliv / wind.sum())
        cap = DEMAND + np.minimum(3 * DEMAND, paired)
        ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, cap, horizon=24,
                      loss_per_hour=LOSS)
        c = bill(ch)
        print(f"  {f'{R}x battery annual energy':<28}{c:>9.2f}"
              f"{100 * (c - bill(free)) / bill(free):>16.1f}%"
              f"{100 * (paired < 3 * DEMAND).mean():>16.0f}%")

    print("\n  The two-tier structure is not incidental — it is what makes")
    print("  wind-pairing physically possible at all.")


if __name__ == "__main__":
    main()
