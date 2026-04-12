# pairs-scanner

Statistical arbitrage pairs scanner. Finds cointegrated pairs using Engle-Granger cointegration, Hurst exponent, and half-life of mean reversion.

## Why This Exists

Correlation is not cointegration. Two series can be highly correlated yet completely unsuitable for pairs trading. This package applies rigorous econometric tests to distinguish genuine mean-reverting spreads from spurious relationships:

- **ADF test** confirms the spread is stationary (not a random walk).
- **Hurst exponent** detects mean-reversion that ADF may miss at marginal significance.
- **Half-life** tells you how long a trade takes to converge.
- **Quality score** combines all signals into a single tradability metric.

## Quick Start

```bash
pip install pairs-scanner

# With full ADF implementation (recommended):
pip install "pairs-scanner[full]"
```

```python
import numpy as np
from pairs_scanner import analyze_pair

# Your two price series (numpy arrays, same length)
series_a = np.array([...])
series_b = np.array([...])

result = analyze_pair(series_a, series_b, "SeriesA", "SeriesB")

print(f"Cointegrated: {result.is_cointegrated}")
print(f"Mean-reverting: {result.is_mean_reverting}")
print(f"Half-life: {result.half_life_days:.1f} days")
print(f"Signal: {result.signal}")
print(f"Quality: {result.quality_score}/100")
print(f"Tradeable: {result.tradeable}")
```

## Demo

```bash
python examples/demo.py
```

```
--- Single Pair Analysis ---

============================================================
  Pair: SyntheticA / SyntheticB
============================================================
  Correlation:            0.9932
  Hedge Ratio:            1.2387
  Half-Life (days):         3.2
  Hurst Exponent:         0.0532
  Mean-Reverting:           True
  ADF Statistic:         -12.4051
  ADF p-value:            0.0000
  Cointegrated:             True
  Spread Z-Score:         0.3817
  Signal:               NEUTRAL
  Quality Score:           90.0
  Tradeable:                True
============================================================
```

## API Reference

### `analyze_pair(series_a, series_b, name_a, name_b, zscore_entry, zscore_exit)`

Full cointegration analysis of a pair. Returns a `PairAnalysis` dataclass.

**Parameters:**
- `series_a`, `series_b` — Price arrays (numpy, same length).
- `name_a`, `name_b` — Labels (default `"A"`, `"B"`).
- `zscore_entry` — Z-score threshold for entry signals (default `2.0`).
- `zscore_exit` — Z-score threshold for neutral zone (default `0.5`).

### `scan_pairs(data, pairs, min_quality)`

Batch-scan multiple pairs. Returns a list of `PairAnalysis` sorted by quality score.

**Parameters:**
- `data` — Dict mapping names to price arrays.
- `pairs` — List of `(name_a, name_b)` tuples.
- `min_quality` — Minimum quality score to include (default `0.0`).

### `adf_test(series)`

Augmented Dickey-Fuller test. Returns `(statistic, p_value)`. Uses `statsmodels` if installed, otherwise a simplified fallback.

### `hurst_exponent(series)`

Hurst exponent via variance of lagged differences. Returns a float in `[0, 1]`.

### `compute_spread(series_a, series_b)`

OLS hedge ratio and spread construction. Returns `(spread, hedge_ratio, half_life)`.

### `PairAnalysis` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `series_a` | `str` | Label for series A |
| `series_b` | `str` | Label for series B |
| `correlation` | `float` | Pearson correlation |
| `hedge_ratio` | `float` | OLS beta (A = beta * B + e) |
| `half_life_days` | `float` | Mean-reversion half-life |
| `hurst_exponent` | `float` | H < 0.5 = mean-reverting |
| `is_mean_reverting` | `bool` | True if H < 0.5 |
| `adf_statistic` | `float` | ADF test statistic |
| `adf_pvalue` | `float` | ADF p-value |
| `is_cointegrated` | `bool` | True if p < 0.05 |
| `spread_zscore` | `float` | Current z-score of spread |
| `signal` | `str` | `LONG_SPREAD`, `SHORT_SPREAD`, or `NEUTRAL` |
| `quality_score` | `float` | Composite score 0-100 |
| `tradeable` | `bool` | True if quality >= 70 |

## What the Metrics Mean

### Hurst Exponent (H)

Measures the tendency of a time series to revert to the mean or trend persistently.

- **H < 0.5** — Mean-reverting. The spread tends to return to its average. This is what you want for pairs trading.
- **H = 0.5** — Random walk. No exploitable pattern.
- **H > 0.5** — Trending. The spread drifts away. Dangerous for mean-reversion strategies.

### Half-Life of Mean Reversion

How many periods (days, bars) it takes for the spread to revert halfway to its mean. Estimated from an Ornstein-Uhlenbeck model fit to the spread.

- **1-5 days** — Fast reversion. Good for short-term strategies.
- **5-30 days** — Moderate. Standard pairs trading horizon.
- **30-60 days** — Slow. Requires patience and capital.
- **> 60 days** — Too slow for most practical strategies.

### Z-Score

How many standard deviations the current spread is from its historical mean.

- **|z| > 2.0** — Entry signal (spread is stretched, expect reversion).
- **|z| < 0.5** — Exit signal (spread has reverted).
- **z > 2.0** — SHORT the spread (sell A, buy B in hedge ratio).
- **z < -2.0** — LONG the spread (buy A, sell B in hedge ratio).

### Quality Score

A composite metric (0-100) combining:

| Component | Points | Condition |
|-----------|--------|-----------|
| Cointegrated | 30 | ADF p-value < 0.05 |
| Mean-reverting | 25 | Hurst < 0.5 |
| Reasonable half-life | 20 | 1 < half-life < 60 days |
| High correlation | 15 | |corr| > 0.7 |
| Near entry signal | 10 | |z-score| > 1.5 |

A score of 70+ is considered tradeable.

## Use Cases

- **Equities** — Pairs within the same sector sharing fundamental drivers.
- **Crypto** — Related tokens or exchange-listed vs. DeFi versions.
- **Commodities** — Related commodities (e.g., heating oil vs. crude oil).
- **ETFs** — Regional or thematic ETFs tracking overlapping baskets.
- **Any two correlated time series** — The math works on any numerical data.

## Requirements

- Python >= 3.9
- numpy >= 1.20
- Optional: statsmodels >= 0.13 (for production-grade ADF test)

## License

MIT
