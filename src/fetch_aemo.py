"""Download a year of South Australian spot prices from AEMO.

AEMO publishes one file per region per month. Each row is a five-minute
interval:

    REGION, SETTLEMENTDATE, TOTALDEMAND, RRP, PERIODTYPE

Two things to know, both easy to get wrong:

* **SETTLEMENTDATE is interval-ENDING.** A row stamped 00:05 covers 00:00-00:05.
* **The timestamp is market time, not local time.** The NEM runs on Australian
  Eastern Standard Time all year and never shifts for daylight saving. South
  Australia is half an hour behind that, and shifts in summer. The loader
  converts; the raw files are left exactly as published.

    python src/fetch_aemo.py --year 2025 --region SA1
"""

import argparse
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "aemo"
URL = ("https://aemo.com.au/aemo/data/nem/priceanddemand/"
       "PRICE_AND_DEMAND_{ym}_{region}.csv")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--region", default="SA1")
    args = p.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    total_rows = 0

    # The bracketing months are fetched too. AEMO stamps everything in Eastern
    # Standard Time, which never shifts, but South Australia does - so the local
    # calendar year starts and ends part-way through a market-time hour. Without
    # the neighbouring months the first and last local hours are incomplete.
    months = ([(args.year - 1, 12)]
              + [(args.year, m) for m in range(1, 13)]
              + [(args.year + 1, 1)])

    with requests.Session() as s:
        s.headers["User-Agent"] = "flexibility-value/0.1 (research)"
        for year, month in months:
            ym = f"{year}{month:02d}"
            out = RAW / f"PRICE_AND_DEMAND_{ym}_{args.region}.csv"

            if out.exists() and out.stat().st_size > 1000:
                rows = out.read_text().count("\n") - 1
                print(f"  {ym}  cached      {rows:>6,} rows")
                total_rows += rows
                continue

            r = s.get(URL.format(ym=ym, region=args.region), timeout=60)
            r.raise_for_status()
            if not r.text.startswith("REGION"):
                raise SystemExit(f"{ym}: unexpected content, got {r.text[:80]!r}")

            out.write_text(r.text, encoding="utf-8")
            rows = r.text.count("\n") - 1
            print(f"  {ym}  downloaded  {rows:>6,} rows")
            total_rows += rows

    print(f"\n{args.region} {args.year}: {total_rows:,} five-minute intervals "
          f"(expect ~{365 * 288:,})")


if __name__ == "__main__":
    main()
