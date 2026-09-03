"""Network charges: the part of the bill that is not the price of the power.

Every market charges in two parts, and they behave completely differently:

* an **energy charge** on each MWh delivered, which both buyers pay alike; and
* a **capacity charge** on the power drawn, which a battery pays far more of,
  because it takes the same energy through far fewer hours.

The second is why tariff *design* decides whether flexibility pays, and it is
the reason a bespoke tariff was needed to make Big Stone work.

All three markets are modelled from published rates — see notes/fees.md for
the source of every figure.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Spain: tariff 6.1TD
#
# Six periods, applied to both the power term (EUR/kW/year) and the energy term
# (EUR/kWh). Rates below are the 2025 access tolls (peajes), transport plus
# distribution, from CNMC's resolution of 4 December 2024, BOE-A-2024-26218.
#
# ---------------------------------------------------------------------------

# Access tolls by tariff class, 2025, transport plus distribution.
#
# Class follows connection voltage. Spanish regulation defines the voltage
# bands (1-30 kV is third category, 30-66 kV second), and larger connections
# take higher voltages - but the megawatt threshold at each level is set by the
# distributor's own connection study, not by a citable universal table. So the
# class a 40-60 MW load would take is NOT asserted here.
#
# Instead the study runs all four and reports the range. It does not need the
# question settled: the saving is 36.4% on 6.1TD and 38.8% on 6.4TD, so no
# choice of class can overturn the conclusion, and 6.1TD is the conservative
# floor. See analyse_robustness.py check 2.
ES_CLASSES = {
    "6.1TD": {"voltage": "1-30 kV",
              "power": {1: 23.669055, 2: 12.513915, 3: 4.696330,
                        4: 3.309245, 5: 0.069965, 6: 0.062286},
              "energy": {1: 0.027104, 2: 0.011894, 3: 0.004726,
                         4: 0.002739, 5: 0.000122, 6: 0.000029}},
    "6.2TD": {"voltage": "30-45 kV",
              "power": {1: 16.620368, 2: 9.426053, 3: 2.481516,
                        4: 1.512028, 5: 0.059278, 6: 0.052654},
              "energy": {1: 0.014770, 2: 0.006840, 3: 0.002279,
                         4: 0.001219, 5: 0.000063, 6: 0.000020}},
    "6.3TD": {"voltage": "30-72.5 kV",
              "power": {1: 10.791377, 2: 6.502236, 3: 2.118318,
                        4: 1.380541, 5: 0.045332, 6: 0.039905},
              "energy": {1: 0.012294, 2: 0.005470, 3: 0.001931,
                         4: 0.001063, 5: 0.000055, 6: 0.000015}},
    "6.4TD": {"voltage": ">72.5 kV",
              "power": {1: 6.590215, 2: 3.939980, 3: 0.956817,
                        4: 0.665081, 5: 0.019779, 6: 0.013181},
              "energy": {1: 0.007944, 2: 0.003569, 3: 0.001288,
                         4: 0.000681, 5: 0.000036, 6: 0.000004}},
}
# Base case: 6.3TD (30-72.5 kV), a mid-range choice. The floor is 6.1TD.
ES_DEFAULT_CLASS = "6.3TD"
ES_PEAJES_POWER = ES_CLASSES[ES_DEFAULT_CLASS]["power"]            # EUR/kW/yr
ES_PEAJES_ENERGY = ES_CLASSES[ES_DEFAULT_CLASS]["energy"]          # EUR/kWh

# System charges (cargos) for 2025, tariff segment 6, from Orden TED/1487/2024
# of 26 December 2024, BOE-A-2024-27289. These fund regulated system costs
# rather than the wires. For high-voltage industry they are small - Spain keeps
# them deliberately low at this voltage - and much smaller than the peajes.
ES_CARGOS_POWER = {1: 1.178247, 2: 0.589615, 3: 0.428453,
                   4: 0.428453, 5: 0.428453, 6: 0.196374}          # EUR/kW/yr
ES_CARGOS_ENERGY = {1: 0.002582, 2: 0.001913, 3: 0.001033,
                    4: 0.000516, 5: 0.000331, 6: 0.000207}         # EUR/kWh

# What a consumer actually pays: tolls plus charges, per period.
ES_POWER_EUR_KW_YR = {p: ES_PEAJES_POWER[p] + ES_CARGOS_POWER[p]
                      for p in range(1, 7)}
ES_ENERGY_EUR_MWH = {p: (ES_PEAJES_ENERGY[p] + ES_CARGOS_ENERGY[p]) * 1000
                     for p in range(1, 7)}

# Seasons by month, and which three periods a weekday uses in each.
ES_SEASON_PERIODS = {
    "high":   ({1, 2, 7, 12}, (1, 2)),   # peak block -> P1, shoulder -> P2
    "medhigh": ({3, 11},      (2, 3)),
    "medium": ({6, 8, 9},     (3, 4)),
    "low":    ({4, 5, 10},    (4, 5)),
}
ES_PEAK_HOURS = set(range(9, 14)) | set(range(18, 22))   # 09-14 and 18-22
ES_NIGHT_HOURS = set(range(0, 8))                        # always P6



def spain_periods(index: pd.DatetimeIndex) -> np.ndarray:
    """Map each hour to its 6.1TD period, 1-6.

    Weekends are P6 for all 24 hours. National holidays are also P6 in the real
    tariff; they are not applied here, which slightly overstates the charge.
    """
    periods = np.full(len(index), 6, dtype=int)
    weekday = index.dayofweek < 5
    hour, month = index.hour, index.month

    for _, (months, (peak_p, shoulder_p)) in ES_SEASON_PERIODS.items():
        in_season = np.isin(month, list(months))
        is_peak = np.isin(hour, list(ES_PEAK_HOURS))
        is_night = np.isin(hour, list(ES_NIGHT_HOURS))
        periods = np.where(in_season & weekday & is_peak, peak_p, periods)
        periods = np.where(in_season & weekday & ~is_peak & ~is_night,
                           shoulder_p, periods)
    return periods


@dataclass(frozen=True)
class NetworkCost:
    energy_per_mwh: float     # charge on each MWh delivered
    capacity_per_mwh: float   # capacity charge, spread over the heat delivered

    @property
    def total_per_mwh(self) -> float:
        return self.energy_per_mwh + self.capacity_per_mwh


def spain_network_cost(draw_mwh: np.ndarray, index: pd.DatetimeIndex,
                       delivered_mwh: float) -> NetworkCost:
    """What a buyer pays Spain's network for a given hourly draw profile.

    Contracted power is billed per period, and must be non-decreasing from P1 to
    P6 - so contracting more in the cheap late periods is explicitly allowed.
    A buyer contracts, in each period, the most it ever draws in that period.
    """
    periods = spain_periods(index)

    # Most drawn in each period, then enforce P1 <= P2 <= ... <= P6.
    peak = {p: float(draw_mwh[periods == p].max(initial=0.0)) for p in range(1, 7)}
    running = 0.0
    contracted = {}
    for p in range(1, 7):
        running = max(running, peak[p])
        contracted[p] = running

    capacity = sum(contracted[p] * 1000 * ES_POWER_EUR_KW_YR[p]
                   for p in range(1, 7))
    energy = sum(draw_mwh[periods == p].sum() * ES_ENERGY_EUR_MWH[p]
                 for p in range(1, 7))

    return NetworkCost(energy_per_mwh=energy / delivered_mwh,
                       capacity_per_mwh=capacity / delivered_mwh)


# ---------------------------------------------------------------------------
# South Australia and MISO, modelled structurally.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# South Australia: SA Power Networks, Sub Transmission tariff (STR)
#
# The right class for a 40-60 MW load. Rates from SA Power Networks' NUoS
# Tariff Price List, Table 1, effective 1 July 2026. Two demand components:
#
#   Peak Demand    charged on the largest draw inside the peak window only,
#                  which outside the Adelaide CBD is 17:00-21:00, every day
#   Anytime Demand charged on the largest draw at any hour of the year
#
# The "Flexible" variant (STRF) charges Anytime Demand at half rate for
# controllable load - a reform introduced 1 July 2025.
# ---------------------------------------------------------------------------

SA_PEAK_WINDOW = range(17, 21)      # 17:00-21:00, outside the Adelaide CBD
SA_PEAK_MONTHS = {11, 12, 1, 2, 3}  # Peak Demand is measured Nov-Mar only

# SA Power Networks publishes only the current year's price list, so the
# 2025-26 schedule covering our data year is not retrievable. Both published
# years that bracket it are carried instead, and results are reported as the
# range between them. Note the tariff code changed from STN to STR.
SA_RATES = {
    "2024-25": {"code": "STN", "energy_mwh": 15.30,     # $0.0153/kWh
                "peak": 0.1584, "anytime": 0.0449, "anytime_flex": 0.0225},
    "2026-27": {"code": "STR", "energy_mwh": 25.00,     # $0.0250/kWh
                "peak": 0.1737, "anytime": 0.0274, "anytime_flex": 0.0137},
}
SA_ENERGY_AUD_MWH = SA_RATES["2026-27"]["energy_mwh"]   # back-compat default


def sa_network_cost(draw_mwh: np.ndarray, index: pd.DatetimeIndex,
                    delivered_mwh: float, flexible: bool = False,
                    vintage: str = "2026-27") -> NetworkCost:
    """What a buyer pays SA Power Networks for a given hourly draw profile.

    Per SA Power Networks' large-business tariff definitions:

      Peak Demand     the highest *daily average* demand inside the window,
                      measured **November to March only**, though billed all
                      year round. Outside the Adelaide CBD the window is
                      17:00-21:00.
      Anytime Demand  the highest interval at any time in the last 12 months.
    """
    r = SA_RATES[vintage]
    days = len(np.unique(index.date))

    in_window = (np.isin(index.hour, list(SA_PEAK_WINDOW))
                 & np.isin(index.month, list(SA_PEAK_MONTHS)))
    if in_window.any():
        daily_mean = (pd.Series(draw_mwh[in_window], index=index[in_window])
                      .groupby(index[in_window].date).mean())
        peak_kva = float(daily_mean.max()) * 1000 if len(daily_mean) else 0.0
    else:
        peak_kva = 0.0

    anytime_kva = float(draw_mwh.max(initial=0.0)) * 1000
    anytime_rate = r["anytime_flex"] if flexible else r["anytime"]

    capacity = days * (peak_kva * r["peak"] + anytime_kva * anytime_rate)
    return NetworkCost(energy_per_mwh=r["energy_mwh"],
                       capacity_per_mwh=capacity / delivered_mwh)


# ---------------------------------------------------------------------------
# MISO: Otter Tail Power, Minnesota Schedule 632 - Transmission Service
#
# The right class for a load of this size. Rates from Otter Tail's published
# Minnesota commercial rate summary. Billing demand is the customer's maximum
# in each calendar month - no time-of-day structure at all, so nothing about
# *when* a peak occurs reduces it.
#
# Excludes sales tax, fuel adjustments and riders, which Otter Tail states are
# not in these tables.
# ---------------------------------------------------------------------------

MISO_DEMAND_USD_KW_MONTH = {"summer": 12.74, "winter": 9.97}   # Jun-Sep / Oct-May
MISO_ENERGY_USD_MWH = {"summer": 20.10, "winter": 22.00}
MISO_CUSTOMER_USD_MONTH = 253.00
MISO_SUMMER_MONTHS = {6, 7, 8, 9}

# The rate summary excludes the Energy Adjustment and the riders, and Otter Tail
# says so. Both are published separately and both are large enough to matter.
#
# Energy Adjustment Factor, Large General Service Non Time of Day, 2025, USD/MWh.
# This is the fuel and purchased-energy pass-through, so a customer buying its
# own energy at MISO prices does not pay it.
MISO_EAF_USD_MWH_2025 = {1: 18.30, 2: 19.46, 3: 13.85, 4: 15.28, 5: 14.22,
                         6: 11.08, 7: 18.44, 8: 19.58, 9: 17.00, 10: 16.57,
                         11: 18.76, 12: 23.74}

# Volumetric riders. These are public-policy surcharges on delivered energy, so
# they apply however the energy was procured.
MISO_ECO_USD_MWH = 5.78          # Energy Conservation & Optimisation, LGS
MISO_EITE_USD_MWH = 0.45         # Energy-Intensive Trade-Exposed surcharge
# Renewable Resource Cost Recovery: an energy component that flipped to a small
# credit mid-year, and a demand component. Supply-side, so battery-exempt.
MISO_RRCR_ENERGY_USD_MWH = {"h1": 2.28, "h2": -0.24}   # to 30 Jun / from 1 Jul
MISO_RRCR_DEMAND_USD_KW = {"h1": 0.413, "h2": 0.038}
MISO_TCR_DEMAND_USD_KW = 1.03    # Transmission Cost Recovery, Apr 24 - Dec 25


def miso_network_cost(draw_mwh: np.ndarray, index: pd.DatetimeIndex,
                      delivered_mwh: float,
                      utility_supplied: bool = False,
                      riders: bool = True) -> NetworkCost:
    """What a buyer pays Otter Tail under Schedule 632.

    `utility_supplied` is True for the inflexible counterfactual, which buys its power
    from Otter Tail: it then pays the schedule's own kWh charge, the Energy
    Adjustment that trues that up to actual fuel and purchased-energy cost, and
    the supply-side Renewable Resource rider. A battery buying at MISO hourly
    prices pays for its energy there instead and none of those apply.

    Both buyers pay the demand charge, the demand-side riders, and the
    volumetric public-policy riders, which fall on delivered energy however it
    was procured.
    """
    df = pd.DataFrame({"draw": draw_mwh}, index=index)
    monthly_peak = df.groupby([index.year, index.month])["draw"].max()

    capacity = MISO_CUSTOMER_USD_MONTH * len(monthly_peak)
    for (_, month), peak_mw in monthly_peak.items():
        season = "summer" if month in MISO_SUMMER_MONTHS else "winter"
        rate = MISO_DEMAND_USD_KW_MONTH[season]
        if riders:
            half = "h1" if month <= 6 else "h2"
            rate += MISO_TCR_DEMAND_USD_KW + MISO_RRCR_DEMAND_USD_KW[half]
        capacity += peak_mw * 1000 * rate

    energy = 0.0
    if riders:
        energy += draw_mwh.sum() * (MISO_ECO_USD_MWH + MISO_EITE_USD_MWH)

    if utility_supplied:
        is_summer = np.isin(index.month, list(MISO_SUMMER_MONTHS))
        energy += (draw_mwh[is_summer].sum() * MISO_ENERGY_USD_MWH["summer"]
                   + draw_mwh[~is_summer].sum() * MISO_ENERGY_USD_MWH["winter"])
        energy += sum(draw_mwh[index.month == m].sum() * MISO_EAF_USD_MWH_2025[m]
                      for m in range(1, 13))
        if riders:
            h1 = index.month <= 6
            energy += (draw_mwh[h1].sum() * MISO_RRCR_ENERGY_USD_MWH["h1"]
                       + draw_mwh[~h1].sum() * MISO_RRCR_ENERGY_USD_MWH["h2"])

    return NetworkCost(energy_per_mwh=energy / delivered_mwh,
                       capacity_per_mwh=capacity / delivered_mwh)
