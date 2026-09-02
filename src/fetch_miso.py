"""Download a year of MISO day-ahead hourly prices for one hub.

Uses the gridstatus library, which pulls MISO's published day-ahead ex-post LMP
market reports. One file per day, so we cache each day's hub rows locally and
only fetch what is missing.

MINN.HUB is the default: it is the closest published hub to Big Stone City,
South Dakota, where Antora's thermal battery sits alongside POET's ethanol
plant.

    python src/fetch_miso.py --year 2025 --hub MINN.HUB
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import gridstatus
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "miso"
KEEP = ["Interval Start", "Interval End", "Location", "LMP",
        "Energy", "Congestion", "Loss"]


def days_in_year(year: int):
    """The year, plus a day either side.

    MISO stamps its market reports in a fixed -05:00 clock that never shifts for
    daylight saving, but Minnesota's local day does. So the market year and the
    local year do not line up at the edges, and the bracketing days are needed
    to fill the local calendar year completely.
    """
    d, end = date(year - 1, 12, 31), date(year + 1, 1, 2)
    while d < end:
        yield d
        d += timedelta(days=1)


def fetch_day(d: date, hub: str) -> tuple[date, str]:
    out = RAW / f"miso_da_{d:%Y%m%d}.csv"
    if out.exists() and out.stat().st_size > 200:
        return d, "cached"
    try:
        iso = gridstatus.MISO()
        df = iso.get_lmp(date=str(d), market="DAY_AHEAD_HOURLY", locations=[hub])
        if df.empty:
            return d, "empty"
        df[KEEP].to_csv(out, index=False)
        return d, "downloaded"
    except Exception as exc:                      # noqa: BLE001 - report and move on
        return d, f"error: {exc.__class__.__name__}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--hub", default="MINN.HUB")
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    days = list(days_in_year(args.year))
    print(f"{len(days)} days requested for {args.hub} {args.year} -> {RAW}")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda d: fetch_day(d, args.hub), days))

    counts: dict[str, int] = {}
    for _, status in results:
        key = status.split(":")[0]
        counts[key] = counts.get(key, 0) + 1
    for k, v in sorted(counts.items()):
        print(f"  {k:>12}: {v}")

    bad = [d for d, st in results if st not in ("cached", "downloaded")]
    if bad:
        print(f"\n{len(bad)} day(s) missing, first few: "
              f"{', '.join(str(d) for d in bad[:8])}")
    else:
        rows = sum(len(pd.read_csv(f)) for f in sorted(RAW.glob("miso_da_*.csv")))
        print(f"\nAll days present. {rows:,} hourly rows "
              f"(expect ~{365 * 24:,}).")


if __name__ == "__main__":
    main()
