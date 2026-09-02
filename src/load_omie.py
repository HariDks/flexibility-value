"""Turn the raw OMIE day files into one tidy hourly price series for Spain.

Two wrinkles this handles, both real and both easy to get silently wrong:

1. **Resolution changes mid-year.** Spain priced in hourly blocks until
   2025-09-30 and in 15-minute blocks from 2025-10-01 (the EU market-time-unit
   change). We average the quarter-hours up to hourly so the whole year — and
   later, all three markets — share one time step.

2. **Clock changes.** OMIE numbers periods 1..N in *local* time, so the spring
   day has 23 hours and the autumn day 25. Rather than assuming 24, we generate
   the true local timestamps for each day and check the count matches the file.

    python src/load_omie.py --year 2025
"""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "omie"
PROCESSED = ROOT / "data" / "processed"
TZ = "Europe/Madrid"

# marginalpdbc columns: year;month;day;period;price_PT;price_ES;
COLS = ["year", "month", "day", "period", "price_pt", "price_es"]


def load_day(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", skiprows=1, header=None,
                     usecols=range(6), names=COLS)
    df = df[pd.to_numeric(df["year"], errors="coerce").notna()]
    df = df.astype({"year": int, "month": int, "day": int, "period": int})

    day = pd.Timestamp(year=df["year"].iat[0], month=df["month"].iat[0],
                       day=df["day"].iat[0])
    n = len(df)

    # 24/23/25 periods means hourly; 96/92/100 means quarter-hourly.
    freq = "h" if n <= 25 else "15min"
    start = day.tz_localize(TZ)
    end = (day + pd.Timedelta(1, unit="D")).tz_localize(TZ)
    idx = pd.date_range(start, end, freq=freq, inclusive="left")

    if len(idx) != n:
        raise ValueError(
            f"{path.name}: file has {n} rows but {day.date()} has {len(idx)} "
            f"{freq} periods in {TZ}")

    return pd.DataFrame({"ts": idx, "price_eur_mwh": df["price_es"].to_numpy()})


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    args = p.parse_args()

    files = sorted(RAW.glob(f"marginalpdbc_{args.year}*.txt"))
    if not files:
        raise SystemExit(f"No raw files for {args.year} in {RAW}")

    native = pd.concat([load_day(f) for f in files], ignore_index=True)
    native = native.sort_values("ts").set_index("ts")

    # Average quarter-hours up to hourly. A no-op for the hourly part of the year.
    hourly = native["price_eur_mwh"].resample("h").mean().to_frame()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / f"prices_spain_{args.year}.csv"
    hourly.reset_index().to_csv(out, index=False)

    # ---- quality report -------------------------------------------------
    s = hourly["price_eur_mwh"]
    expected = len(pd.date_range(
        pd.Timestamp(f"{args.year}-01-01").tz_localize(TZ),
        pd.Timestamp(f"{args.year + 1}-01-01").tz_localize(TZ),
        freq="h", inclusive="left"))

    print(f"Spain {args.year} -> {out.relative_to(ROOT)}")
    print(f"  hours:            {len(s)} (expected {expected})")
    print(f"  missing values:   {int(s.isna().sum())}")
    gaps = native.index.to_series().diff()
    quarter_hourly = native.index[gaps == pd.Timedelta(15, unit="m")]
    print(f"  native 15-min from: {quarter_hourly.min()}")
    print(f"  range:            {s.min():.2f} to {s.max():.2f} EUR/MWh")
    print(f"  mean:             {s.mean():.2f} EUR/MWh")
    print(f"  hours at or below zero: {int((s <= 0).sum())} "
          f"({100 * (s <= 0).mean():.1f}%)")
    print(f"  hours below zero:       {int((s < 0).sum())} "
          f"({100 * (s < 0).mean():.1f}%)")

    # The cheapest and dearest hours should sit where intuition says they do.
    by_hour = s.groupby(s.index.hour).mean()
    print(f"  cheapest hour of day (annual mean): "
          f"{by_hour.idxmin():02d}:00 at {by_hour.min():.2f}")
    print(f"  dearest  hour of day (annual mean): "
          f"{by_hour.idxmax():02d}:00 at {by_hour.max():.2f}")


if __name__ == "__main__":
    main()
