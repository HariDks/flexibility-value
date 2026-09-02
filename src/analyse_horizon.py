"""Step 5: what is it worth to see ahead?

Every earlier result let the battery look ahead as far as its tank could carry
heat. That is not automatically unrealistic — Spain and MISO both publish
tomorrow's prices today, so an operator there genuinely does know what is
coming. South Australia has no day-ahead market at all, so an operator there
knows much less.

This step dials the battery's visibility from "only this hour" up to
"tank-limited" and measures what each extra hour of warning is worth.

    python src/analyse_horizon.py --year 2025
"""

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

from battery import evaluate

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "output" / "figures"
PROCESSED = ROOT / "data" / "processed"

DEMAND = 10.0
HORIZONS = [1, 2, 3, 4, 6, 8, 12, 18, 24, 36]
TANKS = [12, 24]

MARKETS = [
    ("spain", "Spain",            "prices_spain", "price_eur_mwh", "Europe/Madrid",
     24, "day-ahead market: tomorrow's prices published each midday"),
    ("sa",    "South Australia",  "prices_sa",    "price_aud_mwh", "Australia/Adelaide",
     3,  "no day-ahead market: price is set in real time"),
    ("miso",  "MISO (Minn. Hub)", "prices_miso",  "price_usd_mwh", "US/Central",
     24, "day-ahead market: tomorrow's prices published each afternoon"),
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


def load(stem, col, tz, year):
    df = pd.read_csv(PROCESSED / f"{stem}_{year}.csv")
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert(tz)
    return df.set_index("ts")[col]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    args = p.parse_args()

    rows = []
    for key, label, stem, col, tz, real_h, _ in MARKETS:
        prices = load(stem, col, tz, args.year).to_numpy()
        for tank in TANKS:
            best = evaluate(prices, DEMAND, tank).saving_pct   # tank-limited
            for h in HORIZONS + [None]:
                r = evaluate(prices, DEMAND, tank, horizon=h)
                rows.append({"market": key, "label": label, "tank": tank,
                             "horizon": h if h is not None else 999,
                             "saving_pct": r.saving_pct,
                             "share_of_best": 100 * r.saving_pct / best
                                              if best else 0.0})
    res = pd.DataFrame(rows)
    res.to_csv(PROCESSED / f"results_horizon_{args.year}.csv", index=False)

    for tank in TANKS:
        print(f"\nSaving with a {tank}h tank, by hours of visibility\n")
        print("  " + "hours ahead".ljust(14)
              + "".join(f"{m[1]:>19}" for m in MARKETS))
        for h in HORIZONS:
            line = f"  {h:>3}h".ljust(16)
            for key, *_ in MARKETS:
                v = res[(res.market == key) & (res.tank == tank)
                        & (res.horizon == h)].saving_pct.iat[0]
                line += f"{v:>18.1f}%"
            print(line)
        line = "  tank-limited".ljust(16)
        for key, *_ in MARKETS:
            v = res[(res.market == key) & (res.tank == tank)
                    & (res.horizon == 999)].saving_pct.iat[0]
            line += f"{v:>18.1f}%"
        print(line)

    print("\n\nWhat each market's operator can realistically see:\n")
    for key, label, _, _, _, real_h, why in MARKETS:
        d = res[(res.market == key) & (res.tank == 12)]
        realistic = d[d.horizon == real_h].saving_pct.iat[0]
        best = d[d.horizon == 999].saving_pct.iat[0]
        print(f"  {label}")
        print(f"    {why}")
        print(f"    at {real_h}h visibility: {realistic:.1f}%   "
              f"tank-limited best: {best:.1f}%   "
              f"cost of not seeing further: {best - realistic:.1f} points")

    # ---- figure ----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.2, 4.9))
    for key, label, _, _, _, real_h, _ in MARKETS:
        d = res[(res.market == key) & (res.tank == 12)
                & (res.horizon != 999)].sort_values("horizon")
        ax.plot(d.horizon, d.saving_pct, lw=2, color=COLOURS[key],
                marker="o", ms=4.5, zorder=3)
        last = d.iloc[-1]
        ax.annotate(f" {label}", (last.horizon, last.saving_pct),
                    textcoords="offset points", xytext=(6, 0), va="center",
                    fontsize=9, color=INK, zorder=4)
        # mark what this market's operator actually gets to see
        pt = d[d.horizon == real_h]
        ax.plot(pt.horizon, pt.saving_pct, marker="o", ms=11, mfc="none",
                mec=COLOURS[key], mew=2, zorder=5)

    ax.set_xticks(HORIZONS)
    ax.set_xticklabels([f"{h}" for h in HORIZONS])
    ax.set_xlim(0, 47)
    ax.set_ylim(0, 115)
    ax.set_xlabel("Hours of price visibility")
    ax.set_ylabel("Saving on the price of power")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="y", color="#eef1f3", lw=1)
    ax.set_axisbelow(True)
    ax.set_title(f"What seeing ahead is worth, {args.year}",
                 loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=30)
    ax.text(0, 1.035, "12-hour tank. Ringed points mark what each market's "
                      "operator can actually see.",
            transform=ax.transAxes, fontsize=9.5, color=INK2)

    out = FIGS / f"all_{args.year}_horizon.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"\n  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
