"""Step 4, Spain: what survives once the network bill is included?

Three batteries are compared, all delivering identical heat:

  1. **Energy-only.** Chases the cheapest power and ignores the network bill.
     This is every result up to now.
  2. **Tariff-aware.** Sees the network's energy charge as part of the price,
     and holds itself back during the expensive bands so it does not contract
     capacity there.
  3. **Best of a sweep** over how fast it may draw in cheap bands versus
     expensive ones - the "sweet spot".

    python src/analyse_spain_tariff.py --year 2025
"""

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, CARGOS_RANGE_EUR_MWH,
                    spain_network_cost, spain_periods)

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "output" / "figures"
PROCESSED = ROOT / "data" / "processed"

DEMAND = 10.0
STORAGE_H = 12
CHEAP_PERIODS, PEAK_PERIODS = (4, 5, 6), (1, 2, 3)

INK, INK2, MUTED, RULE = "#0b0d0f", "#4c5257", "#7d8288", "#dde2e6"
SURFACE, BATTERY, FACTORY = "#fdfdfe", "#2a78d6", "#eb6834"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": RULE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130,
})


def bill(draw, idx, prices, cargos):
    delivered = len(prices) * DEMAND
    nc = spain_network_cost(draw, idx, delivered, cargos_eur_mwh=cargos)
    energy = float((draw * prices).sum() / delivered)
    return {"energy": energy, "net_energy": nc.energy_per_mwh,
            "net_capacity": nc.capacity_per_mwh,
            "total": energy + nc.total_per_mwh}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--cargos", type=float, default=None,
                   help="system charges EUR/MWh; default is the midpoint")
    args = p.parse_args()

    cargos = args.cargos if args.cargos is not None else float(
        np.mean(CARGOS_RANGE_EUR_MWH))

    df = pd.read_csv(PROCESSED / f"prices_spain_{args.year}.csv")
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("Europe/Madrid")
    s = df.set_index("ts")["price_eur_mwh"]
    idx, prices = s.index, s.to_numpy()
    per = spain_periods(idx)

    # The price the battery should actually be reacting to: the market price
    # plus what the network charges for energy in that band.
    net_energy = np.array([ES_ENERGY_EUR_MWH[p] + cargos for p in per])
    effective = prices + net_energy

    storage = STORAGE_H * DEMAND
    flat = np.full(len(prices), DEMAND)

    print(f"Spain {args.year}, {STORAGE_H}h tank, "
          f"system charges assumed EUR {cargos:.1f}/MWh\n")

    results = {"Normal factory": bill(flat, idx, prices, cargos)}

    # 1. energy-only, the battery from every previous step
    d1 = schedule(prices, DEMAND, storage, 4 * DEMAND)
    results["Battery, ignores network"] = bill(d1, idx, prices, cargos)

    # 2 & 3. sweep how hard it may pull in cheap versus expensive bands
    rows = []
    for cheap in (2, 3, 4, 6, 8):
        for peak in (1.0, 1.25, 1.5, 2.0, 4.0):
            if peak > cheap:
                continue
            cap = np.where(np.isin(per, CHEAP_PERIODS), cheap, peak) * DEMAND
            try:
                d = schedule(effective, DEMAND, storage, cap)
            except RuntimeError:
                continue
            b = bill(d, idx, prices, cargos)
            rows.append({"cheap": cheap, "peak": peak, **b})

    sweep = pd.DataFrame(rows).sort_values("total")
    best = sweep.iloc[0]
    cap = np.where(np.isin(per, CHEAP_PERIODS), best.cheap, best.peak) * DEMAND
    d3 = schedule(effective, DEMAND, storage, cap)
    results[f"Battery, tariff-aware ({best.cheap:.0f}x cheap / "
            f"{best.peak:.2f}x peak)"] = bill(d3, idx, prices, cargos)

    # ---- report ----------------------------------------------------------
    print(f"  {'':<46}{'power':>8}{'net.en':>8}{'net.cap':>9}{'TOTAL':>9}"
          f"{'saving':>9}")
    base = results["Normal factory"]["total"]
    for name, b in results.items():
        save = 100 * (base - b["total"]) / abs(base)
        print(f"  {name:<46}{b['energy']:>8.2f}{b['net_energy']:>8.2f}"
              f"{b['net_capacity']:>9.2f}{b['total']:>9.2f}"
              + (f"{save:>8.1f}%" if name != "Normal factory" else f"{'—':>9}"))

    print(f"\n  Contracted power by band (MW):")
    print(f"  {'':<28}" + "".join(f"{'P'+str(p):>7}" for p in range(1, 7)))
    for name, d in (("factory", flat), ("ignores network", d1),
                    ("tariff-aware", d3)):
        print(f"  {name:<28}"
              + "".join(f"{d[per == p].max(initial=0):7.1f}" for p in range(1, 7)))

    print(f"\n  Top of the sweep (delivered EUR/MWh):")
    print(f"  {'cheap':>7}{'peak':>7}{'power':>9}{'net.cap':>9}{'TOTAL':>9}")
    for _, r in sweep.head(6).iterrows():
        print(f"  {r.cheap:>6.0f}x{r.peak:>6.2f}x{r.energy:>9.2f}"
              f"{r.net_capacity:>9.2f}{r.total:>9.2f}")

    # ---- sensitivity to the one number we are least sure of ---------------
    print(f"\n  Sensitivity to system charges (the least certain input):")
    print(f"  {'cargos':>8}{'factory':>10}{'battery':>10}{'saving':>9}")
    for c in (CARGOS_RANGE_EUR_MWH[0], cargos, CARGOS_RANGE_EUR_MWH[1]):
        ne = np.array([ES_ENERGY_EUR_MWH[p] + c for p in per])
        dd = schedule(prices + ne, DEMAND, storage, cap)
        fb, bb = bill(flat, idx, prices, c), bill(dd, idx, prices, c)
        print(f"  {c:>7.0f} {fb['total']:>9.2f} {bb['total']:>9.2f}"
              f"{100 * (fb['total'] - bb['total']) / fb['total']:>8.1f}%")

    # ---- figure ----------------------------------------------------------
    labels = ["Normal\nfactory", "Battery\nignoring network",
              "Battery\ntariff-aware"]
    keys = list(results.keys())
    parts = np.array([[results[k]["energy"], results[k]["net_energy"],
                       results[k]["net_capacity"]] for k in keys])

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    bottom = np.zeros(3)
    for i, (lab, colour) in enumerate([
            ("Price of the power", BATTERY),
            ("Network: per unit used", "#9ec5f4"),
            ("Network: for the connection", FACTORY)]):
        ax.bar(labels, parts[:, i], 0.55, bottom=bottom, label=lab,
               color=colour, edgecolor=SURFACE, linewidth=2)
        bottom += parts[:, i]

    for x, tot in enumerate(bottom):
        ax.annotate(f"EUR {tot:.0f}", (x, tot), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=10.5,
                    fontweight="bold", color=INK)

    ax.set_ylabel("EUR / MWh of heat delivered")
    ax.set_ylim(0, max(bottom) * 1.2)
    ax.grid(axis="y", color="#eef1f3", lw=1)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.set_title(f"Spain {args.year}: what the network bill does",
                 loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=30)
    ax.text(0, 1.035, "Same factory, same heat, same year. Only the buying "
                      "strategy changes.",
            transform=ax.transAxes, fontsize=9.5, color=INK2)

    out = FIGS / f"spain_{args.year}_network_bill.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    sweep.to_csv(PROCESSED / f"sweep_spain_{args.year}.csv", index=False)
    print(f"\n  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
