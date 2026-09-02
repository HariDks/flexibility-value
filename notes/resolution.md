# Time resolution: why hourly, and what it costs

Each market publishes prices at a different granularity:

| Market | Native resolution | Day-ahead market? |
|---|---|---|
| Spain (OMIE) | hourly to 2025-09-30, then 15-minute | **Yes** — price known before you commit |
| South Australia (AEMO) | 5-minute | **No** — real-time spot only |
| MISO (MINN.HUB) | hourly day-ahead | **Yes** |

Everything is aggregated to **hourly local time**. This is a real decision with a
measurable cost, so it is measured rather than asserted.

## The measured effect, South Australia 2025

Running the identical model on hourly averages versus native 5-minute data:

| Tank | Saving, hourly | Saving, 5-minute | Understated by |
|---|---|---|---|
| 4h | 60.1% | 71.9% | 11.8 points |
| 12h | 98.7% | 103.8% | 5.1 points |
| 24h | 112.9% | 116.2% | 3.3 points |

**Averaging never touches the normal factory's bill** — its mean is AUD 86.74
either way, because averaging preserves the mean. It only hurts the battery,
which lives on extremes that averaging buries: the 5-minute series reaches
−AUD 907/MWh, the hourly one only −AUD 314.

So every South Australian figure in this study is a **floor, not a ceiling**. The
bias is largest for small tanks, which depend on catching brief dips.

## Why keep hourly anyway

1. **Comparability.** It is the only granularity all three markets share.
2. **It matches where you can actually commit.** In Spain and MISO the hourly
   day-ahead price is the thing you contract at. Hourly is not an approximation
   there; it is the decision unit.
3. **It errs against the argument.** Understating the battery is the safe
   direction for a study whose conclusion favours flexibility.

## The offsetting bias, and what it implies for Step 5

The 5-minute result assumes the battery knows each five-minute price in advance.
In a market with **no day-ahead stage**, that is a far stronger assumption than
the equivalent in Spain or MISO, where the price genuinely is published ahead of
delivery.

So the two biases point in opposite directions and partly cancel: hourly
averaging understates the opportunity, while hourly granularity implicitly
penalises unrealistic foresight.

**Prediction to test in Step 5:** the cost of having to guess should be
structurally larger in South Australia than in Spain or MISO — not only because
prices swing more, but because the market design gives less warning. If the
foresight gap comes out similar across all three, something is wrong with the
guessing rule.
