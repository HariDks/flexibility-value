"""Download a year of Spanish hourly day-ahead prices from OMIE.

OMIE publishes one small file per day. Each row is:

    year;month;day;hour;price_Portugal;price_Spain;

Hour is 1-based and counts *local* hours, so a normal day has 24 rows, the
spring clock-change day has 23, and the autumn one has 25. We keep that as-is
here and let the loader turn it into real timestamps.

Files are cached in data/raw/omie/ — rerunning only fetches what is missing.

    python src/fetch_omie.py --year 2025
"""

import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "omie"
URL = ("https://www.omie.es/es/file-download?parents=marginalpdbc"
       "&filename=marginalpdbc_{ymd}.{suffix}")


def days_in_year(year: int):
    d, end = date(year, 1, 1), date(year + 1, 1, 1)
    while d < end:
        yield d
        d += timedelta(days=1)


# OMIE republishes corrected files under an incrementing suffix, so
# marginalpdbc_20251030.3 supersedes .2 and .1. Probe downwards and keep the
# highest one that exists. Two days in 2025 are only available as revisions.
SUFFIXES = (3, 2, 1)


def fetch_day(d: date, session: requests.Session, retries: int = 2) -> tuple[date, str]:
    ymd = f"{d:%Y%m%d}"
    if any((RAW / f"marginalpdbc_{ymd}.{s}.txt").exists() for s in SUFFIXES):
        return d, "cached"

    for suffix in SUFFIXES:
        for attempt in range(retries):
            try:
                r = session.get(URL.format(ymd=ymd, suffix=suffix), timeout=30)
                if r.status_code == 200 and r.text.startswith("MARGINALPDBC"):
                    (RAW / f"marginalpdbc_{ymd}.{suffix}.txt").write_text(
                        r.text, encoding="utf-8")
                    return d, "downloaded" if suffix == 1 else f"downloaded rev.{suffix}"
                if r.status_code == 404:
                    break  # try the next suffix down
            except requests.RequestException:
                if attempt == retries - 1:
                    break
                time.sleep(1.5 * (attempt + 1))
    return d, "missing"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    days = list(days_in_year(args.year))
    print(f"{len(days)} days requested for {args.year} -> {RAW}")

    with requests.Session() as s:
        s.headers["User-Agent"] = "flexibility-value/0.1 (research)"
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda d: fetch_day(d, s), days))

    counts: dict[str, int] = {}
    for _, status in results:
        key = status.split(":")[0]
        counts[key] = counts.get(key, 0) + 1
    for k, v in sorted(counts.items()):
        print(f"  {k:>16}: {v}")

    bad = [d for d, st in results
           if not (st == "cached" or st.startswith("downloaded"))]
    if bad:
        print(f"\n{len(bad)} day(s) not retrieved, first few: "
              f"{', '.join(str(d) for d in bad[:5])}")
    else:
        print("\nAll days present.")


if __name__ == "__main__":
    main()
