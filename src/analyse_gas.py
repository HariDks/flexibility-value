"""The commercial counterfactual: delivered heat from a thermal battery versus
heat from a gas boiler, with and without a carbon price.

The flat-electric case elsewhere in this project is the *flexibility-value*
counterfactual - it isolates what timing is worth. This file is the *commercial*
counterfactual: what a customer is actually choosing between.

    python src/analyse_gas.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

from battery import schedule
from tariff import (miso_network_cost, sa_network_cost, spain_network_cost,
                    spain_periods, ES_ENERGY_EUR_MWH, SA_ENERGY_AUD_MWH,
                    SA_PEAK_WINDOW, SA_PEAK_MONTHS, MISO_DEMAND_USD_KW_MONTH, MISO_SUMMER_MONTHS,
                    MISO_TCR_DEMAND_USD_KW, MISO_RRCR_DEMAND_USD_KW,
                    MISO_ECO_USD_MWH, MISO_EITE_USD_MWH)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEMAND, STORAGE_H = 10.0, 12

# --- gas, converted to cost of delivered heat -----------------------------
# Boiler efficiency: 85%, a good industrial steam boiler. Being generous to gas
# is the conservative choice here.
BOILER_EFF = 0.85
# Natural gas combustion: ~0.0561 tCO2/GJ -> 0.202 tCO2 per MWh of gas burnt.
GAS_TCO2_PER_MWH = 0.202

GAS = {
    # market: (price per MWh of gas, currency, source note)
    "Spain": (43.20, "EUR", "Eurostat nrg_pc_203 band I4 "
                            "(100,000-999,999 GJ/yr), 2025 average of both "
                            "half-years, excluding VAT"),
    "South Australia": (13.00 / 0.277778, "AUD",
                        "AER STTM quarterly register, Adelaide, mean of the "
                        "four quarters of 2025 (13.51/12.90/12.76/12.82 A$/GJ)"),
    "MISO": (6.63 / (1.037 * 0.293071), "USD", "EIA Minnesota industrial, "
                                               "$6.63/Mcf 2025"),
}
# Carbon price actually faced by an industrial emitter in each market, 2025.
CARBON = {
    "Spain": (75.0, "EU ETS, ~EUR 72-84 through 2025"),
    "South Australia": (36.99, "Safeguard default prescribed unit price 2025-26"),
    "MISO": (0.0, "no carbon price"),
}


def gas_heat_cost(market: str, carbon_price: float | None = None) -> float:
    price, _, _ = GAS[market]
    co2 = carbon_price if carbon_price is not None else CARBON[market][0]
    return (price + co2 * GAS_TCO2_PER_MWH) / BOILER_EFF


def load(stem, col, tz):
    d = pd.read_csv(PROCESSED / f"{stem}_2025.csv")
    d["ts"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert(tz)
    return d.set_index("ts")[col]


def battery_cost(market: str, charge_mult: float, storage_h: float = STORAGE_H,
                 loss_per_day: float = 0.01) -> float:
    """Delivered cost of heat from the battery, on the market's real tariff."""
    loss = 1 - (1 - loss_per_day) ** (1 / 24)
    st = storage_h * DEMAND

    if market == "Spain":
        s = load("prices_spain", "price_eur_mwh", "Europe/Madrid")
        idx, pr = s.index, s.to_numpy()
        per = spain_periods(idx)
        eff = pr + np.array([ES_ENERGY_EUR_MWH[p] for p in per])
        cap = np.where(np.isin(per, (4, 5, 6)), charge_mult, 1) * DEMAND
        ch = schedule(eff, DEMAND, st, cap, horizon=24, loss_per_hour=loss)
        d = len(pr) * DEMAND
        return (ch * pr).sum() / d + spain_network_cost(ch, idx, d).total_per_mwh

    if market == "South Australia":
        s = load("prices_sa", "price_aud_mwh", "Australia/Adelaide")
        idx, pr = s.index, s.to_numpy()
        blocked = (np.isin(idx.hour, list(SA_PEAK_WINDOW))
                   & np.isin(idx.month, list(SA_PEAK_MONTHS)))
        cap = np.where(blocked, 0.0, charge_mult * DEMAND)
        ch = schedule(pr + SA_ENERGY_AUD_MWH, DEMAND, st, cap, horizon=6,
                      loss_per_hour=loss)
        d = len(pr) * DEMAND
        return (ch * pr).sum() / d + sa_network_cost(ch, idx, d).total_per_mwh

    # MISO under TMEP: demand billed on Baseline Demand, not metered peak.
    s = load("prices_miso", "price_usd_mwh", "US/Central")
    idx, pr = s.index, s.to_numpy()
    ch = schedule(pr, DEMAND, st, charge_mult * DEMAND, horizon=24,
                  loss_per_hour=loss)
    d = len(pr) * DEMAND
    cap = 282.00 * 12
    for m in range(1, 13):
        rate = MISO_DEMAND_USD_KW_MONTH["summer" if m in MISO_SUMMER_MONTHS
                                        else "winter"]
        rate += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[
            "h1" if m <= 6 else "h2"]
        cap += DEMAND * 1000 * rate            # baseline demand, not peak
    energy = (ch * pr).sum() + ch.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)
    return (energy + cap) / d


