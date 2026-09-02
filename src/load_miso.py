"""Turn the raw MISO day files into one tidy hourly price series.

MISO's day-ahead market is already hourly, so there is no aggregation to do.
The work here is joining 365 daily files, checking the clock changes land where
they should, and confirming nothing is missing.

    python src/load_miso.py --year 2025
"""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "miso"
PROCESSED = ROOT / "data" / "processed"
LOCAL_TZ = "US/Central"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    args = p.parse_args()

    # Read every day available, including the bracketing ones, then trim to the
    # local year. MISO's market clock is a fixed -05:00 with no daylight saving,
    # so the market year and the Minnesota year do not share their edges.
    files = sorted(RAW.glob("miso_da_*.csv"))
    if not files:
        raise SystemExit(f"No raw MISO files in {RAW}")

    raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    ts = pd.to_datetime(raw["Interval Start"], utc=True).dt.tz_convert(LOCAL_TZ)

    hourly = (pd.DataFrame({"ts": ts, "price_usd_mwh": raw["LMP"].to_numpy()})
              .sort_values("ts")
              .drop_duplicates(subset="ts", keep="first")
              .set_index("ts"))

    start = pd.Timestamp(f"{args.year}-01-01").tz_localize(LOCAL_TZ)
    end = pd.Timestamp(f"{args.year + 1}-01-01").tz_localize(LOCAL_TZ)
    hourly = hourly[(hourly.index >= start) & (hourly.index < end)]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / f"prices_miso_{args.year}.csv"
    hourly.reset_index().to_csv(out, index=False)

    s = hourly["price_usd_mwh"]
    full = pd.date_range(
        pd.Timestamp(f"{args.year}-01-01").tz_localize(LOCAL_TZ),
        pd.Timestamp(f"{args.year + 1}-01-01").tz_localize(LOCAL_TZ),
        freq="h", inclusive="left")
    gaps = full.difference(s.index)

    print(f"MISO MINN.HUB {args.year} -> {out.relative_to(ROOT)}")
    print(f"  hours:            {len(s)} (expected {len(full)})")
    print(f"  gaps:             {len(gaps)}"
          + (f"  first: {gaps[0]}" if len(gaps) else ""))
    print(f"  missing values:   {int(s.isna().sum())}")
    print(f"  range:            {s.min():.2f} to {s.max():.2f} USD/MWh")
    print(f"  mean:             {s.mean():.2f} USD/MWh")
    print(f"  median:           {s.median():.2f} USD/MWh")
    print(f"  hours below zero: {int((s < 0).sum())} "
          f"({100 * (s < 0).mean():.1f}%)")

    # Clock changes: one short day in spring, one long day in autumn.
    per_day = s.groupby(s.index.date).size()
    odd = per_day[per_day != 24]
    print(f"  days not 24h:     {len(odd)}"
          + ("  " + ", ".join(f"{d} ({n}h)" for d, n in odd.items())
             if len(odd) else ""))

    by_hour = s.groupby(s.index.hour).mean()
    print(f"  cheapest hour of day (annual mean): "
          f"{by_hour.idxmin():02d}:00 at {by_hour.min():.2f}")
    print(f"  dearest  hour of day (annual mean): "
          f"{by_hour.idxmax():02d}:00 at {by_hour.max():.2f}")


if __name__ == "__main__":
    main()
