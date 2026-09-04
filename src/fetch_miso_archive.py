"""Download MISO's monthly day-ahead LMP archives for older years.

MISO's daily report URLs only serve about two years. Older data is published as
**monthly zips** under the same path, and those go back much further — the
filename pattern is `YYYYMM_da_expost_lmp_csv.zip`. No account is needed; the
Market Report Archives page simply lists them.

The archive format is wide (one row per node, hours as columns HE 1..HE 24) and
stamped in MISO's fixed Eastern Standard clock, which the files state
explicitly. This converts it to the same per-day long format that
`fetch_miso.py` writes, so `load_miso.py` reads both without knowing which
route the data came from.

    python src/fetch_miso_archive.py --start 2018 --end 2022
"""

import argparse
import io
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "miso"
URL = "https://docs.misoenergy.org/marketreports/{ym}_da_expost_lmp_csv.zip"
HUB = "MINN.HUB"
KEEP = ["Interval Start", "Interval End", "Location", "LMP",
        "Energy", "Congestion", "Loss"]


def parse_day(text: str, hub: str) -> pd.DataFrame | None:
    """One daily archive file -> long format, one row per hour."""
    lines = text.splitlines()
    header = next((i for i, l in enumerate(lines) if l.startswith("Node,")), None)
    # The date sits in the first few lines, sometimes padded with trailing
    # commas to the width of the table. Match the pattern, do not measure length.
    date_line = None
    for l in lines[:6]:
        m = re.match(r"\s*(\d{1,2}/\d{1,2}/\d{4})", l)
        if m:
            date_line = m.group(1)
            break
    if header is None or date_line is None:
        return None

    df = pd.read_csv(io.StringIO("\n".join(lines[header:])))
    rows = df[df["Node"] == hub]
    if rows.empty:
        return None

    day = pd.to_datetime(date_line, format="%m/%d/%Y")
    hours = [c for c in df.columns if c.startswith("HE ")]
    # Hour-ending N covers the hour starting N-1, in a fixed -05:00 clock.
    start = (day + pd.to_timedelta([int(h.split()[1]) - 1 for h in hours],
                                   unit="h")).tz_localize("Etc/GMT+5")

    def series(kind):
        r = rows[rows["Value"] == kind]
        return (pd.to_numeric(r[hours].iloc[0], errors="coerce").to_numpy()
                if not r.empty else [None] * len(hours))

    # The archive gives LMP and its congestion (MCC) and loss (MLC) parts; the
    # energy component is the remainder. Only LMP is used downstream, but a
    # column labelled Energy should hold energy.
    lmp, mcc, mlc = (pd.Series(series(k), dtype="float64")
                     for k in ("LMP", "MCC", "MLC"))
    return pd.DataFrame({
        "Interval Start": start,
        "Interval End": start + pd.Timedelta(1, unit="h"),
        "Location": hub,
        "LMP": lmp.to_numpy(),
        "Energy": (lmp - mcc - mlc).to_numpy(),
        "Congestion": mcc.to_numpy(),
        "Loss": mlc.to_numpy(),
    })


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=int, default=2018)
    p.add_argument("--end", type=int, default=2022)
    p.add_argument("--hub", default=HUB)
    args = p.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    written = skipped = missing = 0

    with requests.Session() as s:
        s.headers["User-Agent"] = "flexibility-value/0.1 (research)"
        for year in range(args.start, args.end + 1):
            got = 0
            for month in range(1, 13):
                ym = f"{year}{month:02d}"
                try:
                    r = s.get(URL.format(ym=ym), timeout=120)
                except requests.RequestException:
                    missing += 1
                    continue
                if r.status_code != 200 or len(r.content) < 10_000:
                    missing += 1
                    continue
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    for name in z.namelist():
                        if not name.lower().endswith(".csv"):
                            continue
                        out = RAW / f"miso_da_{name[:8]}.csv"
                        if out.exists():
                            skipped += 1
                            continue
                        day = parse_day(z.read(name).decode("utf-8", "ignore"),
                                        args.hub)
                        if day is None:
                            continue
                        day[KEEP].to_csv(out, index=False)
                        written += 1
                        got += 1
            print(f"  {year}: {got} days written")

    print(f"\nwritten {written}, already present {skipped}, "
          f"months unavailable {missing}")


if __name__ == "__main__":
    main()
