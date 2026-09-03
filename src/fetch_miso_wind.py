"""Download MISO's hourly generation fuel mix, to model TMEP's wind-coincidence rule.

TMEP requires the load to "take service coincident with and not to exceed the
hourly generating output of a nearby specifically identified wind and/or solar
generation resource." Output for one named plant is not public, so MISO's
**North region** wind generation is used as the proxy — North covers Minnesota
and the Dakotas, where Big Stone sits.

The report published on date D carries the market data for D-1.

    python src/fetch_miso_wind.py --year 2025
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "miso_wind"
URL = "https://docs.misoenergy.org/marketreports/{ymd}_sr_gfm.xlsx"


def fetch(d: date, session: requests.Session) -> tuple[date, str]:
    out = RAW / f"gfm_{d:%Y%m%d}.xlsx"
    if out.exists() and out.stat().st_size > 5000:
        return d, "cached"
    try:
        r = session.get(URL.format(ymd=f"{d:%Y%m%d}"), timeout=45)
        if r.status_code == 200 and len(r.content) > 5000:
            out.write_bytes(r.content)
            return d, "downloaded"
        return d, f"http {r.status_code}"
    except requests.RequestException as exc:
        return d, f"error: {exc.__class__.__name__}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    # publish date D holds market date D-1, so fetch one day past year end
    days = [date(args.year, 1, 1) + timedelta(days=i) for i in range(367)]
    days = [d for d in days if d <= date(args.year + 1, 1, 2)]

    with requests.Session() as s:
        s.headers["User-Agent"] = "flexibility-value/0.1 (research)"
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda d: fetch(d, s), days))

    counts: dict[str, int] = {}
    for _, st in results:
        counts[st.split(":")[0]] = counts.get(st.split(":")[0], 0) + 1
    for k, v in sorted(counts.items()):
        print(f"  {k:>14}: {v}")
    bad = [d for d, st in results if st not in ("cached", "downloaded")]
    print(f"\n{len(days) - len(bad)} of {len(days)} files present.")


if __name__ == "__main__":
    main()
