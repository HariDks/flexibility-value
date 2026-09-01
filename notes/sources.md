# Sources

Verified during scoping. Anything marked **unverified** still needs checking
before it goes in the memo.

## Antora and the anchor project

- [Otter Tail Power's thermal storage tariff](https://betterenergy.org/blog/otter-tail-power-thermal-storage-tariff-industrial-heat/)
  — Great Plains Institute. The single most important background document: the
  TMEP rider, its eligibility rules, and the Big Stone / POET arrangement.
  **Still to do:** find the primary South Dakota PUC filing behind this.
- [Antora — "Turning sunshine and wind into 24/7 industrial heat"](https://www.antora.com/insights/sunshine-and-wind-2)
  — their economic thesis in their own words. This project is a quantitative test
  of this post.
- [Antora — technology](https://www.antora.com/technology)
- [Antora — $550M Series C](https://www.antora.com/insights/series-c) — note the
  stated focus is US deployment and a second US manufacturing hub.
- [Canary Media on the Big Stone battery](https://www.canarymedia.com/articles/energy-storage/innovation-antora-massive-heat-battery)
- [Energy-Storage.News on the Series C](https://www.energy-storage.news/antora-energy-closes-us550-million-series-c-to-scale-us-thermal-battery-deployment/)
  — also mentions MGA Thermal + Knode's 195 MWh project at Tronox Kwinana, WA.
  Note: Kwinana is in the WEM, a separate market from the NEM.

## Market data

- [`gridstatus`](https://github.com/gridstatus/gridstatus) — Python library for US
  ISO data. MISO and SPP prices.
  [SPP LMP example](https://opensource.gridstatus.io/en/stable/Examples/spp/LMP%20Data.html).
  Note: SPP methods default to hub nodes.
- **AEMO** — Australian regional prices via NEMWeb; OpenNEM is the friendlier
  front door. **Unverified:** exact download path.
- **OMIE** — Spanish/Iberian hourly day-ahead prices. **Unverified:** exact
  download path.
- [AEMO Quarterly Energy Dynamics Q1 2025](https://www.aemo.com.au/-/media/files/major-publications/qed/2025/qed-q1-2025.pdf)
  — useful for vocabulary and for AEMO's own framing of negative prices.

## Market context

- [Fresh Energy — negative prices in MISO](https://fresh-energy.org/negative-prices-in-the-miso-market-whats-happening-and-why-should-we-care)
  — plain-language explainer. Note: historical MISO negative pricing was under ~2%
  of node-hours, far below the Australian figures.
- [Australian Energy Council — a decade of NEM negative prices](https://energycouncil.com.au/negative-prices-and-revenues-in-the-nem-over-the-past-decade/)
- [AEMO — negative electricity demand in South Australia](https://www.aemo.com.au/newsroom/news-updates/negative-electricity-demand-in-south-australia)
- [Modo Energy — Spanish PPAs and negative prices](https://modoenergy.com/research/en/ppa-contracts-spain-negative-prices-settlement-zero-floor-remuneration)
- [Storpeak — curtailment and negative prices in Spain](https://storpeak.com/insights/curtailment-negative-prices-spain/)
- [Grid Status — curtailment explainer](https://blog.gridstatus.io/curtailment/)

## Figures picked up during scoping — all need re-checking before use

| Figure | Source | Confidence |
|---|---|---|
| NEM negative prices 23.1% of intervals, Q4 2024 | AEMO QED | medium |
| South Australia 38% negative — regional record | AEMO QED | medium |
| SA logged 112 hours of negative operational demand in 2025 | AEMO | medium |
| Spain: 500+ negative hours in 2025, ~2× 2024 | press | low |
| Spain: solar capture ~€34/MWh vs wind ~€62/MWh, 2025 | press | low |
| MISO: negative prices <2% of node-hours, 2015–17 | Fresh Energy | medium |

## Policy background (not needed for the model)

- [FERC RM26-4 — large load interconnection](https://www.ferc.gov/rm26-4)
- [Foley Hoag on IRS Notice 2026-15 (45X, material assistance)](https://foleyhoag.com/news-and-insights/blogs/energy-and-climate-counsel/2026/march/new-irs-macr-guidance-what-it-means-for-section-45x-advanced-manufacturing-production-tax-credits/)
  — only relevant if the 45X idea is revived.
