"""What is TMEP worth at each agreed Baseline Demand?

Otter Tail's Thermal Market Energy Pricing tariff bills demand on a **Baseline
Demand** agreed in the service agreement. The tariff does not say what that
number is, so the headline TMEP result is a fact about the tariff plus an
assumption about a negotiation, and the assumption is worth more than the fact.

This sweeps it. The figures appeared in `RESULTS.md` for a long time without a
script behind them, which meant they could not be regenerated or checked.

    python src/analyse_tmep_baseline.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (MISO_CUSTOMER_USD_MONTH, MISO_DEMAND_USD_KW_MONTH,
                    MISO_ECO_USD_MWH, MISO_EITE_USD_MWH,
                    MISO_RRCR_DEMAND_USD_KW, MISO_SUMMER_MONTHS,
                    MISO_TCR_DEMAND_USD_KW, miso_network_cost)

P = Path(__file__).resolve().parents[1] / "data" / "processed"
DEMAND, STORAGE_H, RATE, YEAR = 10.0, 12.0, 4.0, 2025
LOSS = 1 - (1 - 0.01) ** (1 / 24)
BASELINES = (10.0, 15.0, 20.0, 40.0)


def demand_charge_per_year(billed_mw: float) -> float:
    """Twelve monthly demand charges on an agreed figure, plus the riders."""
    total = MISO_CUSTOMER_USD_MONTH * 12
    for m in range(1, 13):
        rate = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                        else "winter"]
        rate += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        total += billed_mw * 1000 * rate
    return total


def main() -> None:
    d = pd.read_csv(P / f"prices_miso_{YEAR}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert("US/Central")
    s = d.set_index("ts")["price_usd_mwh"]
    idx, pr = s.index, s.to_numpy()
    delivered = len(pr) * DEMAND

    # The counterfactual buys its power FROM THE UTILITY, so its energy cost is
    # the schedule's own kWh charge plus the Energy Adjustment and supply
    # rider, all of which miso_network_cost already returns when
    # utility_supplied is set. Adding a wholesale term on top would count the
    # energy twice.
    flat = np.full(len(pr), DEMAND)
    inflex = miso_network_cost(flat, idx, delivered, utility_supplied=True,
                               riders=True).total_per_mwh

    ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, RATE * DEMAND, horizon=24,
                  loss_per_hour=LOSS)
    energy = ((ch * pr).sum()
              + ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH))

    print(f"Otter Tail TMEP, {YEAR}, at {RATE:.0f}x charge rate\n")
    print("  Demand is billed on a figure agreed in the service agreement.")
    print("  The tariff does not specify it, so it is swept here.\n")
    print(f"  inflexible counterfactual   {inflex:7.2f} USD/MWh of heat\n")
    print(f"  {'agreed baseline':<28}{'delivered':>11}{'vs inflexible':>15}")
    for b in BASELINES:
        total = (energy + demand_charge_per_year(b)) / delivered
        note = ""
        if b == DEMAND:
            note = "   firm load, the study's assumption"
        elif b == float(RATE * DEMAND):
            note = "   the metered peak, i.e. no agreement"
        print(f"  {b:>10.0f} MW{'':<15}{total:>11.2f}"
              f"{100 * (inflex - total) / inflex:>14.1f}%{note}")

    print("\n  The mechanism is the finding. The agreed number is where the")
    print("  value is actually decided, and it is not in the tariff.")


if __name__ == "__main__":
    main()
