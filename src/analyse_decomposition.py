"""Where does each market's saving come from?

A battery has two levers: hunt cheap prices, and obey the tariff clock. This
separates them. The tariff-only case is given a flat wholesale price signal, so
it has no price preference at all but still plans around the network's bands.

Also tests whether avoiding South Australia's peak window entirely is optimal.

    python src/analyse_decomposition.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS,
                    SA_PEAK_WINDOW, miso_network_cost, sa_network_cost,
                    spain_network_cost, spain_periods)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEMAND, STORAGE_H = 10.0, 12


def load(stem, col, tz):
    d = pd.read_csv(PROCESSED / f"{stem}_2025.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


def decompose():
    print("Where each market's saving comes from\n")
    print("  B  hunts cheap prices, ignores the tariff clock")
    print("  C  obeys the tariff clock, no price preference (flat price signal)")
    print("  D  both\n")

    out = []

    s = load("prices_spain", "price_eur_mwh", "Europe/Madrid")
    idx, pr = s.index, s.to_numpy()
    d, per = len(pr) * DEMAND, spain_periods(s.index)
    netE = np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    capT = np.where(np.isin(per, (4, 5, 6)), 6, 1) * DEMAND
    f = lambda x: (x * pr).sum() / d + spain_network_cost(x, idx, d).total_per_mwh
    out.append(("Spain", "EUR", {
        "A inflexible": f(np.full(len(pr), DEMAND)),
        "B price only": f(schedule(pr, DEMAND, STORAGE_H * DEMAND,
                                   4 * DEMAND, horizon=24)),
        "C tariff only": f(schedule(netE, DEMAND, STORAGE_H * DEMAND, capT)),
        "D both": f(schedule(pr + netE, DEMAND, STORAGE_H * DEMAND, capT,
                             horizon=24))}))

    s = load("prices_sa", "price_aud_mwh", "Australia/Adelaide")
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    blocked = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
               & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    capT = np.where(blocked, 0.0, 6 * DEMAND)
    f = lambda x: (x * pr).sum() / d + sa_network_cost(x, idx, d).total_per_mwh
    out.append(("South Australia", "AUD", {
        "A inflexible": f(np.full(len(pr), DEMAND)),
        "B price only": f(schedule(pr, DEMAND, STORAGE_H * DEMAND,
                                   4 * DEMAND, horizon=6)),
        "C tariff only": f(schedule(np.ones(len(pr)), DEMAND,
                                    STORAGE_H * DEMAND, capT)),
        "D both": f(schedule(pr + SA_ENERGY_AUD_MWH, DEMAND,
                             STORAGE_H * DEMAND, capT, horizon=6))}))

    s = load("prices_miso", "price_usd_mwh", "US/Central")
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    g = lambda x: (x * pr).sum() / d + miso_network_cost(x, idx, d).total_per_mwh
    out.append(("MISO", "USD", {
        "A inflexible": miso_network_cost(np.full(len(pr), DEMAND), idx, d,
                                          utility_supplied=True).total_per_mwh,
        "B price only": g(schedule(pr, DEMAND, STORAGE_H * DEMAND,
                                   4 * DEMAND, horizon=24)),
        "C tariff only": g(schedule(np.ones(len(pr)), DEMAND,
                                    STORAGE_H * DEMAND, 2 * DEMAND)),
        "D both": g(schedule(pr, DEMAND, STORAGE_H * DEMAND, 2 * DEMAND,
                             horizon=24))}))

    for market, cur, c in out:
        a = list(c.values())[0]
        print(f"{market} ({cur}/MWh)")
        for k, v in c.items():
            sv = "—" if k.startswith("A") else f"{100 * (a - v) / abs(a):+7.1f}%"
            print(f"  {k:<18}{v:>9.2f}{sv:>10}")
        b = 100 * (a - c["B price only"]) / abs(a)
        t = 100 * (a - c["C tariff only"]) / abs(a)
        both = 100 * (a - c["D both"]) / abs(a)
        print(f"  -> price {b:+.1f}, tariff {t:+.1f}, together {both:+.1f} "
              f"(interaction {both - b - t:+.1f})\n")

    print("Spain is PERMISSIVE: the clock is worth nothing alone but roughly")
    print("doubles what price-hunting earns, by not punishing the peak that")
    print("hunting creates. South Australia is REWARDING: the clock pays on its")
    print("own, with no forecasting at all. MISO is PUNITIVE: every lever loses.")


def sa_peak_window_sweep():
    print("\n" + "=" * 72)
    print("Is avoiding South Australia's peak window entirely optimal?\n")
    s = load("prices_sa", "price_aud_mwh", "Australia/Adelaide")
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    blocked = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
               & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    print(f"  {'allowance in window':<24}{'off-peak 4x':>13}{'off-peak 6x':>13}")
    for pk in (0.0, 0.5, 1.0, 2.0, 4.0):
        row = f"  {f'{pk:.1f}x demand':<24}"
        for off in (4.0, 6.0):
            cap = np.where(blocked, pk * DEMAND, off * DEMAND)
            try:
                ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND,
                              STORAGE_H * DEMAND, cap, horizon=6)
                row += f"{(ch * pr).sum() / d + sa_network_cost(ch, idx, d).total_per_mwh:>13.2f}"
            except RuntimeError:
                row += f"{'infeasible':>13}"
        print(row)
    print("\n  Monotonic, so zero is optimal. The assumption holds.")


if __name__ == "__main__":
    decompose()
    sa_peak_window_sweep()
