"""Step 3: run the same battery over all three markets.

Savings are reported as percentages because the three markets price in three
currencies. Converting them to a common currency would add an exchange-rate
assumption that changes the numbers without improving the argument; the
percentage is what the comparison actually rests on.

Still energy price only, and the battery still knows the future.

    python src/analyse_all.py --year 2025
"""

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from battery import evaluate

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "output" / "figures"
PROCESSED = ROOT / "data" / "processed"

DEMAND = 10.0
STORAGE_HOURS = [0, 4, 8, 12, 24, 48]

MARKETS = [
    # key,    label,               file stem,      price column,     currency, tz
    ("spain", "Spain",             "prices_spain", "price_eur_mwh",  "EUR", "Europe/Madrid"),
    ("sa",    "South Australia",   "prices_sa",    "price_aud_mwh",  "AUD", "Australia/Adelaide"),
    ("miso",  "MISO (Minn. Hub)",  "prices_miso",  "price_usd_mwh",  "USD", "US/Central"),
]
COLOURS = {"spain": "#2a78d6", "sa": "#eb6834", "miso": "#1baf7a"}

INK, INK2, MUTED, RULE = "#0b0d0f", "#4c5257", "#7d8288", "#dde2e6"
SURFACE = "#fdfdfe"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": RULE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130,
})


def load(stem: str, col: str, tz: str, year: int) -> pd.Series:
    df = pd.read_csv(PROCESSED / f"{stem}_{year}.csv")
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert(tz)
    return df.set_index("ts")[col]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    args = p.parse_args()

    series, rows = {}, []
    for key, label, stem, col, cur, tz in MARKETS:
        s = load(stem, col, tz, args.year)
        series[key] = s
        for h in STORAGE_HOURS:
            r = evaluate(s.to_numpy(), demand=DEMAND, storage_hours=h)
            rows.append({"market": key, "label": label, "currency": cur,
                         "storage_hours": h, "flat": r.flat_cost,
                         "battery": r.battery_cost, "saving_pct": r.saving_pct})

    res = pd.DataFrame(rows)
    out = PROCESSED / f"results_all_{args.year}.csv"
    res.to_csv(out, index=False)

    # ---- how different are these markets, structurally? -------------------
    print(f"The three markets, {args.year}\n")
    print(f"  {'':<18} {'mean':>9} {'median':>9} {'below 0':>9} "
          f"{'cheap hr':>9} {'dear hr':>9}")
    for key, label, _, _, cur, _ in MARKETS:
        s = series[key]
        by_hour = s.groupby(s.index.hour).mean()
        print(f"  {label:<18} {s.mean():>9.2f} {s.median():>9.2f} "
              f"{100 * (s < 0).mean():>8.1f}% "
              f"{by_hour.idxmin():>7d}:00 {by_hour.idxmax():>7d}:00")
    print("\n  (mean and median in each market's own currency per MWh)")

    # ---- the result -------------------------------------------------------
    print(f"\n\nSaving from waiting, by tank size\n")
    header = f"  {'tank':>6}" + "".join(f"{m[1]:>19}" for m in MARKETS)
    print(header)
    for h in STORAGE_HOURS:
        line = f"  {h:>4}h"
        for key, _, _, _, _, _ in MARKETS:
            r = res[(res.market == key) & (res.storage_hours == h)].iloc[0]
            line += f"{r.saving_pct:>18.1f}%"
        print(line)
    print("\n  Above 100% means the battery is paid to take power: its bill for "
          "\n  energy is negative, so it more than saves the whole cost.")

    print(f"\n  In local currency per MWh of heat, with a 12h tank:")
    for key, label, _, _, cur, _ in MARKETS:
        r = res[(res.market == key) & (res.storage_hours == 12)].iloc[0]
        print(f"    {label:<18} factory {cur} {r.flat:>7.2f}   "
              f"battery {cur} {r.battery:>7.2f}")

    # ---- figure -----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    for key, label, _, _, _, _ in MARKETS:
        d = res[res.market == key].sort_values("storage_hours")
        ax.plot(d.storage_hours, d.saving_pct, lw=2, marker="o", ms=5.5,
                color=COLOURS[key], zorder=3, label=label)
        last = d.iloc[-1]
        ax.annotate(f" {label} · {last.saving_pct:.0f}%",
                    (last.storage_hours, last.saving_pct),
                    textcoords="offset points", xytext=(6, 0),
                    va="center", fontsize=9, color=INK, zorder=4)

    # Above this line the battery's energy bill has gone negative: it is being
    # paid to take power, so it saves more than the whole cost.
    ax.axhline(100, color=RULE, lw=1.5, ls=(0, (3, 3)), zorder=1)
    ax.text(52, 101.5, "power becomes free above this line",
            fontsize=8.5, color=MUTED, va="bottom", ha="right")

    ax.set_xticks(STORAGE_HOURS)
    ax.set_xticklabels([f"{h}h" for h in STORAGE_HOURS])
    ax.set_xlim(-1.5, 68)
    ax.set_ylim(0, 138)
    ax.set_xlabel("Tank size (hours of the factory's heat)")
    ax.set_ylabel("Saving on the price of power")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="y", color="#eef1f3", lw=1)
    ax.set_axisbelow(True)
    ax.set_title(f"What waiting is worth, {args.year}",
                 loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=30)
    ax.text(0, 1.035, "Energy price only — before network fees, and assuming "
                      "the battery knows the future.",
            transform=ax.transAxes, fontsize=9.5, color=INK2)

    fig_path = FIGS / f"all_{args.year}_storage_curves.png"
    fig.savefig(fig_path, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)

    print(f"\n  wrote {out.relative_to(ROOT)}")
    print(f"  wrote {fig_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
