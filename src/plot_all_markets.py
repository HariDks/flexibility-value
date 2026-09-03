"""Step 1, belatedly, for the other two markets.

Spain was inspected visually before modelling; South Australia and MISO were
not. This produces the same year-heatmap for all three so the same class of
data error would be caught in each.

    python src/plot_all_markets.py --year 2025
"""

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
FIGS, PROCESSED = ROOT / "output" / "figures", ROOT / "data" / "processed"

INK, INK2, MUTED, RULE = "#0b0d0f", "#4c5257", "#7d8288", "#dde2e6"
SURFACE = "#fdfdfe"
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("blues", BLUES)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": RULE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130,
})

MARKETS = [
    ("South Australia", "prices_sa", "price_aud_mwh", "Australia/Adelaide", "AUD"),
    ("MISO (Minn. Hub)", "prices_miso", "price_usd_mwh", "US/Central", "USD"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    year = ap.parse_args().year
    FIGS.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(len(MARKETS), 1, figsize=(11, 7.4))
    for ax, (label, stem, col, tz, cur) in zip(axes, MARKETS):
        d = pd.read_csv(PROCESSED / f"{stem}_{year}.csv")
        d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
        s = d.set_index("ts")[col]

        grid = (pd.DataFrame({"p": s.to_numpy(), "date": s.index.date,
                              "hour": s.index.hour})
                .pivot_table(index="hour", columns="date", values="p",
                             aggfunc="mean"))
        lo, hi = np.nanpercentile(grid.to_numpy(), [2, 98])
        im = ax.imshow(grid.to_numpy(), aspect="auto", origin="lower", cmap=CMAP,
                       vmin=lo, vmax=hi, extent=(0, grid.shape[1], 0, 24),
                       interpolation="nearest")

        dates = pd.to_datetime(pd.Series(grid.columns))
        ax.set_xticks([int((dates.dt.month == m).idxmax()) for m in range(1, 13)])
        ax.set_xticklabels(MONTHS)
        ax.set_yticks([0, 6, 12, 18, 24])
        ax.set_yticklabels(["00", "06", "12", "18", "24"])
        ax.set_ylabel("Hour of day (local)")
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)

        cb = fig.colorbar(im, ax=ax, pad=0.012, fraction=0.024)
        cb.set_label(f"{cur} / MWh", color=INK2)
        cb.outline.set_visible(False)
        cb.ax.tick_params(length=0, colors=MUTED)

        by_hour = s.groupby(s.index.hour).mean()
        neg = int((s < 0).sum())
        ax.set_title(f"{label} {year}", loc="left", fontsize=11.5,
                     fontweight="bold", color=INK, pad=26)
        ax.text(0, 1.06, f"mean {s.mean():,.1f} · {neg:,} hours below zero "
                         f"({100 * neg / len(s):.1f}%) · cheapest hour "
                         f"{by_hour.idxmin():02d}:00 · dearest "
                         f"{by_hour.idxmax():02d}:00 · colour clipped to 2–98th pct",
                transform=ax.transAxes, fontsize=8.5, color=INK2)

        # data checks
        print(f"\n{label}")
        print(f"  hours {len(s)}, missing {int(s.isna().sum())}, "
              f"duplicated timestamps {int(s.index.duplicated().sum())}")
        print(f"  range {s.min():,.2f} to {s.max():,.2f}, "
              f"mean {s.mean():,.2f}, median {s.median():,.2f}")
        per_day = s.groupby(s.index.date).size()
        odd = per_day[per_day != 24]
        print(f"  days not 24h: {len(odd)} "
              + ", ".join(f"{k} ({v}h)" for k, v in odd.items()))
        flat = s.groupby(s.index.date).nunique()
        print(f"  days with a single repeated value: {int((flat == 1).sum())}")
        big = s[np.abs(s) > 20 * s.abs().median()]
        print(f"  |price| > 20x median: {len(big)} hours "
              f"(max {s.max():,.0f})")

    fig.suptitle("The two markets that were never eyeballed",
                 x=0.055, y=1.02, ha="left", fontsize=13,
                 fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    out = FIGS / f"sa_miso_{year}_heatmaps.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"\n  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
