"""Download several MISO pricing points at once, to test node sensitivity.

Decision 24 picked MINN.HUB because it is the published hub closest to Big
Stone City. That was never tested against alternatives, and MISO publishes
2,464 pricing points — including **OTP.OTP**, the load zone of Otter Tail
Power itself, which is the utility whose Schedule 632 and TMEP tariff this
study models. For a *load*, the load zone is the settlement point; a hub is a
trading construct. So OTP.OTP is arguably the right answer and MINN.HUB the
approximation.

Two routes, same output format, because MISO serves recent and old data
differently:

* ``--source daily``   2023 onward. One request per day, all locations at once.
* ``--source archive`` 2018-2022. One request per month, wide format.

    python src/fetch_miso_nodes.py --year 2025 --source daily
    python src/fetch_miso_nodes.py --year 2020 --source archive
"""

import argparse
import io
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "miso_nodes"
ARCHIVE = "https://docs.misoenergy.org/marketreports/{ym}_da_expost_lmp_csv.zip"

# Otter Tail's own load zone first, then every MISO hub.
LOCATIONS = ["OTP.OTP", "MINN.HUB", "ARKANSAS.HUB", "ILLINOIS.HUB",
             "INDIANA.HUB", "LOUISIANA.HUB", "MICHIGAN.HUB", "MS.HUB",
             "TEXAS.HUB"]
KEEP = ["Interval Start", "Interval End", "Location", "LMP"]


def days_in_year(year: int):
    """The year plus a day either side - see fetch_miso.py on the -05:00 clock."""
    d, end = date(year - 1, 12, 31), date(year + 1, 1, 2)
    while d < end:
        yield d
        d += timedelta(days=1)


def fetch_day(d: date, locations: list[str]) -> str:
    import gridstatus

    out = RAW / f"nodes_{d:%Y%m%d}.csv"
    if out.exists() and out.stat().st_size > 200:
        return "cached"
    try:
        df = gridstatus.MISO().get_lmp(date=str(d), market="DAY_AHEAD_HOURLY",
                                       locations=locations)
        if df.empty:
            return "empty"
        df[KEEP].to_csv(out, index=False)
        return "downloaded"
    except Exception as exc:                      # noqa: BLE001 - report, move on
        return f"error: {exc.__class__.__name__}"


def parse_archive_day(text: str, locations: list[str]) -> pd.DataFrame | None:
    """One wide archive day -> long format, every requested location."""
    lines = text.splitlines()
    header = next((i for i, l in enumerate(lines) if l.startswith("Node,")), None)
    date_line = next((m.group(1) for l in lines[:6]
                      if (m := re.match(r"\s*(\d{1,2}/\d{1,2}/\d{4})", l))), None)
    if header is None or date_line is None:
        return None

    df = pd.read_csv(io.StringIO("\n".join(lines[header:])))
    rows = df[(df["Node"].isin(locations)) & (df["Value"] == "LMP")]
    if rows.empty:
        return None

    day = pd.to_datetime(date_line, format="%m/%d/%Y")
    hours = [c for c in df.columns if c.startswith("HE ")]
    start = (day + pd.to_timedelta([int(h.split()[1]) - 1 for h in hours],
                                   unit="h")).tz_localize("Etc/GMT+5")

    out = []
    for _, r in rows.iterrows():
        out.append(pd.DataFrame({
            "Interval Start": start,
            "Interval End": start + pd.Timedelta(1, unit="h"),
            "Location": r["Node"],
            "LMP": pd.to_numeric(r[hours], errors="coerce").to_numpy(),
        }))
    return pd.concat(out, ignore_index=True)


def run_archive(year: int, locations: list[str]) -> None:
    written = missing = skipped = 0
    # January of the following year too. MISO's market clock is a fixed -05:00
    # and Central time is -06:00 in winter, so the last local hour of the year
    # (23:00 on 31 December) is stamped 00:00 on 1 January in the market's
    # clock, and lives in the next month's file. Without it the year is 8,759
    # hours instead of 8,760.
    months = [(year, m) for m in range(1, 13)] + [(year + 1, 1)]
    with requests.Session() as s:
        s.headers["User-Agent"] = "flexibility-value/0.1 (research)"
        for y, month in months:
            ym = f"{y}{month:02d}"
            r = s.get(ARCHIVE.format(ym=ym), timeout=300)
            if r.status_code != 200 or len(r.content) < 10_000:
                missing += 1
                continue
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                for name in z.namelist():
                    if not name.lower().endswith(".csv"):
                        continue
                    out = RAW / f"nodes_{name[:8]}.csv"
                    if out.exists():
                        skipped += 1
                        continue
                    day = parse_archive_day(
                        z.read(name).decode("utf-8", "ignore"), locations)
                    if day is None:
                        continue
                    day.to_csv(out, index=False)
                    written += 1
    print(f"  {year}: {written} days written, {skipped} cached, "
          f"{missing} months unavailable")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--source", choices=("daily", "archive"), default="daily")
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    if args.source == "archive":
        run_archive(args.year, LOCATIONS)
        return

    days = list(days_in_year(args.year))
    print(f"{len(days)} days requested, {len(LOCATIONS)} locations -> {RAW}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda d: fetch_day(d, LOCATIONS), days))
    counts: dict[str, int] = {}
    for r in results:
        counts[r] = counts.get(r, 0) + 1
    for k, v in sorted(counts.items()):
        print(f"  {k:<24}{v:>5}")


if __name__ == "__main__":
    main()
