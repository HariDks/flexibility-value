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

ES_POWER_EUR_KW_YR = {1: 23.669055, 2: 12.513915, 3: 4.696330,
                      4: 3.309245, 5: 0.069965, 6: 0.062286}
ES_ENERGY_EUR_MWH = {p: v * 1000 for p, v in
                     {1: 0.027104, 2: 0.011894, 3: 0.004726,
                      4: 0.002739, 5: 0.000122, 6: 0.000029}.items()}

# Seasons by month, and which three periods a weekday uses in each.
ES_SEASON_PERIODS = {
    "high":   ({1, 2, 7, 12}, (1, 2)),   # peak block -> P1, shoulder -> P2
    "medhigh": ({3, 11},      (2, 3)),
    "medium": ({6, 8, 9},     (3, 4)),
    "low":    ({4, 5, 10},    (4, 5)),
}
ES_PEAK_HOURS = set(range(9, 14)) | set(range(18, 22))   # 09-14 and 18-22
ES_NIGHT_HOURS = set(range(0, 8))                        # always P6

# Cargos (system charges) are not in the peajes resolution. Public sources put
# the 6.1TD energy-side cargos in roughly this band, EUR/MWh, averaged across
# periods. Carried as a sensitivity rather than a point estimate.
CARGOS_RANGE_EUR_MWH = (8.0, 20.0)


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
                       delivered_mwh: float,
                       cargos_eur_mwh: float = 0.0) -> NetworkCost:
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
    energy = sum(draw_mwh[periods == p].sum()
                 * (ES_ENERGY_EUR_MWH[p] + cargos_eur_mwh)
                 for p in range(1, 7))

    return NetworkCost(energy_per_mwh=energy / delivered_mwh,
                       capacity_per_mwh=capacity / delivered_mwh)


# ---------------------------------------------------------------------------
# South Australia and MISO, modelled structurally.
# ---------------------------------------------------------------------------

def anytime_demand_cost(draw_mwh: np.ndarray, delivered_mwh: float,
                        demand_charge_per_kw_yr: float,
                        energy_charge_per_mwh: float,
                        flexible_discount: float = 0.0) -> NetworkCost:
    """A demand tariff charged on the largest draw at any time of year.

    This is South Australia's "Anytime Demand" shape, and it is the harshest
    design for a battery: nothing about *when* the peak happens reduces it.

    `flexible_discount` models SA Power Networks' flexible connections,
    introduced 1 July 2025, which charge flexible demand at half rate.
    """
    peak_mw = float(draw_mwh.max(initial=0.0))
    rate = demand_charge_per_kw_yr * (1.0 - flexible_discount)
    capacity = peak_mw * 1000 * rate
    return NetworkCost(
        energy_per_mwh=energy_charge_per_mwh,
        capacity_per_mwh=capacity / delivered_mwh)
