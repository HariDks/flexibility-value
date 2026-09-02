"""Step 1: look at the Spanish year before modelling anything.

Produces three figures in output/figures/:

  1. spain_YYYY_heatmap.png       the whole year, hour-of-day x day-of-year
  2. spain_YYYY_monthly_shape.png average day per month, twelve lines
  3. spain_YYYY_weeks.png         one week from the best and worst months

The extreme months are chosen from the data, not assumed. The measure is the
"flexibility spread": for each day, the mean price minus the mean of that day's
eight cheapest hours — i.e. how much a buyer who could wait would have saved.
Averaged per month, the highest and lowest months are the extremes.

    python src/plot_step1.py --year 2025
"""

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "output" / "figures"

INK, INK2, MUTED, RULE = "#0b0d0f", "#4c5257", "#7d8288", "#dde2e6"
SURFACE = "#fdfdfe"
# Sequential blue ramp (steps 100..700), light = cheap, dark = dear.
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
PRICE_CMAP = LinearSegmentedColormap.from_list("blues", BLUES)
# Ordinal steps for the twelve months: never paler than step 250.
MONTH_RAMP = LinearSegmentedColormap.from_list("months", BLUES[1:])

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": RULE,
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 130,
})

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load(year: int) -> pd.Series:
    path = ROOT / "data" / "processed" / f"prices_spain_{year}.csv"
    df = pd.read_csv(path)
    # The year spans a clock change, so the saved offsets are mixed (+01:00 and
    # +02:00). Parse as UTC first, then put it back into local time.
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("Europe/Madrid")
    return df.set_index("ts")["price_eur_mwh"]


def flexibility_spread(s: pd.Series, cheapest_n: int = 8) -> pd.Series:
    """Per-day: mean price minus the mean of that day's N cheapest hours."""
    by_day = s.groupby(s.index.date)
    return by_day.mean() - by_day.apply(lambda d: d.nsmallest(cheapest_n).mean())


def fig_heatmap(s: pd.Series, year: int) -> Path:
    df = pd.DataFrame({
        "price": s.to_numpy(),
        "date": s.index.date,
        "hour": s.index.hour,
    })
    # One NaN cell where the spring clock change removes an hour; the autumn
    # change repeats an hour, so it is averaged.
    grid = df.pivot_table(index="hour", columns="date",
                          values="price", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(11, 3.9))
    lo, hi = np.nanpercentile(grid.to_numpy(), [1, 99])
    im = ax.imshow(grid.to_numpy(), aspect="auto", origin="lower",
                   cmap=PRICE_CMAP, vmin=lo, vmax=hi,
                   extent=(0, grid.shape[1], 0, 24), interpolation="nearest")

    dates = pd.to_datetime(pd.Series(grid.columns))
    starts = [int((dates.dt.month == m).idxmax()) for m in range(1, 13)]
    ax.set_xticks(starts)
    ax.set_xticklabels(MONTHS)
    ax.set_yticks([0, 6, 12, 18, 24])
    ax.set_yticklabels(["00:00", "06:00", "12:00", "18:00", "24:00"])
    ax.set_ylabel("Hour of day (local)")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)

    cb = fig.colorbar(im, ax=ax, pad=0.012, fraction=0.024)
    cb.set_label("EUR / MWh", color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, colors=MUTED)

    neg = int((s < 0).sum())
    ax.set_title(f"Spain {year}: every hour of the year",
                 loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=30)
    ax.text(0, 1.055, f"Pale = cheap. {neg:,} hours priced below zero "
                      f"({100 * neg / len(s):.1f}% of the year).",
            transform=ax.transAxes, fontsize=9.5, color=INK2)

    out = FIGS / f"spain_{year}_heatmap.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return out


