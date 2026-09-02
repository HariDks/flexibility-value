"""Step 2: run the battery over a real year of Spanish prices.

Energy price only — network fees come in Step 4, and the battery still knows
the future here, which is Step 5's problem.

    python src/analyse_spain.py --year 2025
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

DEMAND = 10.0                       # MWh of heat per hour
STORAGE_HOURS = [0, 4, 8, 12, 24, 48]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

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


def load(year: int) -> pd.Series:
    df = pd.read_csv(PROCESSED / f"prices_spain_{year}.csv")
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("Europe/Madrid")
    return df.set_index("ts")["price_eur_mwh"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    args = p.parse_args()

    s = load(args.year)
    prices = s.to_numpy()

    rows, charges = [], {}
    for h in STORAGE_HOURS:
        r = evaluate(prices, demand=DEMAND, storage_hours=h)
        rows.append({"storage_hours": h,
                     "flat_eur_mwh": r.flat_cost,
                     "battery_eur_mwh": r.battery_cost,
                     "saving_pct": r.saving_pct})
        charges[h] = r.charge

    res = pd.DataFrame(rows)
    out = PROCESSED / f"results_spain_{args.year}.csv"
    res.to_csv(out, index=False)

    print(f"Spain {args.year} — energy price only, battery knows the future\n")
    print(f"  A normal factory paid EUR {res['flat_eur_mwh'].iat[0]:.2f} / MWh "
          f"(the annual average price).\n")
    print(f"  {'tank':>6}  {'battery':>10}  {'saving':>8}")
    print(f"  {'':>6}  {'EUR/MWh':>10}  {'':>8}")
    for _, r in res.iterrows():
        print(f"  {int(r.storage_hours):>4}h  {r.battery_eur_mwh:>10.2f}  "
              f"{r.saving_pct:>7.1f}%")

    # --- sanity check: is it buying when we think it should be? ----------
    ref = charges[12]
    by_hour = pd.Series(ref, index=s.index).groupby(s.index.hour).sum()
    share = 100 * by_hour / by_hour.sum()
    top = share.nlargest(6).sort_index()
    print("\n  With a 12h tank, the hours it buys most in:")
    print("   ", ", ".join(f"{h:02d}:00 ({v:.0f}%)" for h, v in top.items()))
    print(f"    share of all buying between 10:00 and 17:00: "
          f"{share.loc[10:17].sum():.0f}%")

    # --- seasonal split ---------------------------------------------------
    print("\n  By month, with a 12h tank (EUR/MWh):")
    ch = pd.Series(ref, index=s.index)
    print(f"    {'':>5} {'factory':>9} {'battery':>9} {'saving':>8}")
    for m in range(1, 13):
        mask = s.index.month == m
        flat_m = s[mask].mean()
        bought = ch[mask].sum()
        batt_m = (ch[mask] * s[mask]).sum() / bought if bought else float("nan")
        save_m = 100 * (flat_m - batt_m) / abs(flat_m)
        print(f"    {MONTHS[m - 1]:>5} {flat_m:>9.2f} {batt_m:>9.2f} "
              f"{save_m:>7.1f}%")

    # --- figure -----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.plot(res.storage_hours, res.battery_eur_mwh, lw=2, color=BATTERY,
            marker="o", ms=6, zorder=3, label="Thermal battery")
    ax.axhline(res.flat_eur_mwh.iat[0], lw=2, color=FACTORY, ls=(0, (4, 3)),
               zorder=2, label="Normal factory")

    for _, r in res.iterrows():
        if r.storage_hours in (0, 8, 48):
            ax.annotate(f"EUR {r.battery_eur_mwh:.0f}",
                        (r.storage_hours, r.battery_eur_mwh),
                        textcoords="offset points", xytext=(0, -17),
                        ha="center", fontsize=9, color=INK)
    ax.annotate(f"EUR {res.flat_eur_mwh.iat[0]:.0f}",
                (48, res.flat_eur_mwh.iat[0]), textcoords="offset points",
                xytext=(0, 8), ha="right", fontsize=9, color=FACTORY)

    ax.set_xticks(STORAGE_HOURS)
    ax.set_xticklabels([f"{h}h" for h in STORAGE_HOURS])
    ax.set_xlabel("Tank size (hours of the factory's heat)")
    ax.set_ylabel("EUR / MWh of heat")
    ax.set_ylim(0, res.flat_eur_mwh.iat[0] * 1.22)
    ax.grid(axis="y", color="#eef1f3", lw=1)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower left", fontsize=9.5)
    ax.set_title(f"Spain {args.year}: what waiting is worth",
                 loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=30)
    ax.text(0, 1.035, "Energy price only — before network fees, and assuming "
                      "perfect foresight.",
            transform=ax.transAxes, fontsize=9.5, color=INK2)

    fig_path = FIGS / f"spain_{args.year}_storage_curve.png"
    fig.savefig(fig_path, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)

    print(f"\n  wrote {out.relative_to(ROOT)}")
    print(f"  wrote {fig_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
