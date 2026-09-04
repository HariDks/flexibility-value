"""Download the full published gas-price history for all three markets.

The gas comparison originally ran on 2025 alone, while prices ran 25
market-years. That was a scope decision, not a data limitation — every one of
these series was already public and long:

* **Spain** — Eurostat `nrg_pc_203`, band I4 (100,000–999,999 GJ/yr), excluding
  VAT and other recoverable taxes. Bi-annual from 2007. That tax basis is the
  right one for an industrial buyer, who recovers VAT but pays levies, and it
  reproduces the 43.20 EUR/MWh the single-year study used.
* **MISO** — EIA series `N3035MN3`, Minnesota natural gas industrial price,
  annual, dollars per thousand cubic feet.
* **South Australia** — the AER's STTM quarterly register, already in
  `data/raw/aemo/`. It covers 64 quarters from September 2010; the single-year
  study used four of them.

2022 is the reason this matters: Spanish industrial gas averaged **90.50
EUR/MWh** that year against 40.45 in 2025.

    python src/fetch_gas.py
"""

import io
import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"

EUROSTAT = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/"
            "data/nrg_pc_203?format=JSON&geo=ES&lang=EN&siec=G3000"
            "&nrg_cons=GJ100000-999999&unit=KWH&currency=EUR&tax=X_VAT")
EIA = "https://www.eia.gov/dnav/ng/hist_xls/N3035MN3a.xls"
AER = "AER_STTM - Quarterly prices_1_20260717164350.CSV"

# 1 Mcf of natural gas -> MWh. 1.037 MMBtu per Mcf, 0.293071 MWh per MMBtu.
MCF_TO_MWH = 1.037 * 0.293071
GJ_TO_MWH = 1 / 3.6


def spain() -> pd.Series:
    s = requests.Session()
    s.headers["User-Agent"] = "flexibility-value/0.1 (research)"
    d = s.get(EUROSTAT, timeout=300).json()
    inv = {v: k for k, v in d["dimension"]["time"]["category"]["index"].items()}
    half = {inv[int(k)]: v * 1000 for k, v in d["value"].items()}  # /kWh -> /MWh
    by_year: dict[int, list[float]] = {}
    for period, val in half.items():
        by_year.setdefault(int(period[:4]), []).append(val)
    return pd.Series({y: sum(v) / len(v) for y, v in sorted(by_year.items())},
                     name="eur_per_mwh_gas")


def miso() -> pd.Series:
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (research; flexibility-value)"
    r = s.get(EIA, timeout=300)
    r.raise_for_status()
    x = pd.read_excel(io.BytesIO(r.content), sheet_name=1, skiprows=2)
    x.columns = ["date", "usd_per_mcf"]
    x = x.dropna()
    return pd.Series(
        {int(pd.Timestamp(d).year): v / MCF_TO_MWH
         for d, v in zip(x["date"], x["usd_per_mcf"])},
        name="usd_per_mwh_gas").sort_index()


def south_australia() -> pd.Series:
    d = pd.read_csv(RAW / "aemo" / AER)
    d = d.dropna(subset=["Adelaide ($ per gigajoule)"])
    # "Sep 10" style quarter labels; the year is a two-digit suffix.
    yr = d["Quarter Ending"].str.extract(r"(\d{2})$")[0].astype(int) + 2000
    val = d["Adelaide ($ per gigajoule)"].astype(float) / GJ_TO_MWH
    return (pd.DataFrame({"year": yr, "v": val}).groupby("year")["v"].mean()
            .rename("aud_per_mwh_gas"))


def main() -> None:
    series = {"Spain": spain(), "MISO": miso(),
              "South Australia": south_australia()}

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {m: {int(y): round(float(v), 4) for y, v in s.items()}
               for m, s in series.items()}
    dest = OUT / "gas_prices.json"
    dest.write_text(json.dumps(payload, indent=1))

    print("Gas price per MWh of gas burnt, by year\n")
    print(f"  {'year':>6}{'Spain EUR':>12}{'S.Aus AUD':>12}{'MISO USD':>11}")
    years = sorted(set().union(*[set(s.index) for s in series.values()]))
    for y in years:
        if y < 2016:
            continue
        row = f"  {y:>6}"
        for m in ("Spain", "South Australia", "MISO"):
            v = series[m].get(y)
            row += f"{v:>12.2f}" if v is not None and not pd.isna(v) else f"{'—':>12}"
        print(row)
    print(f"\n  -> {dest.relative_to(ROOT)}")

    # The single-year study's figures, as a check that nothing has shifted.
    print("\n  reconciles with the 2025-only study:")
    for m, want in (("Spain", 43.20), ("South Australia", 46.80),
                    ("MISO", 21.82)):
        got = float(series[m].get(2025, float("nan")))
        flag = "ok" if abs(got - want) / want < 0.02 else "CHECK"
        print(f"    {m:<18}{want:>9.2f} used{got:>10.2f} now   {flag}")


if __name__ == "__main__":
    main()
