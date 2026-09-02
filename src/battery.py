"""The charging model: when does a thermal battery buy its power?

A factory needs a fixed amount of heat every hour. A thermal battery can buy
power ahead of time and hold the heat, so it can wait for cheap hours; a normal
factory has to buy as it burns. The difference between the two bills is the
value of flexibility.

The rule is deliberately simple and explainable rather than optimal: walk
forward through the year, and whenever the tank is about to run dry, go back and
buy in the cheapest hour that could still be holding heat now. Three things
limit it — the tank size, the most it can buy in any one hour, and the fact that
it cannot buy power in the past.

That last constraint is what keeps this honest: cheap power on Tuesday afternoon
cannot serve Tuesday morning.

Run this file directly to check the model against a case with a known answer:

    python src/battery.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

EPS = 1e-9


@dataclass(frozen=True)
class Result:
    """What each buyer paid, per unit of heat delivered."""
    flat_cost: float        # a normal factory, buying as it burns
    battery_cost: float     # the thermal battery, buying when cheap
    charge: np.ndarray      # how much the battery bought in each hour
    storage_hours: float

    @property
    def saving_pct(self) -> float:
        """Saving measured against the size of the reference bill, so the sign
        stays right when prices — and therefore the bill — go negative."""
        if abs(self.flat_cost) < 1e-9:
            return 0.0
        return 100.0 * (self.flat_cost - self.battery_cost) / abs(self.flat_cost)


def schedule(prices: np.ndarray, demand: float, storage: float,
             charge_cap: float, horizon: float | None = None) -> np.ndarray:
    """Return how much the battery buys in each hour.

    prices      price per MWh in each hour
    demand      MWh of heat the factory needs every hour
    storage     tank size in MWh
    charge_cap  most the battery can buy in any single hour, in MWh
    horizon     how many hours ahead the operator can see. None means limited
                only by the tank.

    The tank is empty at the start and ends empty, so total purchases equal
    total heat delivered.

    On `horizon`. Deciding to buy at hour j to cover a shortfall at hour h means
    knowing at j what will happen h - j hours later. So the operator's forecast
    horizon and the search window are the same quantity, and capping one caps
    the other. A horizon of 1 is a buyer who cannot see ahead at all and must
    buy as it burns; an uncapped horizon still cannot exceed what the tank can
    carry, because power bought earlier than that has already been burnt.
    """
    n = len(prices)
    charge = np.zeros(n)
    soc = np.zeros(n)  # tank level after each hour's buying and burning

    # Power bought more than this many hours ago has already been burnt, so it
    # cannot help with a shortfall now. Bounding the search this way is what
    # makes a full year tractable — and it is a physical fact, not an
    # approximation.
    lookback = int(math.ceil(storage / demand)) + 2
    if horizon is not None:
        # A horizon of 1 hour means seeing only the hour you are in, which
        # leaves no earlier hour to have bought in: lookback zero.
        lookback = min(lookback, max(0, int(horizon) - 1))

    prev = 0.0
    for h in range(n):
        soc[h] = prev + charge[h] - demand

        while soc[h] < -EPS:
            lo = max(0, h - lookback)

            # Walk backwards from now, tracking the highest the tank gets
            # between a candidate hour and now. Buying at hour j lifts the tank
            # for every hour from j onwards, so that peak is what limits how
            # much more we can take on.
            best_j, best_price, best_room = -1, math.inf, 0.0
            peak = -math.inf
            for j in range(h, lo - 1, -1):
                peak = max(peak, soc[j])
                room = min(charge_cap - charge[j], storage - peak)
                if room > EPS and prices[j] < best_price:
                    best_j, best_price, best_room = j, prices[j], room

            if best_j < 0:
                raise RuntimeError(
                    f"hour {h}: the factory runs short and there is no earlier "
                    f"hour with room to buy. Storage {storage} MWh and charge "
                    f"cap {charge_cap} MWh/h are too small for demand {demand}.")

            bought = min(best_room, -soc[h])
            charge[best_j] += bought
            soc[best_j:h + 1] += bought

        prev = soc[h]

    delivered = n * demand
    if not math.isclose(charge.sum(), delivered, rel_tol=1e-6):
        raise RuntimeError(
            f"energy does not balance: bought {charge.sum():.1f} MWh to deliver "
            f"{delivered:.1f} MWh")

    return charge


def evaluate(prices: np.ndarray, demand: float, storage_hours: float,
             charge_cap_hours: float = 4.0,
             horizon: float | None = None) -> Result:
    """Run both buyers over the same prices and report cost per MWh of heat.

    storage_hours     tank size, expressed in hours of the factory's demand
    charge_cap_hours  most it can buy in one hour, in hours of demand
    horizon           hours of price visibility; None means tank-limited
    """
    prices = np.asarray(prices, dtype=float)
    charge = schedule(prices, demand,
                      storage=storage_hours * demand,
                      charge_cap=charge_cap_hours * demand,
                      horizon=horizon)

    delivered = len(prices) * demand
    return Result(
        flat_cost=float((demand * prices).sum() / delivered),
        battery_cost=float((charge * prices).sum() / delivered),
        charge=charge,
        storage_hours=storage_hours,
    )


# ---------------------------------------------------------------------------
# Check against a case where the answer is already known.
#
# The interactive explainer works a made-up day in four six-hour blocks priced
# 30 / 45 / 0 / 110. With a twelve-hour tank a normal factory pays $46.25 per
# MWh and the battery pays $15.00. If this port is faithful, it reproduces both.
# ---------------------------------------------------------------------------

def _self_test() -> None:
    blocks = [30, 45, 0, 110]
    prices = np.repeat(blocks, 6).astype(float)

    r = evaluate(prices, demand=10, storage_hours=12)
    print("Toy day from the explainer (blocks 30 / 45 / 0 / 110, 12h tank)")
    print(f"  normal factory : ${r.flat_cost:6.2f} / MWh   (expected $46.25)")
    print(f"  thermal battery: ${r.battery_cost:6.2f} / MWh   (expected $15.00)")
    print(f"  saving         : {r.saving_pct:5.1f}%          (expected  68.0%)")

    assert math.isclose(r.flat_cost, 46.25, abs_tol=0.01), r.flat_cost
    assert math.isclose(r.battery_cost, 15.00, abs_tol=0.01), r.battery_cost

    # No tank means no choice about when to buy: it must match a normal factory.
    r0 = evaluate(prices, demand=10, storage_hours=0)
    assert math.isclose(r0.battery_cost, r0.flat_cost, abs_tol=1e-6)
    print(f"\n  zero-tank check: battery ${r0.battery_cost:.2f} == "
          f"flat ${r0.flat_cost:.2f}  (no storage, no advantage)")

    # A flat price gives nothing to wait for, whatever the tank size.
    flat = np.full(240, 50.0)
    rf = evaluate(flat, demand=10, storage_hours=24)
    assert math.isclose(rf.battery_cost, 50.0, abs_tol=1e-6)
    print(f"  flat-price check: battery ${rf.battery_cost:.2f} == "
          f"flat ${rf.flat_cost:.2f}  (nothing to wait for)")

    # A buyer who cannot see ahead has no way to use a tank, so it must pay
    # what a normal factory pays however large the tank is.
    rb = evaluate(prices, demand=10, storage_hours=12, horizon=1)
    assert math.isclose(rb.battery_cost, rb.flat_cost, abs_tol=1e-6)
    print(f"  blind-buyer check: battery ${rb.battery_cost:.2f} == "
          f"flat ${rb.flat_cost:.2f}  (12h tank, no visibility)")

    # More visibility can never be worse than less.
    costs = [evaluate(prices, demand=10, storage_hours=12, horizon=h).battery_cost
             for h in (1, 2, 3, 6, 12, 24)]
    assert all(b <= a + 1e-9 for a, b in zip(costs, costs[1:])), costs
    print(f"  monotonic check: cost falls as visibility grows "
          f"{' -> '.join(f'${c:.0f}' for c in costs)}")

    print("\nAll checks passed.")


if __name__ == "__main__":
    _self_test()
