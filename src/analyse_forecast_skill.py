"""How much of the theoretical saving do real AEMO forecasts actually capture?

South Australia's forecast horizon was the largest judgment in this study. The
horizon parameter elsewhere assumes *perfect* prices within a truncated window,
which overstates what a given lead time really delivers — a forecast is not a
price.

This is the honest test: **rank hours using the forecast AEMO actually
published H hours ahead, then pay what the price actually turned out to be.**

Needs `fetch_aemo_predispatch.py` to have been run first.

    python src/analyse_forecast_skill.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (SA_ENERGY_AUD_MWH, SA_PEAK_MONTHS, SA_PEAK_WINDOW,
                    sa_network_cost)

ROOT = Path(__file__).resolve().parents[1]
P, RAW = ROOT / "data" / "processed", ROOT / "data" / "raw" / "aemo"
DEMAND, ST = 10.0, 120.0
HORIZONS = (2, 4, 6, 8, 12)


def main() -> None:
    f = pd.read_csv(P / "sa_predispatch_forecasts.csv", parse_dates=["target"])
    f["target_h"] = f["target"].dt.ceil("h")
    raw = pd.concat([pd.read_csv(x) for x in
                     sorted(RAW.glob("PRICE_AND_DEMAND_2025*_SA1.csv"))],
                    ignore_index=True)
    raw["ts"] = pd.to_datetime(raw["SETTLEMENTDATE"], format="%Y/%m/%d %H:%M:%S")
    act = (raw.set_index("ts")["RRP"]
           .resample("h", label="right", closed="right").mean().dropna())

    fcs = {H: f[(f.horizon_h >= H - 1) & (f.horizon_h < H + 1)]
           .groupby("target_h")["forecast"].mean() for H in HORIZONS}
    common = set.intersection(*[set(s.index) for s in fcs.values()]) & set(act.index)

    ix, blocks, s = pd.DatetimeIndex(sorted(common)), [], 0
    for i in range(1, len(ix) + 1):
        if i == len(ix) or (ix[i] - ix[i - 1]) != pd.Timedelta(1, unit="h"):
            if i - s >= 120:
                blocks.append(ix[s:i])
            s = i

    def evaluate(getsig, hz, avoid_peak=True):
        tb = tc = td = 0.0
        for b in blocks:
            a = act.loc[b].to_numpy()
            d = len(b) * DEMAND
            loc = b.tz_localize("Etc/GMT-10").tz_convert("Australia/Adelaide")
            bl = (np.isin(loc.hour, list(SA_PEAK_WINDOW))
                  & np.isin(loc.month, list(SA_PEAK_MONTHS)))
            cap = (np.where(bl, 0.0, 4 * DEMAND) if avoid_peak
                   else np.full(len(b), 4 * DEMAND))
            flat = np.full(len(b), DEMAND)
            ch = schedule(getsig(b) + SA_ENERGY_AUD_MWH, DEMAND, ST, cap,
                          horizon=hz)
            tb += (flat * a).sum() + sa_network_cost(flat, loc, d).total_per_mwh * d
            tc += (ch * a).sum() + sa_network_cost(ch, loc, d).total_per_mwh * d
            td += d
        return tb / td, tc / td

    print(f"{len(blocks)} contiguous blocks, {sum(len(b) for b in blocks):,} "
          f"hours, September–December 2025")
    print("  " + ", ".join(f"{b[0]:%d %b}–{b[-1]:%d %b}" for b in blocks) + "\n")

    for label, avoid in (("Peak-window avoidance strategy", True),
                         ("Price-following only", False)):
        base, perf = evaluate(lambda b: act.loc[b].to_numpy(), None, avoid)
        ps = 100 * (base - perf) / base
        print(f"{label}\n")
        print(f"  {'basis':<32}{'delivered':>11}{'saving':>9}{'of perfect':>12}")
        print(f"  {'inflexible':<32}{base:>11.2f}{'—':>9}")
        print(f"  {'perfect knowledge':<32}{perf:>11.2f}{ps:>8.1f}%{'—':>12}")
        for H in HORIZONS:
            try:
                _, c = evaluate(lambda b, H=H: fcs[H].loc[b].to_numpy(), H, avoid)
            except RuntimeError:
                print(f"  {f'real forecast, {H}h ahead':<32}"
                      f"{'infeasible — cannot pre-fill':>32}")
                continue
            sv = 100 * (base - c) / base
            print(f"  {f'real forecast, {H}h ahead':<32}{c:>11.2f}{sv:>8.1f}%"
                  f"{sv / ps * 100:>11.0f}%")
        print()

    print("A forecast is not a price. The horizon parameter used elsewhere gives")
    print("the battery perfect prices inside a truncated window, which overstates")
    print("what a given lead time delivers. These capture ratios are the honest")
    print("discount on it.")


if __name__ == "__main__":
    main()