def main() -> None:
    markets = ["Spain", "South Australia", "MISO"]

    print("Cost of delivered heat: thermal battery vs gas boiler, 2025\n")
    print("Gas is converted at 85% boiler efficiency and includes the carbon")
    print("price an industrial emitter actually faces.\n")

    print(f"  {'':<18}{'gas, no':>10}{'carbon':>9}{'gas, with':>11}"
          f"{'battery':>10}{'battery vs':>12}")
    print(f"  {'':<18}{'carbon':>10}{'adder':>9}{'carbon':>11}{'(4x)':>10}"
          f"{'gas+carbon':>12}")
    rows = []
    for m in markets:
        cur = GAS[m][1]
        bare = gas_heat_cost(m, carbon_price=0.0)
        full = gas_heat_cost(m)
        bat = battery_cost(m, 4.0)
        rows.append((m, cur, bare, full, bat))
        print(f"  {m:<18}{bare:>10.2f}{full - bare:>9.2f}{full:>11.2f}"
              f"{bat:>10.2f}{100 * (full - bat) / full:>11.1f}%")

    print(f"\n  Against gas with NO carbon price at all "
          f"(positive = battery is cheaper):")
    for m, cur, bare, full, bat in rows:
        print(f"    {m:<18}{100 * (bare - bat) / bare:>7.1f}%")

    # --- sensitivity grid --------------------------------------------------
    print(f"\n\nBattery cost of heat by charge rate and storage duration")
    print(f"  (1%/day standby loss; market's own tariff)\n")
    for m in markets:
        cur = GAS[m][1]
        print(f"  {m} ({cur}/MWh) — gas with carbon "
              f"{gas_heat_cost(m):.2f}, without {gas_heat_cost(m, 0.0):.2f}")
        print(f"    {'charge':>8}" + "".join(f"{f'{h}h':>9}" for h in (6, 12, 24, 48)))
        for mult in (2.0, 4.0, 6.0):
            row = f"    {f'{mult:.0f}x':>8}"
            for h in (6, 12, 24, 48):
                try:
                    row += f"{battery_cost(m, mult, h):>9.2f}"
                except RuntimeError:
                    row += f"{'n/a':>9}"
            print(row)
        print()

    # --- what carbon price would it take? ----------------------------------
    print("Carbon price at which the battery matches gas (4x, 12h):\n")
    for m in markets:
        cur = GAS[m][1]
        bat = battery_cost(m, 4.0)
        gas_bare = GAS[m][0]
        # (gas + c*factor)/eff = bat  ->  c = (bat*eff - gas)/factor
        c = (bat * BOILER_EFF - gas_bare) / GAS_TCO2_PER_MWH
        actual = CARBON[m][0]
        verdict = "already above" if actual >= c else "below"
        print(f"  {m:<18} breakeven {cur} {c:>7.2f}/t   "
              f"actual {actual:>6.2f}   ({verdict})")


if __name__ == "__main__":
    main()
