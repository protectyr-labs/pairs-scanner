#!/usr/bin/env python3
"""
Demo: analyze a synthetic cointegrated pair.

Generates two series that share a common stochastic trend (cointegrated),
runs the full Engle-Granger analysis, and prints a formatted results table.
"""

import numpy as np
from pairs_scanner import analyze_pair, scan_pairs


def generate_cointegrated_pair(n: int = 500, seed: int = 42):
    """Create two synthetic cointegrated price series."""
    rng = np.random.default_rng(seed)
    # Shared random walk (the cointegrating factor)
    trend = np.cumsum(rng.normal(0, 1, n))
    series_a = trend + rng.normal(0, 0.5, n) + 100
    series_b = 0.8 * trend + rng.normal(0, 0.5, n) + 80
    return series_a, series_b


def print_result(result):
    """Pretty-print a PairAnalysis result."""
    print("=" * 60)
    print(f"  Pair: {result.series_a} / {result.series_b}")
    print("=" * 60)
    print(f"  Correlation:        {result.correlation:>10.4f}")
    print(f"  Hedge Ratio:        {result.hedge_ratio:>10.4f}")
    print(f"  Half-Life (days):   {result.half_life_days:>10.1f}")
    print(f"  Hurst Exponent:     {result.hurst_exponent:>10.4f}")
    print(f"  Mean-Reverting:     {str(result.is_mean_reverting):>10}")
    print(f"  ADF Statistic:      {result.adf_statistic:>10.4f}")
    print(f"  ADF p-value:        {result.adf_pvalue:>10.4f}")
    print(f"  Cointegrated:       {str(result.is_cointegrated):>10}")
    print(f"  Spread Z-Score:     {result.spread_zscore:>10.4f}")
    print(f"  Signal:             {result.signal:>10}")
    print(f"  Quality Score:      {result.quality_score:>10.1f}")
    print(f"  Tradeable:          {str(result.tradeable):>10}")
    print("=" * 60)


def main():
    print("\n--- Single Pair Analysis ---\n")
    a, b = generate_cointegrated_pair()
    result = analyze_pair(a, b, name_a="SyntheticA", name_b="SyntheticB")
    print_result(result)

    # Multi-pair scan
    print("\n--- Multi-Pair Scan ---\n")
    rng = np.random.default_rng(99)
    unrelated = np.cumsum(rng.normal(0, 1, 500)) + 90

    data = {
        "SyntheticA": a,
        "SyntheticB": b,
        "Unrelated": unrelated,
    }
    pairs = [("SyntheticA", "SyntheticB"), ("SyntheticA", "Unrelated")]
    results = scan_pairs(data, pairs)

    for r in results:
        tag = "TRADEABLE" if r.tradeable else "---"
        print(
            f"  {r.series_a:>12} / {r.series_b:<12}  "
            f"Q={r.quality_score:5.1f}  signal={r.signal:<14}  [{tag}]"
        )

    print()


if __name__ == "__main__":
    main()
