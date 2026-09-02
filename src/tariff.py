"""Network charges: the part of the bill that is not the price of the power.

Every market charges in two parts, and they behave completely differently:

* an **energy charge** on each MWh delivered, which both buyers pay alike; and
* a **capacity charge** on the power drawn, which a battery pays far more of,
  because it takes the same energy through far fewer hours.

The second is why tariff *design* decides whether flexibility pays, and it is
the reason a bespoke tariff was needed to make Big Stone work.

Spain is modelled from the published rates. South Australia and MISO are
modelled structurally, with rates carried as documented ranges — see
notes/fees.md for sources and confidence.
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
# NOT included: the system charges (cargos), set separately by ministerial
# order, which add materially to the energy side. Modelled as a sensitivity
# instead - see CARGOS_RANGE.
# ---------------------------------------------------------------------------

ES_PEAJES_POWER = {1: 23.669055, 2: 12.513915, 3: 4.696330,
                   4: 3.309245, 5: 0.069965, 6: 0.062286}          # EUR/kW/yr
ES_PEAJES_ENERGY = {1: 0.027104, 2: 0.011894, 3: 0.004726,
                    4: 0.002739, 5: 0.000122, 6: 0.000029}         # EUR/kWh

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

SA_ENERGY_AUD_MWH = 25.00          # $0.0250/kWh
SA_PEAK_AUD_KVA_DAY = 0.1737
SA_ANYTIME_AUD_KVA_DAY = 0.0274
SA_ANYTIME_FLEX_AUD_KVA_DAY = 0.0137
SA_PEAK_WINDOW = range(17, 21)     # 17:00-21:00, outside the CBD


def sa_network_cost(draw_mwh: np.ndarray, index: pd.DatetimeIndex,
                    delivered_mwh: float, flexible: bool = False
                    ) -> NetworkCost:
    """What a buyer pays SA Power Networks for a given hourly draw profile."""
    days = len(np.unique(index.date))
    in_peak = np.isin(index.hour, list(SA_PEAK_WINDOW))

    peak_kva = float(draw_mwh[in_peak].max(initial=0.0)) * 1000
    anytime_kva = float(draw_mwh.max(initial=0.0)) * 1000
    anytime_rate = (SA_ANYTIME_FLEX_AUD_KVA_DAY if flexible
                    else SA_ANYTIME_AUD_KVA_DAY)

    capacity = days * (peak_kva * SA_PEAK_AUD_KVA_DAY
                       + anytime_kva * anytime_rate)
    return NetworkCost(energy_per_mwh=SA_ENERGY_AUD_MWH,
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


def miso_network_cost(draw_mwh: np.ndarray, index: pd.DatetimeIndex,
                      delivered_mwh: float,
                      include_energy: bool = False) -> NetworkCost:
    """What a buyer pays Otter Tail under Schedule 632.

    `include_energy` adds the schedule's own kWh charge. That charge is part of
    a bundled retail rate covering supply as well as delivery, so it is used
    only for the normal factory, which buys its power from the utility. A
    battery buying at MISO hourly prices pays for its energy there instead.
    """
    df = pd.DataFrame({"draw": draw_mwh}, index=index)
    monthly_peak = df.groupby([index.year, index.month])["draw"].max()

    capacity = 0.0
    for (_, month), peak_mw in monthly_peak.items():
        season = "summer" if month in MISO_SUMMER_MONTHS else "winter"
        capacity += peak_mw * 1000 * MISO_DEMAND_USD_KW_MONTH[season]
    capacity += MISO_CUSTOMER_USD_MONTH * len(monthly_peak)

    energy = 0.0
    if include_energy:
        is_summer = np.isin(index.month, list(MISO_SUMMER_MONTHS))
        energy = (draw_mwh[is_summer].sum() * MISO_ENERGY_USD_MWH["summer"]
                  + draw_mwh[~is_summer].sum() * MISO_ENERGY_USD_MWH["winter"])

    return NetworkCost(energy_per_mwh=energy / delivered_mwh,
                       capacity_per_mwh=capacity / delivered_mwh)
