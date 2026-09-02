"""Turn the raw AEMO files into one tidy hourly price series.

Three corrections happen here, and getting any of them wrong shifts the whole
day-shape by an hour or more:

1. **Interval-ending to interval-beginning.** AEMO stamps a five-minute row with
   the time it *ends*. A row at 00:05 covers 00:00-00:05, so we shift back five
   minutes before doing anything else.

2. **Market time to local time.** SETTLEMENTDATE is Australian Eastern Standard
   Time all year round, and never shifts for daylight saving. South Australia is
   30 minutes behind that in winter and 30 minutes ahead in summer. Reading the
   raw stamps as local time would put the solar trough in the wrong place.

3. **Five-minute to hourly**, so all three markets share one time step.

    python src/load_aemo.py --year 2025 --region SA1
"""

import argparse
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "aemo"
PROCESSED = ROOT / "data" / "processed"

MARKET_TZ = timezone(timedelta(hours=10))   # AEST, fixed, no daylight saving
LOCAL_TZ = "Australia/Adelaide"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--region", default="SA1")
    args = p.parse_args()

    # Read every month available, including the bracketing ones, and trim to the
    # local year later. Globbing only the target year would leave the first and
    # last local hours built from half their intervals.
    files = sorted(RAW.glob(f"PRICE_AND_DEMAND_*_{args.region}.csv"))
    if not files:
        raise SystemExit(f"No raw AEMO files for {args.region}")

    raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    ts = pd.to_datetime(raw["SETTLEMENTDATE"], format="%Y/%m/%d %H:%M:%S")

    # (1) interval-ending -> interval-beginning, (2) market time -> local time
    ts = ts.dt.tz_localize(MARKET_TZ) - pd.Timedelta(5, unit="m")
    native = (pd.DataFrame({"ts": ts.dt.tz_convert(LOCAL_TZ),
                            "price_aud_mwh": raw["RRP"].to_numpy()})
              .sort_values("ts").set_index("ts"))
    native = native[~native.index.duplicated(keep="first")]

    # Trim to the local calendar year before aggregating, so no hour is built
    # from a partial set of intervals. The bracketing months make this possible.
    start = pd.Timestamp(f"{args.year}-01-01").tz_localize(LOCAL_TZ)
    end = pd.Timestamp(f"{args.year + 1}-01-01").tz_localize(LOCAL_TZ)
    native = native[(native.index >= start) & (native.index < end)]

    # (3) five-minute -> hourly
    per_hour = native["price_aud_mwh"].resample("h").count()
    short = per_hour[per_hour != 12]
    if len(short):
        raise SystemExit(
            f"{len(short)} hour(s) are not built from 12 five-minute intervals, "
            f"first: {short.index[0]} has {short.iat[0]}")

    hourly = native["price_aud_mwh"].resample("h").mean().to_frame()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / f"prices_sa_{args.year}.csv"
    hourly.reset_index().to_csv(out, index=False)

    s = hourly["price_aud_mwh"]
    expected = len(pd.date_range(
        pd.Timestamp(f"{args.year}-01-01").tz_localize(LOCAL_TZ),
        pd.Timestamp(f"{args.year + 1}-01-01").tz_localize(LOCAL_TZ),
        freq="h", inclusive="left"))

    print(f"South Australia {args.year} -> {out.relative_to(ROOT)}")
    print(f"  five-minute intervals in: {len(native):,}")
    print(f"  hours out:        {len(s)} (expected {expected})")
    print(f"  missing values:   {int(s.isna().sum())}")
    print(f"  range:            {s.min():.2f} to {s.max():.2f} AUD/MWh")
    print(f"  mean:             {s.mean():.2f} AUD/MWh")
    print(f"  median:           {s.median():.2f} AUD/MWh")
    print(f"  hours below zero: {int((s < 0).sum())} "
          f"({100 * (s < 0).mean():.1f}%)")

    by_hour = s.groupby(s.index.hour).mean()
    print(f"  cheapest hour of day (annual mean): "
          f"{by_hour.idxmin():02d}:00 at {by_hour.min():.2f}")
    print(f"  dearest  hour of day (annual mean): "
          f"{by_hour.idxmax():02d}:00 at {by_hour.max():.2f}")


if __name__ == "__main__":
    main()
