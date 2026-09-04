"""Precompute the screener's model layer, and prove it reproduces the study.

The screener lets someone type their own network charges and see whether a
flexible load wins. That has to be exact — if a number on the page disagrees
with `RESULTS.md`, the project's credibility goes with it — so the scheduler is
never reimplemented in the browser.

It does not need to be. **A flat per-MWh charge is the same number added to
every hour, so it cannot change which hours are cheapest.** Neither can a
capacity charge, which falls on the peak rather than on the timing. So given a
market, a rule for when the network is watching, and a charge rate, the
schedule is fixed — and a particular set of currency-per-MWh and
currency-per-kW figures only changes how that schedule is *billed*.

This runs the real scheduler once per (market, rule, charge rate) and records
the handful of summary statistics that any of these tariffs bills on:

    mwh                   heat delivered
    wholesale             spend at market prices
    peak_any              highest instant, whole year          ElectraNet
    peak_<window>         highest instant in each window shape
    peakavg_<window>      highest daily average in each shape  SA Power Networks
    monthly_peaks         twelve monthly maxima                MISO Schedule 632
    es_contracted         six contracted powers                Spain 6.xTD
    es_energy             six per-period energy volumes        Spain 6.xTD

Three different networks read "your peak" three different ways, so recording
one number would have quietly mis-billed two of them.

`--verify` then rebuilds each real tariff from those statistics alone and
compares against `tariff.py`. If the browser's arithmetic cannot reproduce the
study, this says so rather than shipping.

    python src/build_screener.py
    python src/build_screener.py --verify
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, ES_POWER_EUR_KW_YR, SA_RATES,
                    SA_PEAK_MONTHS, SA_PEAK_WINDOW,
                    MISO_CUSTOMER_USD_MONTH, MISO_DEMAND_USD_KW_MONTH,
                    MISO_ECO_USD_MWH, MISO_EITE_USD_MWH,
                    MISO_RRCR_DEMAND_USD_KW, MISO_SUMMER_MONTHS,
                    MISO_TCR_DEMAND_USD_KW, miso_network_cost,
                    sa_network_cost, spain_network_cost, spain_periods)

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "explainer" / "screener-data.json"

DEMAND, STORAGE_H, YEAR = 10.0, 12.0, 2025
LOSS = 1 - (1 - 0.01) ** (1 / 24)
RATES = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)

MARKETS = {
    "spain": dict(stem="prices_spain", col="price_eur_mwh", tz="Europe/Madrid",
                  currency="EUR", horizon=24, label="Spain",
                  note="day-ahead market, 24h visibility"),
    "miso": dict(stem="prices_miso", col="price_usd_mwh", tz="US/Central",
                 currency="USD", horizon=24, label="MISO (Minnesota)",
                 note="day-ahead market, 24h visibility"),
    "sa": dict(stem="prices_sa", col="price_aud_mwh", tz="Australia/Adelaide",
               currency="AUD", horizon=6, label="South Australia",
               note="no day-ahead market, 6h visibility"),
    "nsw": dict(stem="prices_nem_NSW1", col="price_aud_mwh",
                tz="Australia/Sydney", currency="AUD", horizon=6,
                label="New South Wales", note="no day-ahead market, 6h"),
    "qld": dict(stem="prices_nem_QLD1", col="price_aud_mwh",
                tz="Australia/Brisbane", currency="AUD", horizon=6,
                label="Queensland", note="no day-ahead market, 6h"),
    "vic": dict(stem="prices_nem_VIC1", col="price_aud_mwh",
                tz="Australia/Melbourne", currency="AUD", horizon=6,
                label="Victoria", note="no day-ahead market, 6h"),
    "tas": dict(stem="prices_nem_TAS1", col="price_aud_mwh",
                tz="Australia/Hobart", currency="AUD", horizon=6,
                label="Tasmania", note="no day-ahead market, 6h"),
}

# When the network is watching for your peak. These are the shapes real tariffs
# use; the battery holds off inside a window, which is the point of a window.
RULES = {
    "anytime": dict(label="Any hour, all year", hours=None, months=None,
                    example="ElectraNet, Otter Tail Schedule 632"),
    "window_season": dict(label="17:00-21:00, peak season only",
                          hours=tuple(SA_PEAK_WINDOW),
                          months=tuple(SA_PEAK_MONTHS),
                          example="SA Power Networks"),
    "window_year": dict(label="17:00-21:00, all year",
                        hours=tuple(SA_PEAK_WINDOW), months=None,
                        example="many US commercial tariffs"),
}


def load(cfg: dict) -> pd.Series:
    d = pd.read_csv(P / f"{cfg['stem']}_{YEAR}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(cfg["tz"])
    return d.set_index("ts")[cfg["col"]]


def watching(idx: pd.DatetimeIndex, rule: dict) -> np.ndarray:
    if rule["hours"] is None:
        return np.ones(len(idx), dtype=bool)
    m = np.isin(idx.hour, list(rule["hours"]))
    if rule["months"] is not None:
        m &= np.isin(idx.month, list(rule["months"]))
    return m


def stats(draw: np.ndarray, prices: np.ndarray, idx: pd.DatetimeIndex,
          market: str) -> dict:
    """Every summary figure any of these tariffs bills on.

    The peak is recorded under **every** window definition, not just the one
    the battery was playing against. Where the battery holds off is a strategy;
    where the network measures your peak is the tariff. They coincide when the
    battery is avoiding the right window and diverge otherwise — and "is
    avoiding the window even worth it?" is exactly what the screener has to be
    able to answer, so the two must be recorded separately.
    """
    monthly = (pd.Series(draw, index=idx).groupby(idx.month).max()
               .reindex(range(1, 13)).fillna(0.0))
    out = dict(
        mwh=round(float(draw.sum()), 3),
        wholesale=round(float((draw * prices).sum()), 2),
        peak_any=round(float(draw.max(initial=0.0)), 4),
        monthly_peaks=[round(float(x), 4) for x in monthly],
    )

    for wk, rule in RULES.items():
        w = watching(idx, rule)
        avg = 0.0
        if w.any():
            avg = float(pd.Series(draw[w], index=idx[w])
                        .groupby(idx[w].date).mean().max())
        out[f"peak_{wk}"] = round(float(draw[w].max(initial=0.0)), 4)
        out[f"peakavg_{wk}"] = round(avg, 4)

    if market == "spain":
        # Contracted power is billed per period and must not decrease from P1
        # to P6, so contracting more in the cheap late periods is allowed.
        per = spain_periods(idx)
        running, contracted, energy = 0.0, [], []
        for p in range(1, 7):
            running = max(running, float(draw[per == p].max(initial=0.0)))
            contracted.append(round(running, 4))
            energy.append(round(float(draw[per == p].sum()), 3))
        out["es_contracted"] = contracted
        out["es_energy"] = energy
    return out


def run_market(key: str, cfg: dict) -> tuple[list[dict], dict]:
    s = load(cfg)
    idx, pr = s.index, s.to_numpy()
    flat = np.full(len(pr), DEMAND)

    rows, schedules = [], {}
    for rk, rule in RULES.items():
        watched = watching(idx, rule)

        rows.append(dict(market=key, rule=rk, charge_rate=None, flexible=False,
                         feasible=True, **stats(flat, pr, idx, key)))

        for rate in RATES:
            cap = (np.where(watched, 0.0, rate * DEMAND) if rule["hours"]
                   else np.full(len(pr), rate * DEMAND))
            try:
                ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, cap,
                              horizon=cfg["horizon"], loss_per_hour=LOSS)
            except RuntimeError:
                rows.append(dict(market=key, rule=rk, charge_rate=rate,
                                 flexible=True, feasible=False))
                continue
            rows.append(dict(market=key, rule=rk, charge_rate=rate,
                             flexible=True, feasible=True,
                             **stats(ch, pr, idx, key)))
            if rate == 4.0:
                schedules[rk] = ch

    # One week, the same one for every rule, so the comparison is like for like.
    sel = pick_week(idx, pr)
    profiles = {rk: dict(price=[round(float(x), 2) for x in pr[sel]],
                         draw=[round(float(x), 2) for x in ch[sel]],
                         soc=[round(float(x), 2) for x in tank(ch)[sel]],
                         watched=[bool(x) for x in
                                  watching(idx, RULES[rk])[sel]])
                for rk, ch in schedules.items()}
    for prof in profiles.values():
        prof["start"] = str(idx[sel][0])[:16]
    return rows, profiles


def tank(charge: np.ndarray) -> np.ndarray:
    """Heat sitting in the store after each hour.

    Reproduces the level `battery.schedule` carries internally: what was there
    an hour ago, less what leaked, plus what was bought, less what was burnt.
    Showing it is what makes the mechanism legible — the store fills in the
    cheap hours and then carries the factory through the expensive ones.
    """
    keep = 1.0 - LOSS
    soc = np.zeros(len(charge))
    prev = 0.0
    for h in range(len(charge)):
        prev = soc[h] = prev * keep + charge[h] - DEMAND
    return soc


def pick_week(idx, pr) -> np.ndarray:
    """Which week to draw, chosen by a stated rule rather than by eye.

    The week whose mean daily spread is closest to the year's median — so
    nobody has to take on trust that it is typical.

    **Restricted to the peak season.** A seasonal demand window only bites
    inside its own months, so a week outside them shows two tariffs behaving
    identically and demonstrates nothing. The first version of this picked a
    July week in South Australia, where SA Power Networks' November-to-March
    window does not apply at all.
    """
    day = pd.Series(pr, index=idx).groupby(idx.date)
    spread = day.max() - day.min()
    weeks = pd.to_datetime(spread.index).isocalendar().week
    months = pd.to_datetime(spread.index).month

    season = RULES["window_season"]["months"]
    in_season = set(weeks[np.isin(months, list(season))])
    by_week = spread.groupby(weeks).mean()
    candidates = by_week[by_week.index.isin(in_season)]
    if candidates.empty:
        candidates = by_week

    target = candidates.sub(spread.median()).abs().idxmin()
    return np.asarray(pd.to_datetime(idx.date).isocalendar().week == target)


# --------------------------------------------------------------------- verify

def verify(rows: list[dict]) -> bool:
    """Rebuild each real tariff from the recorded statistics alone.

    If the browser cannot reproduce tariff.py from these numbers, the design is
    wrong and the page should not ship.
    """
    print("\nVerifying the recorded statistics reproduce tariff.py\n")
    print(f"  {'tariff':<28}{'from tariff.py':>16}{'from stats':>14}"
          f"{'diff':>10}")
    ok = True

    def check(name, a, b, tol=0.01):
        nonlocal ok
        d = abs(a - b)
        if d > tol:
            ok = False
        print(f"  {name:<28}{a:>16.4f}{b:>14.4f}{d:>10.4f}"
              + ("" if d <= tol else "   MISMATCH"))

    idx_cache = {}
    for key in ("sa", "miso", "spain"):
        cfg = MARKETS[key]
        s = load(cfg)
        idx_cache[key] = (s.index, s.to_numpy())

    # --- South Australia: daily-average window peak + anytime peak, per day
    idx, pr = idx_cache["sa"]
    r = SA_RATES["2026-27"]
    days = len(np.unique(idx.date))
    for rk in ("window_season", "anytime"):
        row = next(x for x in rows if x["market"] == "sa" and x["rule"] == rk
                   and x["charge_rate"] == 4.0)
        rebuilt = (days * (row["peakavg_window_season"] * 1000 * r["peak"]
                           + row["peak_any"] * 1000 * r["anytime"])
                   / row["mwh"])
        # SAPN measures its own window whatever strategy the battery played,
        # so both runs must reconcile — that is the point of recording the
        # peak under every window definition.
        watched = watching(idx, RULES[rk])
        capm = np.where(watched, 0.0, 4.0 * DEMAND) if RULES[rk]["hours"] \
            else np.full(len(pr), 4.0 * DEMAND)
        # South Australia's own horizon — `cfg` here would otherwise still be
        # bound to whichever market the cache loop finished on.
        ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, capm,
                      horizon=MARKETS["sa"]["horizon"], loss_per_hour=LOSS)
        truth = sa_network_cost(ch, idx, row["mwh"]).capacity_per_mwh
        check(f"SAPN capacity, {rk}", truth, rebuilt)

    # --- MISO: twelve monthly maxima, seasonal rates plus riders
    idx, pr = idx_cache["miso"]
    row = next(x for x in rows if x["market"] == "miso"
               and x["rule"] == "anytime" and x["charge_rate"] == 4.0)
    cap_total = MISO_CUSTOMER_USD_MONTH * 12
    for m, peak in enumerate(row["monthly_peaks"], start=1):
        rate = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                        else "winter"]
        rate += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap_total += peak * 1000 * rate
    ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, 4.0 * DEMAND, horizon=24,
                  loss_per_hour=LOSS)
    truth = miso_network_cost(ch, idx, row["mwh"], riders=True).capacity_per_mwh
    check("Otter Tail 632 capacity", truth, cap_total / row["mwh"])
    check("Otter Tail 632 energy",
          miso_network_cost(ch, idx, row["mwh"], riders=True).energy_per_mwh,
          MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)

    # --- Spain: six contracted powers, six energy bands
    idx, pr = idx_cache["spain"]
    row = next(x for x in rows if x["market"] == "spain"
               and x["rule"] == "anytime" and x["charge_rate"] == 4.0)
    ch = schedule(pr, DEMAND, STORAGE_H * DEMAND, 4.0 * DEMAND, horizon=24,
                  loss_per_hour=LOSS)
    truth = spain_network_cost(ch, idx, row["mwh"])
    cap = sum(row["es_contracted"][p - 1] * 1000 * ES_POWER_EUR_KW_YR[p]
              for p in range(1, 7)) / row["mwh"]
    ener = sum(row["es_energy"][p - 1] * ES_ENERGY_EUR_MWH[p]
               for p in range(1, 7)) / row["mwh"]
    check("Spain 6.3TD capacity", truth.capacity_per_mwh, cap)
    check("Spain 6.3TD energy", truth.energy_per_mwh, ener)

    print("\n  " + ("All tariffs reproduce from the recorded statistics."
                    if ok else "MISMATCH — do not ship this."))
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    rows, weeks = [], {}
    for key, cfg in MARKETS.items():
        r, w = run_market(key, cfg)
        rows += r
        weeks[key] = w
        print(f"  {cfg['label']:<22} {len(r)} runs")

    payload = dict(
        year=YEAR, demand_mw=DEMAND, storage_hours=STORAGE_H,
        standby_loss_per_day=0.01, charge_rates=list(RATES),
        markets={k: {a: b for a, b in v.items()
                     if a not in ("stem", "col", "tz")}
                 for k, v in MARKETS.items()},
        rules={k: dict(label=v["label"], example=v["example"],
                       hours=list(v["hours"]) if v["hours"] else None,
                       months=list(v["months"]) if v["months"] else None)
               for k, v in RULES.items()},
        runs=rows, weeks=weeks)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"\n{len(rows)} runs -> {OUT.relative_to(ROOT)} "
          f"({OUT.stat().st_size / 1024:.0f} KB)")

    if args.verify and not verify(rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
