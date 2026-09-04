"""How large would connection capital cost have to be to change the answer?

Everything else in this study is operating cost. A battery that charges faster
needs a physically larger grid connection — transformers, switchgear, protection,
possibly network reinforcement — and that is capital, paid once, regardless of
how the tariff treats it.

That cost is site-specific and not published in any general form, so it is not
asserted here. Instead this computes the **threshold**: how much a bigger
connection would have to cost before the slower, cheaper-to-connect option wins.

    python src/analyse_connection_capex.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS,
                    SA_PEAK_WINDOW, MISO_DEMAND_USD_KW_MONTH, MISO_ECO_USD_MWH,
                    MISO_EITE_USD_MWH, MISO_RRCR_DEMAND_USD_KW,
                    MISO_SUMMER_MONTHS, MISO_TCR_DEMAND_USD_KW,
                    miso_network_cost, sa_network_cost, spain_network_cost,
                    spain_periods)

P = Path(__file__).resolve().parents[1] / "data" / "processed"
DEMAND, ST, LOSS = 10.0, 120.0, 1 - (1 - 0.01) ** (1 / 24)
ANNUAL_MWH = 8760 * DEMAND
RATES = (2.0, 4.0, 6.0)

# Capital recovery factor: what fraction of a one-off cost must be recovered
# each year. Three combinations spanning ordinary infrastructure finance.
FINANCE = {"6% over 25 yr": 0.0782, "8% over 20 yr": 0.1019, "10% over 15 yr": 0.1315}


def load(stem, col, tz, yr=2025):
    d = pd.read_csv(P / f"{stem}_{yr}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


def costs_by_rate():
    out = {}

    s = load("prices_spain", "price_eur_mwh", "Europe/Madrid")
    idx, pr = s.index, s.to_numpy()
    d, per = len(pr) * DEMAND, spain_periods(s.index)
    eff = pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    out["Spain (EUR)"] = {}
    for r in RATES:
        cap = np.where(np.isin(per, (4, 5, 6)), r, 1) * DEMAND
        ch = schedule(eff, DEMAND, ST, cap, horizon=24, loss_per_hour=LOSS)
        out["Spain (EUR)"][r] = ((ch * pr).sum() / d
                                 + spain_network_cost(ch, idx, d).total_per_mwh)

    s = load("prices_sa", "price_aud_mwh", "Australia/Adelaide")
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    blk = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
           & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    out["South Australia (AUD)"] = {}
    for r in RATES:
        try:
            ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, ST,
                          np.where(blk, 0.0, r * DEMAND), horizon=6,
                          loss_per_hour=LOSS)
        except RuntimeError:
            continue
        out["South Australia (AUD)"][r] = ((ch * pr).sum() / d
                                           + sa_network_cost(ch, idx, d).total_per_mwh)

    s = load("prices_miso", "price_usd_mwh", "US/Central")
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    cap_fixed = 282.0 * 12
    for m in range(1, 13):
        rr = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                      else "winter"]
        rr += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap_fixed += DEMAND * 1000 * rr
    out["MISO under TMEP (USD)"] = {}
    for r in RATES:
        ch = schedule(pr, DEMAND, ST, r * DEMAND, horizon=24, loss_per_hour=LOSS)
        out["MISO under TMEP (USD)"][r] = (
            ((ch * pr).sum() + ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)
             + cap_fixed) / d)
    return out


def main() -> None:
    out = costs_by_rate()

    print("Delivered cost by charge rate — operating cost only, per MWh of heat\n")
    print(f"  {'market':<26}" + "".join(f"{f'{r:.0f}x':>10}" for r in RATES))
    for mkt, byr in out.items():
        print(f"  {mkt:<26}"
              + "".join(f"{byr[r]:>10.2f}" if r in byr else f"{'n/a':>10}"
                        for r in RATES))

    print("\n\nWhat a faster connection buys, per year\n")
    print("  A 10 MW heat load charging at 2x needs a 20 MW connection, at 4x a")
    print("  40 MW one, at 6x a 60 MW one. Each step adds 20 MW of connection.\n")
    print(f"  {'market':<26}{'step':>10}{'saving/MWh':>13}{'saving/yr':>15}")
    steps = {}
    for mkt, byr in out.items():
        for lo, hi in ((2.0, 4.0), (4.0, 6.0)):
            if lo not in byr or hi not in byr:
                continue
            per_mwh = byr[lo] - byr[hi]
            per_yr = per_mwh * ANNUAL_MWH
            steps[(mkt, lo, hi)] = (per_mwh, per_yr)
            print(f"  {mkt:<26}{f'{lo:.0f}x->{hi:.0f}x':>10}"
                  f"{per_mwh:>13.2f}{per_yr:>15,.0f}")

    print("\n\nBreak-even connection cost — how much the extra 20 MW would have")
    print("to cost, one-off, before the SLOWER option wins\n")
    print(f"  {'market':<26}{'step':>10}"
          + "".join(f"{k:>18}" for k in FINANCE))
    for (mkt, lo, hi), (_, per_yr) in steps.items():
        row = f"  {mkt:<26}{f'{lo:.0f}x->{hi:.0f}x':>10}"
        for crf in FINANCE.values():
            if per_yr <= 0:
                row += f"{'slower wins':>18}"
            else:
                # 20 MW of extra connection = 20,000 kW
                row += f"{per_yr / crf / 20_000:>15,.0f}/kW"
        print(row)

    print("\n  Read as: the extra 20 MW of connection would have to cost more")
    print("  than this per kW before charging slower is the better choice.")
    print("  Below it, faster charging pays for its own connection.")


if __name__ == "__main__":
    main()
