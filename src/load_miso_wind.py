"""Extract MISO North-region hourly wind generation from the fuel mix reports.

North covers Minnesota and the Dakotas, where Big Stone sits, so it is the
closest public proxy for the output of a named wind farm in that area.

The report published on date D carries the market data for D-1.

    python src/load_miso_wind.py --year 2025
"""

import argparse
import warnings
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd

MARKET_TZ = timezone(timedelta(hours=-5))   # MISO market clock, fixed, no DST

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "miso_wind"
PROCESSED = ROOT / "data" / "processed"
LOCAL_TZ = "US/Central"


def parse(path: Path) -> pd.DataFrame | None:
    """Return market date and 24 hourly North-region wind values, in MW."""
    raw = pd.read_excel(path, sheet_name="RT Generation Fuel Mix", header=None)

    market_date = None
    for v in raw.iloc[:6, 0].dropna().astype(str):
        if "Market Date" in v:
            market_date = pd.to_datetime(v.split(":", 1)[1].strip()).date()
    if market_date is None:
        return None

    # Region banner row, then the column headers beneath it.
    region_row = next(i for i in range(6)
                      if raw.iloc[i].astype(str).str.strip().eq("North").any())
    north_start = int(raw.iloc[region_row].astype(str).str.strip()
                      .eq("North").idxmax())
    header_row = region_row + 1
    headers = raw.iloc[header_row].astype(str).str.strip()
    wind_col = next(c for c in range(north_start, north_start + 10)
                    if headers.iloc[c] == "Wind")

    body = raw.iloc[header_row + 1:]
    hours = pd.to_numeric(body.iloc[:, 0], errors="coerce")
    wind = pd.to_numeric(body.iloc[:, wind_col], errors="coerce")
    keep = hours.between(1, 24) & wind.notna()
    if not keep.any():
        return None

    return pd.DataFrame({"market_date": market_date,
                         "hour_ending": hours[keep].astype(int),
                         "wind_mw": wind[keep].to_numpy()})


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    args = p.parse_args()

    frames = []
    for f in sorted(RAW.glob("gfm_*.xlsx")):
        try:
            df = parse(f)
        except Exception:                            # noqa: BLE001
            df = None
        if df is not None:
            frames.append(df)

    all_df = pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["market_date", "hour_ending"])

    # Hour ending 1 covers 00:00-01:00, so interval start is hour_ending - 1.
    ts = (pd.to_datetime(all_df["market_date"].astype(str))
          + pd.to_timedelta(all_df["hour_ending"] - 1, unit="h"))
    out = (pd.DataFrame({"ts": ts, "wind_mw": all_df["wind_mw"].to_numpy()})
           .sort_values("ts").drop_duplicates("ts").set_index("ts"))
    # MISO's market clock is a fixed -05:00 with no daylight saving - the same
    # convention as its LMP reports - so localise there first, then convert to
    # Minnesota local time.
    out.index = (out.index.tz_localize(MARKET_TZ).tz_convert(LOCAL_TZ))

    start = pd.Timestamp(f"{args.year}-01-01").tz_localize(LOCAL_TZ)
    end = pd.Timestamp(f"{args.year + 1}-01-01").tz_localize(LOCAL_TZ)
    out = out[(out.index >= start) & (out.index < end)]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED / f"miso_north_wind_{args.year}.csv"
    out.reset_index().to_csv(dest, index=False)

    full = pd.date_range(start, end, freq="h", inclusive="left")
    w = out["wind_mw"]
    print(f"MISO North wind {args.year} -> {dest.relative_to(ROOT)}")
    print(f"  hours:        {len(w)} (expected {len(full)})")
    print(f"  gaps:         {len(full.difference(out.index))}")
    print(f"  mean:         {w.mean():,.0f} MW")
    print(f"  min / max:    {w.min():,.0f} / {w.max():,.0f} MW")
    print(f"  hours at zero: {int((w <= 0).sum())} "
          f"({100 * (w <= 0).mean():.1f}%)")
    by_hour = w.groupby(w.index.hour).mean()
    print(f"  windiest hour of day: {by_hour.idxmax():02d}:00 "
          f"({by_hour.max():,.0f} MW)")
    print(f"  calmest  hour of day: {by_hour.idxmin():02d}:00 "
          f"({by_hour.min():,.0f} MW)")


if __name__ == "__main__":
    main()
