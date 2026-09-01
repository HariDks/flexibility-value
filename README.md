# flexibility-value

What is a thermal battery's ability to wait for cheap electricity actually worth —
and how much of that value do network fees take back?

A charging-cost study across three electricity markets: **Spain**, **South
Australia**, and the **US Midwest (MISO)**.

**Read [`PROJECT_PLAN.md`](PROJECT_PLAN.md) first.** It holds the scope, the
locked decisions, and the list of things deliberately not being done.

## The idea

A factory needs heat around the clock. A normal factory buys electricity as it
burns it and pays roughly the average price. A thermal battery stores heat, so it
can buy only during the cheap hours. The difference between those two bills is the
value of flexibility.

Network fees are charged per unit delivered regardless of when it was bought, so
they compress that advantage — by different amounts in different countries. That
compression is the finding.

## Layout

```
data/raw/         downloaded price files (not committed)
data/processed/   tidy price table (not committed)
src/              data pulls, the charging model, analysis
notes/            fee research, sources, working notes
output/figures/   charts
explainer/        interactive explainer of the mechanism
```

## Setup

```bash
cd ~/projects/flexibility-value
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Status

Step 0 — scaffolding done. Next: Step 1, download and look at Spanish prices.