def fig_monthly_shape(s: pd.Series, year: int) -> Path:
    shape = s.groupby([s.index.month, s.index.hour]).mean().unstack(level=0)

    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    for i, m in enumerate(range(1, 13)):
        ax.plot(shape.index, shape[m], lw=2,
                color=MONTH_RAMP(i / 11), label=MONTHS[i], zorder=2)
    ax.axhline(0, color=RULE, lw=1.5, ls=(0, (3, 3)), zorder=1)

    ax.set_xticks([0, 6, 12, 18, 23])
    ax.set_xticklabels(["00:00", "06:00", "12:00", "18:00", "23:00"])
    ax.set_ylabel("EUR / MWh")
    ax.grid(axis="y", color="#e8ecef", lw=1)
    ax.set_axisbelow(True)
    ax.legend(ncol=6, frameon=False, fontsize=8.5, loc="upper center",
              bbox_to_anchor=(0.5, -0.11), handlelength=1.4, columnspacing=1.4)

    ax.set_title(f"Spain {year}: the average day, month by month",
                 loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=30)
    ax.text(0, 1.035, "The midday trough is deepest in summer and all but gone in winter.",
            transform=ax.transAxes, fontsize=9.5, color=INK2)

    out = FIGS / f"spain_{year}_monthly_shape.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return out


def fig_weeks(s: pd.Series, year: int, best: int, worst: int) -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 6.2), sharey=True)

    for ax, month, tag, colour in [
        (axes[0], best, "widest spread", "#2a78d6"),
        (axes[1], worst, "narrowest spread", "#eb6834"),
    ]:
        month_data = s[s.index.month == month]
        # First Monday in the month, then seven days.
        mondays = month_data.index[month_data.index.dayofweek == 0]
        start = mondays[0].normalize()
        week = s[(s.index >= start) & (s.index < start + pd.Timedelta(7, unit="D"))]

        ax.plot(week.index, week.to_numpy(), lw=1.8, color=colour, zorder=3)
        ax.axhline(0, color=RULE, lw=1.5, ls=(0, (3, 3)), zorder=1)
        ax.fill_between(week.index, week.to_numpy(), 0,
                        where=week.to_numpy() <= 0, color=colour, alpha=0.22, zorder=2)

        for d in pd.date_range(start, periods=8, freq="D", tz=week.index.tz):
            ax.axvline(d, color="#e8ecef", lw=1, zorder=0)
        ax.set_xticks(pd.date_range(start, periods=7, freq="D", tz=week.index.tz))
        ax.set_xticklabels([d.strftime("%a %-d") for d in
                            pd.date_range(start, periods=7, freq="D")])
        ax.set_ylabel("EUR / MWh")
        ax.grid(axis="y", color="#f0f2f4", lw=1)
        ax.set_axisbelow(True)
        ax.set_title(f"{MONTHS[month - 1]} — {tag}", loc="left",
                     fontsize=10.5, fontweight="bold", color=INK, pad=6)

    fig.suptitle(f"Spain {year}: one week from each extreme",
                 x=0.075, ha="left", fontsize=12.5, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    out = FIGS / f"spain_{year}_weeks.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    args = p.parse_args()

    FIGS.mkdir(parents=True, exist_ok=True)
    s = load(args.year)

    spread = flexibility_spread(s)
    spread.index = pd.to_datetime(pd.Series(spread.index))
    by_month = spread.groupby(spread.index.month).mean()

    print(f"Flexibility spread by month, Spain {args.year}")
    print("(mean price minus mean of the day's 8 cheapest hours, EUR/MWh)\n")
    for m in range(1, 13):
        bar = "#" * int(round(by_month[m] / 1.5))
        print(f"  {MONTHS[m - 1]}  {by_month[m]:6.1f}  {bar}")

    best, worst = int(by_month.idxmax()), int(by_month.idxmin())
    print(f"\n  widest:    {MONTHS[best - 1]} ({by_month[best]:.1f})")
    print(f"  narrowest: {MONTHS[worst - 1]} ({by_month[worst]:.1f})\n")

    for path in (fig_heatmap(s, args.year),
                 fig_monthly_shape(s, args.year),
                 fig_weeks(s, args.year, best, worst)):
        print(f"  wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
