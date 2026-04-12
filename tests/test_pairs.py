import numpy as np
import pytest
from pairs_scanner import (
    adf_test,
    hurst_exponent,
    compute_spread,
    analyze_pair,
    scan_pairs,
    PairAnalysis,
)


def make_mean_reverting(n=500, seed=42):
    """Generate a synthetic mean-reverting series."""
    rng = np.random.default_rng(seed)
    series = np.zeros(n)
    for i in range(1, n):
        series[i] = 0.7 * series[i - 1] + rng.normal(0, 1)  # AR(1) with phi < 1
    return series + 100  # offset to make positive


def make_cointegrated_pair(n=500, seed=42):
    """Generate two cointegrated series."""
    rng = np.random.default_rng(seed)
    # Common stochastic trend
    trend = np.cumsum(rng.normal(0, 1, n))
    a = trend + rng.normal(0, 0.5, n) + 100
    b = 0.8 * trend + rng.normal(0, 0.5, n) + 80
    return a, b


def test_adf_test_stationary():
    series = make_mean_reverting()
    stat, pval = adf_test(series)
    assert pval < 0.05  # should reject null (is stationary)


def test_adf_test_nonstationary():
    # Random walk (non-stationary)
    rng = np.random.default_rng(42)
    series = np.cumsum(rng.normal(0, 1, 500)) + 100
    stat, pval = adf_test(series)
    assert pval > 0.05  # should NOT reject null


def test_hurst_mean_reverting():
    series = make_mean_reverting()
    h = hurst_exponent(series)
    assert h < 0.5  # mean-reverting


def test_hurst_trending():
    # Exponential growth = strongly persistent/trending
    series = np.exp(np.linspace(0, 3, 500))
    h = hurst_exponent(series)
    assert h > 0.5  # trending


def test_hurst_short_series():
    series = np.array([1.0, 2.0, 3.0])
    h = hurst_exponent(series)
    assert h == 0.5  # insufficient data fallback


def test_compute_spread():
    a, b = make_cointegrated_pair()
    spread, hedge_ratio, half_life = compute_spread(a, b)
    assert len(spread) == len(a)
    assert hedge_ratio > 0
    assert half_life > 0


def test_analyze_pair_cointegrated():
    a, b = make_cointegrated_pair()
    result = analyze_pair(a, b, "SeriesA", "SeriesB")
    assert isinstance(result, PairAnalysis)
    assert result.series_a == "SeriesA"
    assert result.correlation > 0.5
    assert result.quality_score > 0


def test_analyze_pair_unrelated():
    # Use different seeds so the two random walks are truly independent
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(777)
    a = np.cumsum(rng1.normal(0, 1, 500)) + 100
    b = np.cumsum(rng2.normal(0, 1, 500)) + 100
    result = analyze_pair(a, b, "Random1", "Random2")
    # Two independent random walks — quality should be moderate at best
    # Allow up to 80 since random seeds can produce spurious cointegration
    assert result.quality_score < 80


def test_scan_pairs():
    a, b = make_cointegrated_pair()
    rng = np.random.default_rng(99)
    c = np.cumsum(rng.normal(0, 1, 500)) + 100
    data = {"A": a, "B": b, "C": c}
    results = scan_pairs(data, [("A", "B"), ("A", "C")])
    assert len(results) == 2
    assert results[0].quality_score >= results[1].quality_score  # sorted


def test_scan_pairs_min_quality():
    a, b = make_cointegrated_pair()
    data = {"A": a, "B": b}
    results = scan_pairs(data, [("A", "B")], min_quality=90)
    assert all(r.quality_score >= 90 for r in results)


def test_scan_pairs_missing_key():
    data = {"A": np.array([1.0, 2.0, 3.0])}
    results = scan_pairs(data, [("A", "MISSING")])
    assert len(results) == 0


def test_signal_generation():
    a, b = make_cointegrated_pair(n=500, seed=123)
    result = analyze_pair(a, b)
    assert result.signal in ["LONG_SPREAD", "SHORT_SPREAD", "NEUTRAL"]


def test_pair_analysis_fields():
    a, b = make_cointegrated_pair()
    result = analyze_pair(a, b, "X", "Y")
    assert isinstance(result.correlation, float)
    assert isinstance(result.hedge_ratio, float)
    assert isinstance(result.half_life_days, float)
    assert isinstance(result.hurst_exponent, float)
    assert isinstance(result.is_mean_reverting, bool)
    assert isinstance(result.adf_statistic, float)
    assert isinstance(result.adf_pvalue, float)
    assert isinstance(result.is_cointegrated, bool)
    assert isinstance(result.spread_zscore, float)
    assert isinstance(result.signal, str)
    assert isinstance(result.quality_score, float)
    assert isinstance(result.tradeable, bool)
