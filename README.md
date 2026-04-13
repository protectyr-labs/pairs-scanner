# pairs-scanner

> Find cointegrated pairs for statistical arbitrage.

[![CI](https://github.com/protectyr-labs/pairs-scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/protectyr-labs/pairs-scanner/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg)](https://python.org)

## Quick Start

```bash
pip install pairs-scanner            # fallback ADF
pip install "pairs-scanner[full]"    # statsmodels ADF (recommended)
```

```python
import numpy as np
from pairs_scanner import analyze_pair

# Two price series
np.random.seed(42)
base = np.cumsum(np.random.randn(500)) + 100
series_a = base + np.random.randn(500) * 0.5
series_b = base * 1.2 + np.random.randn(500) * 0.5

result = analyze_pair(series_a, series_b, "ETF_A", "ETF_B")
print(f"Quality: {result.quality_score}/100")  # composite tradability score
print(f"Signal:  {result.signal}")             # LONG_SPREAD / SHORT_SPREAD / NEUTRAL
print(f"Tradeable: {result.tradeable}")        # True if quality >= 70
```

## Why This?

- **Rigorous econometrics** -- Engle-Granger cointegration, not just correlation
- **Composite quality score (0-100)** -- combines ADF, Hurst, half-life, correlation, z-score
- **Optional statsmodels** -- uses full ADF when available, simplified fallback when not
- **Batch scanning** -- `scan_pairs(data, pairs, min_quality)` for portfolio-wide screening
- **Actionable signals** -- `LONG_SPREAD`, `SHORT_SPREAD`, or `NEUTRAL` with configurable thresholds

## What the Metrics Mean

| Metric | What It Tells You |
|--------|-------------------|
| **ADF test** (p < 0.05) | Spread is stationary, not a random walk |
| **Hurst exponent** (H < 0.5) | Mean-reverting; H > 0.5 = trending (dangerous) |
| **Half-life** | Days for spread to revert halfway; 1-30 = practical |
| **Z-score** | Standard deviations from mean; |z| > 2 = entry signal |
| **Quality score** | Weighted composite: ADF(30) + Hurst(25) + half-life(20) + corr(15) + signal(10) |

## API

| Function | Purpose |
|----------|---------|
| `analyze_pair(a, b, name_a, name_b, zscore_entry, zscore_exit)` | Full analysis returning `PairAnalysis` |
| `scan_pairs(data, pairs, min_quality)` | Batch scan, sorted by quality score |
| `adf_test(series)` | `(statistic, p_value)` -- statsmodels or fallback |
| `hurst_exponent(series)` | Float in [0, 1] |
| `compute_spread(a, b)` | `(spread, hedge_ratio, half_life)` via OLS |

### PairAnalysis Fields

`correlation`, `hedge_ratio`, `half_life_days`, `hurst_exponent`, `is_mean_reverting`, `adf_statistic`, `adf_pvalue`, `is_cointegrated`, `spread_zscore`, `signal`, `quality_score`, `tradeable`

## Limitations

- **Assumes linear cointegration** -- non-linear relationships are not detected
- **No regime change detection** -- a pair that was cointegrated may stop being so
- **No transaction costs** -- quality score does not factor in fees or slippage
- **Lookback-dependent** -- results change with different history lengths

## License

MIT
