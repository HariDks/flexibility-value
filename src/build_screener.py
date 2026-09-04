"""Precompute the screener's model layer.

The screener lets someone type their own network charges and see whether a
flexible load wins. That has to be exact — if a number on the page disagrees
with `RESULTS.md`, the whole project's credibility goes with it — so the
scheduler is never reimplemented in the browser.

It does not need to be. **The battery's schedule depends on the tariff's
*structure*, not on its prices.** Given a market, a rule for how peak demand is
measured, and a charge rate, the schedule is fixed; what a particular set of
euros per MWh and euros per kW does is only change how that schedule is *billed*.

So this runs the real scheduler once per (market, rule, charge rate) and records
four numbers per run — heat delivered, wholesale spend, peak drawn, and peak
drawn inside the window. Any tariff can then be evaluated from those four
numbers by arithmetic the browser can do exactly:

    bill = wholesale spend
         + energy_rate  * MWh delivered
         + capacity_rate * peak drawn

    python src/build_screener.py
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, ES_POWER_EUR_KW_YR, SA_RATES,
                    MISO_DEMAND_USD_KW_MONTH, MISO_ECO_USD_MWH,
                    MISO_EITE_USD_MWH, MISO_RRCR_DEMAND_USD_KW,
                    MISO_TCR_DEMAND_USD_KW)

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "explainer" / "screener-data.json"

DEMAND, STORAGE_H, YEAR = 10.0, 12.0, 2025
LOSS = 1 - (1 - 0.01) ** (1 / 24)
RATES = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)

# Each market: file stem, price column, local timezone, currency, the forecast
# horizon it really has, and the months its system peaks in.
MARKETS = {
    "spain": dict(stem="prices_spain", col="price_eur_mwh", tz="Europe/Madrid",
                  currency="EUR", horizon=24, peak_months=(6, 7, 8, 9),
                  label="Spain", note="day-ahead market, 24h visibility"),
    "miso": dict(stem="prices_miso", col="price_usd_mwh", tz="US/Central",
                 currency="USD", horizon=24, peak_months=(6, 7, 8, 9),
                 label="MISO (Minnesota)", note="day-ahead market, 24h visibility"),
    "sa": dict(stem="prices_sa", col="price_aud_mwh", tz="Australia/Adelaide",
               currency="AUD", horizon=6, peak_months=(11, 12, 1, 2, 3),
               label="South Australia", note="no day-ahead market, 6h visibility"),
    "nsw": dict(stem="prices_nem_NSW1", col="price_aud_mwh",
                tz="Australia/Sydney", currency="AUD", horizon=6,
                peak_months=(11, 12, 1, 2, 3), label="New South Wales",
                note="no day-ahead market, 6h visibility"),
    "qld": dict(stem="prices_nem_QLD1", col="price_aud_mwh",
                tz="Australia/Brisbane", currency="AUD", horizon=6,
                peak_months=(11, 12, 1, 2, 3), label="Queensland",
                note="no day-ahead market, 6h visibility"),
    "vic": dict(stem="prices_nem_VIC1", col="price_aud_mwh",
                tz="Australia/Melbourne", currency="AUD", horizon=6,
                peak_months=(11, 12, 1, 2, 3), label="Victoria",
                note="no day-ahead market, 6h visibility"),
    "tas": dict(stem="prices_nem_TAS1", col="price_aud_mwh",
                tz="Australia/Hobart", currency="AUD", horizon=6,
                peak_months=(11, 12, 1, 2, 3), label="Tasmania",
                note="no day-ahead market, 6h visibility"),
}

# How the network measures the peak it bills you on. These are the shapes real
# tariffs actually use, not arbitrary settings.
RULES = {
    "anytime": dict(label="Your worst moment, any hour, all year",
                    hours=None, seasonal=False,
                    example="ElectraNet, MISO Schedule 632"),
    "window_season": dict(label="17:00-21:00, peak season only",
                          hours=range(17, 21), seasonal=True,
                          example="SA Power Networks"),
    "window_year": dict(label="17:00-21:00, all year",
                        hours=range(17, 21), seasonal=False,
                        example="many US commercial tariffs"),
}

# Real tariffs, as starting points someone can then edit. Capacity is converted
# to one number — currency per kW of billed peak per year — so the two dials
# stay comparable across markets.
PRESETS = {
    "Spain 6.3TD": dict(currency="EUR", energy=ES_ENERGY_EUR_MWH[6],
                        capacity=sum(ES_POWER_EUR_KW_YR.values()),
                        rule="window_season",
                        note="six time bands; the figure shown sums all six"),
    "SA Power Networks (STR)": dict(
        currency="AUD", energy=SA_RATES["2026-27"]["energy_mwh"],
        capacity=SA_RATES["2026-27"]["peak"] * 365, rule="window_season",
        note="daily charge on peak-window demand, annualised"),
    "ElectraNet (transmission)": dict(
        currency="AUD", energy=SA_RATES["2026-27"]["energy_mwh"],
        capacity=SA_RATES["2026-27"]["anytime"] * 365, rule="anytime",
        note="agreed maximum demand, no window"),
    "Otter Tail Schedule 632": dict(
        currency="USD", energy=MISO_ECO_USD_MWH + MISO_EITE_USD_MWH,
        capacity=(4 * MISO_DEMAND_USD_KW_MONTH["summer"]
                  + 8 * MISO_DEMAND_USD_KW_MONTH["winter"]
                  + 12 * MISO_TCR_DEMAND_USD_KW
                  + 6 * (MISO_RRCR_DEMAND_USD_KW["h1"]
                         + MISO_RRCR_DEMAND_USD_KW["h2"])),
        rule="anytime", note="monthly demand charge plus riders, annualised"),
}


def window_mask(idx: pd.DatetimeIndex, rule: dict,
                peak_months: tuple) -> np.ndarray:
    """Hours in which the network is watching for your peak."""
    if rule["hours"] is None:
        return np.ones(len(idx), dtype=bool)
    m = np.isin(idx.hour, list(rule["hours"]))
    if rule["seasonal"]:
        m &= np.isin(idx.month, list(peak_months))
    return m


def run(key: str, cfg: dict) -> list[dict]:
    d = pd.read_csv(P / f"{cfg['stem']}_{YEAR}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(cfg["tz"])
    s = d.set_index("ts")[cfg["col"]]
    idx, pr = s.index, s.to_numpy()
    total_mwh = len(pr) * DEMAND
    flat = np.full(len(pr), DEMAND)

    rows = []
    for rule_key, rule in RULES.items():
        watched = window_mask(idx, rule, cfg["peak_months"])

        # The inflexible counterfactual draws a flat 10 MW, so its billed peak
        # is 10 MW under every rule. Recorded per rule anyway, so the browser
        # never has to special-case it.
        rows.append(dict(
            market=key, rule=rule_key, charge_rate=None, flexible=False,
            mwh=total_mwh, wholesale=float((flat * pr).sum()),
            peak_mw=float(flat.max()),
            peak_billed_mw=float(flat[watched].max()) if watched.any() else 0.0))

        for rate in RATES:
            # Under a windowed rule the battery holds off inside the window,
            # which is the whole point of a windowed rule. Under "anytime"
            # there is nowhere to hide and only the charge rate matters.
            cap = (np.where(watched, 0.0, rate * DEMAND) if rule["hours"]
                   else np.full(len(pr), rate * DEMAND))
            try:
                ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, cap,
                              horizon=cfg["horizon"], loss_per_hour=LOSS)
            except RuntimeError:
                rows.append(dict(market=key, rule=rule_key, charge_rate=rate,
                                 flexible=True, feasible=False))
                continue
            rows.append(dict(
                market=key, rule=rule_key, charge_rate=rate, flexible=True,
                feasible=True, mwh=total_mwh,
                wholesale=float((ch * pr).sum()),
                peak_mw=float(ch.max()),
                peak_billed_mw=(float(ch[watched].max()) if watched.any()
                                else 0.0)))
    return rows


def week_profile(key: str, cfg: dict, rule_key: str, rate: float) -> dict:
    """One representative week, for the chart: prices and what the battery buys.

    The week is chosen by a stated rule rather than by eye — the week whose
    mean daily spread is closest to the year's median — so nobody has to take
    on trust that it is typical.
    """
    d = pd.read_csv(P / f"{cfg['stem']}_{YEAR}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(cfg["tz"])
    s = d.set_index("ts")[cfg["col"]]
    idx, pr = s.index, s.to_numpy()

    day = pd.Series(pr, index=idx).groupby(idx.date)
    spread = (day.max() - day.min())
    weekly = spread.groupby(pd.to_datetime(spread.index).isocalendar().week).mean()
    target = weekly.sub(spread.median()).abs().idxmin()
    sel = pd.to_datetime(idx.date).isocalendar().week == target
    sel = np.asarray(sel)

    rule = RULES[rule_key]
    watched = window_mask(idx, rule, cfg["peak_months"])
    cap = (np.where(watched, 0.0, rate * DEMAND) if rule["hours"]
           else np.full(len(pr), rate * DEMAND))
    ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, cap, horizon=cfg["horizon"],
                  loss_per_hour=LOSS)

    return dict(start=str(idx[sel][0]), hours=int(sel.sum()),
                price=[round(float(x), 2) for x in pr[sel]],
                draw=[round(float(x), 2) for x in ch[sel]],
                watched=[bool(x) for x in watched[sel]])


def main() -> None:
    rows, weeks = [], {}
    for key, cfg in MARKETS.items():
        rows += run(key, cfg)
        # Both sides of the argument, on the same week, at the same 4x rate.
        weeks[key] = {r: week_profile(key, cfg, r, 4.0)
                      for r in ("window_season", "anytime")}
        print(f"  {cfg['label']:<22} done")

    payload = dict(
        year=YEAR, demand_mw=DEMAND, storage_hours=STORAGE_H,
        standby_loss_per_day=0.01, charge_rates=list(RATES),
        markets={k: {a: b for a, b in v.items()
                     if a not in ("stem", "col", "tz")}
                 for k, v in MARKETS.items()},
        rules={k: dict(label=v["label"], example=v["example"],
                       hours=(list(v["hours"]) if v["hours"] else None),
                       seasonal=v["seasonal"]) for k, v in RULES.items()},
        presets=PRESETS, runs=rows, weeks=weeks)

    for m in payload["markets"].values():
        m["peak_months"] = list(m["peak_months"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"\n{len(rows)} runs, {len(weeks)} weeks -> "
          f"{OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
