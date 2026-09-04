"""Regenerate every headline number, across every year held.

This is the source for RESULTS.md. Run it and the file should agree with it.

    python src/results.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS,
                    SA_PEAK_WINDOW, MISO_DEMAND_USD_KW_MONTH,
                    MISO_ECO_USD_MWH, MISO_EITE_USD_MWH, MISO_RRCR_DEMAND_USD_KW,
                    MISO_SUMMER_MONTHS, MISO_TCR_DEMAND_USD_KW,
                    miso_network_cost, sa_network_cost, spain_network_cost,
                    spain_periods)

P = Path(__file__).resolve().parents[1] / "data" / "processed"
DEMAND, ST, LOSS = 10.0, 120.0, 1 - (1 - 0.01) ** (1 / 24)
GST = 1.10
EN_CAP_COMMON = (160.866 + 62.608) / GST      # ElectraNet non-locational + common
EN_ENERGY = (24.994 + 9.727) / GST
EN_LOC = {"Para 66kV": 54.996 / GST, "Brinkworth 33kV": 128.158 / GST,
          "Ardrossan West 33kV": 194.826 / GST, "Berri 66kV": 227.745 / GST}


def load(stem, col, tz, yr):
    d = pd.read_csv(P / f"{stem}_{yr}.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


def years(stem):
    return sorted(int(f.stem.split("_")[-1]) for f in P.glob(f"{stem}_*.csv"))


def spain(yr):
    s = load("prices_spain", "price_eur_mwh", "Europe/Madrid", yr)
    idx, pr = s.index, s.to_numpy()
    d, per = len(pr) * DEMAND, spain_periods(s.index)
    netE = np.array([ES_ENERGY_EUR_MWH[p] for p in per])
    flat = np.full(len(pr), DEMAND)
    base = (flat * pr).sum() / d + spain_network_cost(flat, idx, d).total_per_mwh
    naive = schedule(pr, DEMAND, ST, 4 * DEMAND, horizon=24, loss_per_hour=LOSS)
    nv = (naive * pr).sum() / d + spain_network_cost(naive, idx, d).total_per_mwh
    aware = schedule(pr + netE, DEMAND, ST,
                     np.where(np.isin(per, (4, 5, 6)), 4, 1) * DEMAND,
                     horizon=24, loss_per_hour=LOSS)
    aw = (aware * pr).sum() / d + spain_network_cost(aware, idx, d).total_per_mwh
    return pr.mean(), 100 * (pr < 0).mean(), base, nv, aw


def sa(yr):
    s = load("prices_sa", "price_aud_mwh", "Australia/Adelaide", yr)
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    flat = np.full(len(pr), DEMAND)
    base = (flat * pr).sum() / d + sa_network_cost(flat, idx, d).total_per_mwh
    naive = schedule(pr, DEMAND, ST, 4 * DEMAND, horizon=6, loss_per_hour=LOSS)
    nv = (naive * pr).sum() / d + sa_network_cost(naive, idx, d).total_per_mwh
    blk = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
           & np.isin(idx.month, list(SA_PEAK_MONTHS)))
    aware = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, ST,
                     np.where(blk, 0.0, 4 * DEMAND), horizon=6, loss_per_hour=LOSS)
    aw = (aware * pr).sum() / d + sa_network_cost(aware, idx, d).total_per_mwh
    # ElectraNet counterfactual: nothing to dodge, so just chase price
    en = schedule(pr, DEMAND, ST, 4 * DEMAND, horizon=6, loss_per_hour=LOSS)
    days = len(np.unique(idx.date))
    enr = {}
    for loc, lc in EN_LOC.items():
        capd = lc + EN_CAP_COMMON
        f = (flat * pr).sum() / d + EN_ENERGY + flat.max() * capd * days / d
        b = (en * pr).sum() / d + EN_ENERGY + en.max() * capd * days / d
        enr[loc] = 100 * (f - b) / f
    return pr.mean(), 100 * (pr < 0).mean(), base, nv, aw, enr


def miso(yr):
    s = load("prices_miso", "price_usd_mwh", "US/Central", yr)
    idx, pr = s.index, s.to_numpy()
    d = len(pr) * DEMAND
    base = miso_network_cost(np.full(len(pr), DEMAND), idx, d,
                             utility_supplied=True).total_per_mwh
    cap = 282.0 * 12
    for m in range(1, 13):
        r = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                     else "winter"]
        r += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap += DEMAND * 1000 * r
    out = {}
    for mult in (1.5, 4.0):
        ch = schedule(pr, DEMAND, ST, mult * DEMAND, horizon=24, loss_per_hour=LOSS)
        std = (ch * pr).sum() / d + miso_network_cost(ch, idx, d).total_per_mwh
        out[f"std{mult}"] = 100 * (base - std) / base
        if mult == 4.0:
            tm = ((ch * pr).sum() + ch.sum()
                  * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH) + cap) / d
            out["tmep"] = 100 * (base - tm) / base
    return pr.mean(), 100 * (pr < 0).mean(), base, out


def main() -> None:
    print("=" * 74)
    print("FLEXIBILITY VALUE vs INFLEXIBLE ELECTRIFICATION, EVERY YEAR HELD")
    print("=" * 74)

    print("\nSPAIN (EUR/MWh, tariff 6.3TD, 24h visibility)")
    print(f"  {'yr':>5}{'mean':>8}{'<0':>7}{'inflex':>9}{'naive':>9}"
          f"{'aware':>9}{'saving':>9}")
    sp = {}
    for y in years("prices_spain"):
        m, n, b, nv, aw = spain(y)
        sp[y] = 100 * (b - aw) / b
        print(f"  {y:>5}{m:>8.1f}{n:>6.1f}%{b:>9.2f}{nv:>9.2f}{aw:>9.2f}{sp[y]:>8.1f}%")

    print("\nSOUTH AUSTRALIA (AUD/MWh, Sub-Transmission, 6h visibility)")
    print(f"  {'yr':>5}{'mean':>8}{'<0':>7}{'inflex':>9}{'naive':>9}"
          f"{'aware':>9}{'saving':>9}")
    sa_r, en_all = {}, {}
    for y in years("prices_sa"):
        m, n, b, nv, aw, enr = sa(y)
        sa_r[y] = 100 * (b - aw) / b
        en_all[y] = enr
        print(f"  {y:>5}{m:>8.1f}{n:>6.1f}%{b:>9.2f}{nv:>9.2f}{aw:>9.2f}{sa_r[y]:>8.1f}%")

    print("\nMISO (USD/MWh, Schedule 632 + riders, 24h visibility)")
    print(f"  {'yr':>5}{'mean':>8}{'<0':>7}{'inflex':>9}{'std 1.5x':>11}"
          f"{'std 4x':>10}{'TMEP 4x':>10}")
    mi = {}
    for y in years("prices_miso"):
        m, n, b, o = miso(y)
        mi[y] = o
        print(f"  {y:>5}{m:>8.1f}{n:>6.1f}%{b:>9.2f}{o['std1.5']:>+10.1f}%"
              f"{o['std4.0']:>+9.1f}%{o['tmep']:>+9.1f}%")

    print("\n" + "=" * 74)
    print("THE TWO-NETWORKS TEST, EVERY AUSTRALIAN YEAR")
    print("=" * 74)
    print(f"  {'yr':>5}{'SAPN':>8}" + "".join(f"{k.split()[0]:>13}" for k in EN_LOC))
    for y in sorted(en_all):
        print(f"  {y:>5}{sa_r[y]:>+7.1f}%"
              + "".join(f"{en_all[y][k]:>+12.1f}%" for k in EN_LOC))

    print("\n" + "=" * 74)
    print("SUMMARY")
    print("=" * 74)
    for nm, dd in (("Spain", sp), ("South Australia", sa_r)):
        ys = np.array(sorted(dd)); vs = np.array([dd[y] for y in ys])
        print(f"  {nm:<18}{len(ys)} yrs, {vs.min():.1f}-{vs.max():.1f}%, "
              f"trend {np.polyfit(ys, vs, 1)[0]:+.1f} pts/yr")
    ys = sorted(mi)
    print(f"  {'MISO':<18}{len(ys)} yrs. Standard tariff at 4x negative in "
          f"{sum(1 for y in ys if mi[y]['std4.0'] < 0)}/{len(ys)}; "
          f"TMEP positive in {sum(1 for y in ys if mi[y]['tmep'] > 0)}/{len(ys)}")
    n_pos = sum(1 for y in en_all for k in EN_LOC if en_all[y][k] > 0)
    n_tot = len(en_all) * len(EN_LOC)
    print(f"  {'Two networks':<18}SAPN positive in {sum(1 for y in sa_r if sa_r[y] > 0)}"
          f"/{len(sa_r)} years; ElectraNet positive in only {n_pos}/{n_tot} "
          f"year-locations")


if __name__ == "__main__":
    main()
