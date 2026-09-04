"""The gas business case, every year — not just 2025.

The original comparison ran on 2025 alone while prices ran 25 market-years.
That hid the only real stress test available: **2022**, when Spanish industrial
gas averaged 93.25 EUR/MWh against 43.25 in 2025. Whether the battery's
advantage widened or collapsed that year is not obvious in advance, because
electricity spiked too — Spain's mean wholesale price ran 167.5 EUR/MWh in 2022
against 65.3 in 2025.

Two things are reported for every year:

* **Gas alone against the battery.** Fully sourced, no carbon price needed.
* **The carbon price at which they tie.** Derived, so it needs no carbon series
  — which matters, because no citable machine-readable EU ETS annual series was
  found. The actual carbon price is quoted only for 2025, where it is sourced.

    python src/analyse_gas_years.py
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS,
                    SA_PEAK_WINDOW, MISO_DEMAND_USD_KW_MONTH,
                    MISO_ECO_USD_MWH, MISO_EITE_USD_MWH,
                    MISO_RRCR_DEMAND_USD_KW, MISO_SUMMER_MONTHS,
                    MISO_TCR_DEMAND_USD_KW, sa_network_cost,
                    spain_network_cost, spain_periods)

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
DEMAND, ST, RATE = 10.0, 120.0, 4.0
LOSS = 1 - (1 - 0.01) ** (1 / 24)
BOILER_EFF = 0.85
GAS_TCO2_PER_MWH = 0.202

# Carbon actually charged, 2025. Australia's Safeguard prescribed unit price is
# recent — the reformed scheme starts 2023-24 — and the carbon tax it replaced
# was repealed in 2014, so there is no comparable Australian series for the
# earlier years. Those years are honestly a zero-carbon world.
CARBON_2025 = {"Spain": 75.0, "South Australia": 36.99, "MISO": 0.0}
CURRENCY = {"Spain": "EUR", "South Australia": "AUD", "MISO": "USD"}


def series(stem: str, col: str, tz: str, year: int) -> pd.Series:
    f = P / f"{stem}_{year}.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


def battery(market: str, year: int) -> float | None:
    """Delivered cost of heat from the battery, on that market's real tariff."""
    if market == "Spain":
        s = series("prices_spain", "price_eur_mwh", "Europe/Madrid", year)
        if s is None:
            return None
        idx, pr = s.index, s.to_numpy()
        per = spain_periods(idx)
        eff = pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per])
        cap = np.where(np.isin(per, (4, 5, 6)), RATE, 1) * DEMAND
        ch = schedule(eff, DEMAND, ST, cap, horizon=24, loss_per_hour=LOSS)
        d = len(pr) * DEMAND
        return (ch * pr).sum() / d + spain_network_cost(ch, idx, d).total_per_mwh

    if market == "South Australia":
        s = series("prices_sa", "price_aud_mwh", "Australia/Adelaide", year)
        if s is None:
            return None
        idx, pr = s.index, s.to_numpy()
        blk = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
               & np.isin(idx.month, list(SA_PEAK_MONTHS)))
        ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, ST,
                      np.where(blk, 0.0, RATE * DEMAND), horizon=6,
                      loss_per_hour=LOSS)
        d = len(pr) * DEMAND
        return (ch * pr).sum() / d + sa_network_cost(ch, idx, d).total_per_mwh

    s = series("prices_miso", "price_usd_mwh", "US/Central", year)
    if s is None:
        return None
    idx, pr = s.index, s.to_numpy()
    ch = schedule(pr, DEMAND, ST, RATE * DEMAND, horizon=24, loss_per_hour=LOSS)
    d = len(pr) * DEMAND
    cap = 282.00 * 12
    for m in range(1, 13):
        rr = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                      else "winter"]
        rr += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap += DEMAND * 1000 * rr           # TMEP baseline demand, not peak
    return ((ch * pr).sum() + ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)
            + cap) / d


def main() -> None:
    gas = json.loads((P / "gas_prices.json").read_text())

    print("The gas business case, every year the prices allow\n")
    print("  Gas converted at 85% boiler efficiency. 'Breakeven carbon' is the")
    print("  price at which delivered heat from gas equals the battery, derived")
    print("  from the two costs, so it needs no carbon-price series.\n")

    summary = {}
    for market in ("Spain", "South Australia", "MISO"):
        cur = CURRENCY[market]
        print(f"\n{market} ({cur} per MWh of heat)")
        print(f"  {'year':>6}{'gas price':>11}{'gas heat':>10}{'battery':>10}"
              f"{'vs gas':>9}{'breakeven carbon':>19}")
        rows = []
        for year in range(2016, 2026):
            g = gas[market].get(str(year))
            b = battery(market, year)
            if g is None or b is None:
                continue
            gas_heat = g / BOILER_EFF
            vs = 100 * (gas_heat - b) / gas_heat
            be = (b * BOILER_EFF - g) / GAS_TCO2_PER_MWH
            rows.append((year, g, gas_heat, b, vs, be))
            print(f"  {year:>6}{g:>11.2f}{gas_heat:>10.2f}{b:>10.2f}"
                  f"{vs:>8.1f}%{be:>16.2f}/t")
        summary[market] = rows

        wins = sum(1 for r in rows if r[4] > 0)
        print(f"\n  Battery beats gas on fuel alone in {wins} of {len(rows)} "
              f"years.")
        be_all = [r[5] for r in rows]
        print(f"  Breakeven carbon runs {min(be_all):.2f} to {max(be_all):.2f} "
              f"{cur}/t; 2025 actual is {CARBON_2025[market]:.2f}.")

    # ---------------------------------------------------------------- 2022
    print("\n\n" + "=" * 72)
    print("2022 — the stress test the single-year study skipped")
    print("=" * 72 + "\n")
    print(f"  {'market':<18}{'gas 2022':>10}{'gas 2025':>10}"
          f"{'vs gas 2022':>13}{'vs gas 2025':>13}")
    for market, rows in summary.items():
        r22 = next((r for r in rows if r[0] == 2022), None)
        r25 = next((r for r in rows if r[0] == 2025), None)
        if not r22 or not r25:
            continue
        print(f"  {market:<18}{r22[1]:>10.2f}{r25[1]:>10.2f}"
              f"{r22[4]:>12.1f}%{r25[4]:>12.1f}%")

    print("\n  Gas roughly doubled in 2022, but so did wholesale electricity —")
    print("  which is what the battery buys. The comparison is not a one-way")
    print("  bet on gas being expensive.")

    print("\n\n  A note on Australian carbon. The Safeguard Mechanism's")
    print("  prescribed unit price is recent, and the carbon tax it replaced")
    print("  was repealed in 2014, so the earlier Australian years are honestly")
    print("  a zero-carbon world. Where the breakeven is positive and no carbon")
    print("  price existed, gas won — not because the economics changed but")
    print("  because the policy did not yet exist.")


if __name__ == "__main__":
    main()
