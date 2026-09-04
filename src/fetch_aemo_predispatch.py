"""Measure how far ahead the NEM can actually be seen.

South Australia's forecast horizon is the largest judgment in this study. AEMO
publishes no day-ahead price, but it does publish **pre-dispatch forecasts** —
half-hourly projections out to roughly 28 hours, refreshed every 30 minutes.

This downloads those forecasts and pairs each one with the price that actually
occurred, so forecast error can be measured against horizon rather than assumed.

The weekly archives are ~280 MB with 337 nested run-zips inside, so they are
streamed in memory and only the SA1 price rows are kept.

    python src/fetch_aemo_predispatch.py --weeks 20250831 20251005 20251109 20251214
"""

import argparse
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

OUT = Path(__file__).resolve().parents[1] / "data" / "processed"
BASE = ("http://nemweb.com.au/Reports/ARCHIVE/PredispatchIS_Reports/"
        "PUBLIC_PREDISPATCHIS_{start}_{end}.zip")
REGION = "SA1"


def week_url(start: str) -> str:
    s = pd.Timestamp(start)
    return BASE.format(start=s.strftime("%Y%m%d"),
                       end=(s + pd.Timedelta(6, unit="D")).strftime("%Y%m%d"))


def rows_from_run(text: str) -> list[tuple]:
    """Pull SA1 forecast rows: (run time, target interval, forecast price)."""
    out = []
    for line in text.splitlines():
        if not line.startswith("D,PREDISPATCH,REGION_PRICES"):
            continue
        f = line.split(",")
        if len(f) < 29 or f[6] != REGION:
            continue
        try:
            rrp = float(f[9])
            run = f[27].strip('"')
            target = f[28].strip('"')
        except (ValueError, IndexError):
            continue
        out.append((run, target, rrp))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--weeks", nargs="+", required=True,
                   help="Monday dates, e.g. 20250831")
    args = p.parse_args()

    frames = []
    with requests.Session() as s:
        s.headers["User-Agent"] = "flexibility-value/0.1 (research)"
        for wk in args.weeks:
            url = week_url(wk)
            r = s.get(url, timeout=600)
            if r.status_code != 200:
                print(f"  {wk}: HTTP {r.status_code}")
                continue
            rows = []
            with zipfile.ZipFile(io.BytesIO(r.content)) as outer:
                inner_names = [n for n in outer.namelist()
                               if n.lower().endswith(".zip")]
                for n in inner_names:
                    with zipfile.ZipFile(io.BytesIO(outer.read(n))) as inner:
                        for c in inner.namelist():
                            if c.lower().endswith(".csv"):
                                rows += rows_from_run(
                                    inner.read(c).decode("utf-8", "ignore"))
            df = pd.DataFrame(rows, columns=["run", "target", "forecast"])
            frames.append(df)
            print(f"  {wk}: {len(inner_names)} runs, {len(df):,} forecast rows")

    all_df = pd.concat(frames, ignore_index=True)
    all_df["run"] = pd.to_datetime(all_df["run"], format="%Y/%m/%d %H:%M:%S")
    all_df["target"] = pd.to_datetime(all_df["target"], format="%Y/%m/%d %H:%M:%S")
    all_df["horizon_h"] = ((all_df["target"] - all_df["run"])
                           .dt.total_seconds() / 3600)

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "sa_predispatch_forecasts.csv"
    all_df.to_csv(dest, index=False)
    print(f"\n{len(all_df):,} forecasts -> {dest.name}")
    print(f"  horizons {all_df.horizon_h.min():.1f} to "
          f"{all_df.horizon_h.max():.1f} hours")
    print(f"  run times {all_df.run.min()} to {all_df.run.max()}")


if __name__ == "__main__":
    main()
