"""Same country, same battery, two networks.

A 25-60 MW industrial site in South Australia connects to SA Power Networks at
33/66 kV. ElectraNet's exit points are almost all bulk supply points into SA
Power Networks' own network, plus legacy SA Water pumping loads at 3.3-11 kV.
SAPN's published rates are NUoS = DUoS + TUoS, so transmission cost is already
inside them.

The direct-connection case is kept anyway, because it proves the argument inside
a single country. ElectraNet bills capacity on agreed maximum demand, every day,
with no peak window - structurally the same as MISO.

    python src/analyse_networks.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS, SA_PEAK_WINDOW,
                    sa_network_cost)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEMAND, STORAGE_H = 10.0, 12
GST = 1.10   # ElectraNet's schedule is GST-inclusive; SA Power Networks' is not

# ElectraNet Prescribed Transmission Service Price Schedule, 1 Jul 2025-30 Jun 2026
EN_NONLOC_CAP, EN_NONLOC_EN = 160.866 / GST, 24.994 / GST   # $/MW/day, $/MWh
EN_COMMON_CAP, EN_COMMON_EN = 62.608 / GST, 9.727 / GST
EN_LOCATIONAL = {"Para 66kV": 54.996 / GST,
                 "Brinkworth 33kV": 128.158 / GST,
                 "Ardrossan West 33kV": 194.826 / GST,
                 "Berri 66kV": 227.745 / GST}


def main() -> None:
    d = pd.read_csv(PROCESSED / "prices_sa_2025.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert("Australia/Adelaide")
    s = d.set_index("ts")["price_aud_mwh"]
    idx, pr = s.index, s.to_numpy()
    deliv = len(pr) * DEMAND
    days = len(np.unique(idx.date))
    flat = np.full(len(pr), DEMAND)

    blocked = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
               & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    bat_sapn = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, STORAGE_H * DEMAND,
                        np.where(blocked, 0.0, 6 * DEMAND), horizon=6)
    # Against a charge that ignores the clock there is nothing to dodge.
    bat_en = schedule(pr, DEMAND, STORAGE_H * DEMAND, 6 * DEMAND, horizon=6)

    print("SOUTH AUSTRALIA — does it matter which network you connect to?\n")
    print("A) SA Power Networks sub-transmission (33/66 kV).")
    print("   Peak Demand measured 17:00-21:00, November to March only.")
    base = None
    for name, dr in (("inflexible", flat), ("battery", bat_sapn)):
        nc = sa_network_cost(dr, idx, deliv)
        t = (dr * pr).sum() / deliv + nc.total_per_mwh
        if base is None:
            base = t
        tag = "" if name == "inflexible" else f"   saving {100 * (base - t) / base:5.1f}%"
        print(f"   {name:<12}{t:>9.2f}  (energy {(dr * pr).sum() / deliv:6.2f}"
              f" + network {nc.total_per_mwh:6.2f}){tag}")

    print("\nB) Connected directly to ElectraNet transmission.")
    print("   Capacity billed on AGREED MAXIMUM DEMAND, every day, no window.")
    en_cap_common = EN_NONLOC_CAP + EN_COMMON_CAP
    en_energy = EN_NONLOC_EN + EN_COMMON_EN
    print(f"   {'connection point':<22}{'inflexible':>12}{'battery':>10}{'result':>10}")
    for loc, loccap in EN_LOCATIONAL.items():
        capd = loccap + en_cap_common

        def tot(dr):
            return ((dr * pr).sum() / deliv + en_energy
                    + float(dr.max(initial=0.0)) * capd * days / deliv)

        f, b = tot(flat), tot(bat_en)
        print(f"   {loc:<22}{f:>12.2f}{b:>10.2f}{100 * (f - b) / f:>9.1f}%")

    print(f"\n   capacity {en_cap_common:.1f} + locational $/MW/day, "
          f"energy {en_energy:.2f} $/MWh, both ex-GST")
    print("\nSame country, prices, year and battery. Only the design of the")
    print("demand charge changes, and it changes the sign of the answer.")


if __name__ == "__main__":
    main()
