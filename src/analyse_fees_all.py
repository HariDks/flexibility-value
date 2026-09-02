"""Step 4: the delivered bill in all three markets, on published tariffs.

Each market gets the tariff class a 40-60 MW industrial load would actually
take, and each battery is allowed to play that tariff as well as it can.

    python src/analyse_fees_all.py --year 2025
"""

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_WINDOW,
                    miso_network_cost, sa_network_cost, spain_network_cost,
                    spain_periods)

ROOT = Path(__file__).resolve().parents[1]
FIGS, PROCESSED = ROOT / "output" / "figures", ROOT / "data" / "processed"
DEMAND, STORAGE_H = 10.0, 12

INK, INK2, MUTED, RULE = "#0b0d0f", "#4c5257", "#7d8288", "#dde2e6"
SURFACE = "#fdfdfe"
C_POWER, C_NETEN, C_NETCAP = "#2a78d6", "#9ec5f4", "#eb6834"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": RULE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130,
})


def load(stem, col, tz, year):
    d = pd.read_csv(PROCESSED / f"{stem}_{year}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    year = ap.parse_args().year

    panels, rows = [], []

    # ---------------- Spain ----------------
    s = load("prices_spain", "price_eur_mwh", "Europe/Madrid", year)
    idx, pr = s.index, s.to_numpy()
    deliv = len(pr) * DEMAND
    per = spain_periods(idx)
    eff = pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    flat = np.full(len(pr), DEMAND)
    naive = schedule(pr, DEMAND, STORAGE_H * DEMAND, 4 * DEMAND, horizon=24)
    cap = np.where(np.isin(per, (4, 5, 6)), 6, 1) * DEMAND
    aware = schedule(eff, DEMAND, STORAGE_H * DEMAND, cap, horizon=24)
    es = []
    for name, d in (("Normal\nfactory", flat), ("Battery\nignoring tariff", naive),
                    ("Battery\nplaying tariff", aware)):
        nc = spain_network_cost(d, idx, deliv)
        es.append((name, float((d * pr).sum() / deliv),
                   nc.energy_per_mwh, nc.capacity_per_mwh))
    panels.append(("Spain", "EUR", es, "6.1TD published rates, 24h visibility"))

    # ---------------- South Australia ----------------
    s = load("prices_sa", "price_aud_mwh", "Australia/Adelaide", year)
    idx, pr = s.index, s.to_numpy()
    deliv = len(pr) * DEMAND
    flat = np.full(len(pr), DEMAND)
    naive = schedule(pr, DEMAND, STORAGE_H * DEMAND, 4 * DEMAND, horizon=6)
    cap = np.where(np.isin(idx.hour, list(SA_PEAK_WINDOW)), 0.0, 6 * DEMAND)
    aware = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, STORAGE_H * DEMAND,
                     cap, horizon=6)
    sa = []
    for name, d, flex in (("Normal\nfactory", flat, False),
                          ("Battery\nignoring tariff", naive, False),
                          ("Battery\nplaying tariff", aware, False)):
        nc = sa_network_cost(d, idx, deliv, flexible=flex)
        sa.append((name, float((d * pr).sum() / deliv),
                   nc.energy_per_mwh, nc.capacity_per_mwh))
    panels.append(("South Australia", "AUD", sa,
                   "Sub Transmission published rates, 6h visibility"))

    # ---------------- MISO ----------------
    s = load("prices_miso", "price_usd_mwh", "US/Central", year)
    idx, pr = s.index, s.to_numpy()
    deliv = len(pr) * DEMAND
    flat = np.full(len(pr), DEMAND)
    mi = []
    nc = miso_network_cost(flat, idx, deliv, utility_supplied=True)
    mi.append(("Normal\nfactory", 0.0, nc.energy_per_mwh, nc.capacity_per_mwh))
    for label, mult in (("Battery\nignoring tariff", 4), ("Battery\nplaying tariff", 1.5)):
        d = schedule(pr, DEMAND, STORAGE_H * DEMAND, mult * DEMAND, horizon=24)
        nc = miso_network_cost(d, idx, deliv)
        mi.append((label, float((d * pr).sum() / deliv), nc.energy_per_mwh,
                   nc.capacity_per_mwh))
    panels.append(("MISO (Otter Tail)", "USD", mi,
                   "Schedule 632 + Energy Adjustment + riders"))

    # ---------------- report ----------------
    for market, cur, data, note in panels:
        base = sum(data[0][1:])
        print(f"\n{market} — {note}   ({cur}/MWh of heat)")
        print(f"  {'':<24}{'power':>9}{'net.en':>9}{'net.cap':>9}{'TOTAL':>9}{'vs factory':>12}")
        for name, p, ne, ncap in data:
            tot = p + ne + ncap
            v = "—" if tot == base else f"{100 * (base - tot) / abs(base):+.1f}%"
            print(f"  {name.replace(chr(10), ' '):<24}{p:>9.2f}{ne:>9.2f}"
                  f"{ncap:>9.2f}{tot:>9.2f}{v:>12}")
            rows.append({"market": market, "currency": cur, "case": name.replace("\n", " "),
                         "power": p, "net_energy": ne, "net_capacity": ncap, "total": tot})
    pd.DataFrame(rows).to_csv(PROCESSED / f"results_fees_{year}.csv", index=False)

    # ---------------- figure ----------------
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.9))
    for ax, (market, cur, data, note) in zip(axes, panels):
        labels = [d[0] for d in data]
        parts = np.array([[d[1], d[2], d[3]] for d in data])
        bottom = np.zeros(len(data))
        for i, (lab, colour) in enumerate([("Price of the power", C_POWER),
                                           ("Network: per unit", C_NETEN),
                                           ("Network: connection", C_NETCAP)]):
            ax.bar(labels, parts[:, i], 0.6, bottom=bottom, color=colour,
                   edgecolor=SURFACE, linewidth=2,
                   label=lab if ax is axes[0] else None)
            bottom += parts[:, i]
        for x, tot in enumerate(bottom):
            ax.annotate(f"{tot:.0f}", (x, tot), textcoords="offset points",
                        xytext=(0, 5), ha="center", fontsize=10.5,
                        fontweight="bold", color=INK)
        ax.axhline(bottom[0], color=MUTED, lw=1, ls=(0, (3, 3)), zorder=1)
        ax.set_ylim(0, max(bottom) * 1.22)
        ax.set_title(f"{market}\n{cur} per MWh", loc="left", fontsize=11,
                     fontweight="bold", color=INK, pad=8)
        ax.grid(axis="y", color="#eef1f3", lw=1)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelsize=8.5)

    axes[0].legend(frameon=False, fontsize=9, loc="upper left",
                   bbox_to_anchor=(0, -0.12), ncol=3)
    fig.suptitle("What the network bill does to flexibility",
                 x=0.062, y=1.045, ha="left", fontsize=13.5,
                 fontweight="bold", color=INK)
    fig.text(0.062, 0.975, "Same factory, same heat, same year — on each market's "
             "own published tariff, with the forward view that market actually gives. "
             "Dashed line is what a normal factory pays.",
             fontsize=9.5, color=INK2, ha="left")
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))

    out = FIGS / f"all_{year}_network_bill.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"\n  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
