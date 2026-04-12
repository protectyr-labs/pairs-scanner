"""
Pairs Scanner — statistical arbitrage analysis toolkit.

Finds cointegrated pairs using:
- Engle-Granger two-step cointegration test
- Augmented Dickey-Fuller stationarity test
- Hurst exponent for mean-reversion detection
- OLS hedge ratio estimation
- Half-life of mean reversion
- Z-score based trading signals
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional

__version__ = "0.1.0"


@dataclass
class PairAnalysis:
    """Result of analyzing a pair of time series."""

    series_a: str
    series_b: str
    correlation: float
    hedge_ratio: float
    half_life_days: float
    hurst_exponent: float
    is_mean_reverting: bool  # Hurst < 0.5
    adf_statistic: float
    adf_pvalue: float
    is_cointegrated: bool  # ADF p-value < 0.05
    spread_zscore: float
    signal: str  # "LONG_SPREAD", "SHORT_SPREAD", "NEUTRAL"
    quality_score: float  # 0-100
    tradeable: bool  # quality_score >= 70


def adf_test(series: np.ndarray) -> tuple[float, float]:
    """
    Augmented Dickey-Fuller test for stationarity.

    Tests the null hypothesis that a unit root is present (non-stationary).
    A low p-value (< 0.05) means the series is stationary.

    Returns:
        (test_statistic, p_value)

    Uses statsmodels if available, otherwise a simplified implementation.
    """
    try:
        from statsmodels.tsa.stattools import adfuller

        result = adfuller(series, maxlag=1, regression="c", autolag=None)
        return float(result[0]), float(result[1])
    except ImportError:
        # Simplified ADF: regress diff(y) on y_lag
        y = series[1:] - series[:-1]
        x = series[:-1]
        n = len(y)
        x_mean = x.mean()
        beta = np.sum((x - x_mean) * y) / np.sum((x - x_mean) ** 2)
        residuals = y - beta * x
        se = np.sqrt(np.sum(residuals**2) / (n - 1)) / np.sqrt(
            np.sum((x - x_mean) ** 2)
        )
        t_stat = beta / se if se > 0 else 0.0
        # Approximate p-value using Dickey-Fuller critical values (n > 250)
        if t_stat < -3.43:
            p_val = 0.01
        elif t_stat < -2.86:
            p_val = 0.05
        elif t_stat < -2.57:
            p_val = 0.10
        else:
            p_val = 0.50
        return float(t_stat), p_val


def hurst_exponent(series: np.ndarray) -> float:
    """
    Compute the Hurst exponent of a time series using the rescaled range method.

    Interpretation:
        H < 0.5: mean-reverting (anti-persistent)
        H = 0.5: random walk (geometric Brownian motion)
        H > 0.5: trending (persistent)

    Args:
        series: 1-D array of prices or spread values.

    Returns:
        Hurst exponent in [0.0, 1.0].
    """
    n = len(series)
    if n < 20:
        return 0.5  # insufficient data

    max_k = min(n // 2, 100)
    lags = range(2, max_k)
    tau = []
    for lag in lags:
        diffs = series[lag:] - series[:-lag]
        std = np.std(diffs)
        if std > 0:
            tau.append(std)
        else:
            tau.append(1e-10)

    if len(tau) < 2:
        return 0.5

    log_lags = np.log(list(lags)[: len(tau)])
    log_tau = np.log(tau)

    # OLS fit: log(tau) = H * log(lag) + c
    x_mean = log_lags.mean()
    y_mean = log_tau.mean()
    h = np.sum((log_lags - x_mean) * (log_tau - y_mean)) / np.sum(
        (log_lags - x_mean) ** 2
    )

    return float(np.clip(h, 0.0, 1.0))


def compute_spread(
    series_a: np.ndarray,
    series_b: np.ndarray,
) -> tuple[np.ndarray, float, float]:
    """
    Compute the spread between two series using OLS hedge ratio.

    The hedge ratio is estimated via ordinary least squares:
        series_a = beta * series_b + epsilon

    The spread is then: series_a - beta * series_b

    Half-life is estimated by regressing spread changes on lagged spread
    levels, using the Ornstein-Uhlenbeck approximation.

    Args:
        series_a: Price series A (numpy array).
        series_b: Price series B (numpy array).

    Returns:
        (spread, hedge_ratio, half_life_days)
    """
    x = series_b
    y = series_a
    x_mean = x.mean()
    beta = np.sum((x - x_mean) * (y - y.mean())) / np.sum((x - x_mean) ** 2)

    spread = y - beta * x

    # Half-life of mean reversion: regress spread_diff on spread_lag
    spread_lag = spread[:-1]
    spread_diff = np.diff(spread)
    sl_mean = spread_lag.mean()
    phi = np.sum((spread_lag - sl_mean) * spread_diff) / np.sum(
        (spread_lag - sl_mean) ** 2
    )

    if phi >= 0:
        half_life = float("inf")
    else:
        half_life = -np.log(2) / phi

    return spread, float(beta), float(half_life)


def analyze_pair(
    series_a: np.ndarray,
    series_b: np.ndarray,
    name_a: str = "A",
    name_b: str = "B",
    zscore_entry: float = 2.0,
    zscore_exit: float = 0.5,
) -> PairAnalysis:
    """
    Full cointegration analysis of a pair of time series.

    Runs the complete Engle-Granger pipeline:
    1. Compute correlation between the two series.
    2. Estimate the OLS hedge ratio and construct the spread.
    3. Test the spread for stationarity (ADF test).
    4. Compute the Hurst exponent of the spread.
    5. Estimate the half-life of mean reversion.
    6. Compute the current z-score and generate a trading signal.
    7. Assign a composite quality score.

    Args:
        series_a: Price series A (numpy array).
        series_b: Price series B (numpy array).
        name_a: Label for series A.
        name_b: Label for series B.
        zscore_entry: Z-score threshold for entry signals.
        zscore_exit: Z-score threshold for exit/neutral.

    Returns:
        PairAnalysis dataclass with all metrics and trading signal.
    """
    # Correlation
    corr = float(np.corrcoef(series_a, series_b)[0, 1])

    # Spread and hedge ratio
    spread, hedge_ratio, half_life = compute_spread(series_a, series_b)

    # Stationarity of spread
    adf_stat, adf_pval = adf_test(spread)
    is_cointegrated = adf_pval < 0.05

    # Hurst exponent of spread
    h = hurst_exponent(spread)
    is_mean_reverting = h < 0.5

    # Current z-score
    spread_mean = spread.mean()
    spread_std = spread.std()
    current_zscore = (
        (spread[-1] - spread_mean) / spread_std if spread_std > 0 else 0.0
    )

    # Trading signal
    if current_zscore > zscore_entry:
        signal = "SHORT_SPREAD"
    elif current_zscore < -zscore_entry:
        signal = "LONG_SPREAD"
    else:
        signal = "NEUTRAL"

    # Quality score (0-100)
    score = 0.0
    if is_cointegrated:
        score += 30
    if is_mean_reverting:
        score += 25
    if 1 < half_life < 60:
        score += 20  # reasonable half-life for daily data
    if abs(corr) > 0.7:
        score += 15
    if abs(current_zscore) > 1.5:
        score += 10  # near entry signal

    return PairAnalysis(
        series_a=name_a,
        series_b=name_b,
        correlation=round(corr, 4),
        hedge_ratio=round(hedge_ratio, 4),
        half_life_days=round(half_life, 1),
        hurst_exponent=round(h, 4),
        is_mean_reverting=is_mean_reverting,
        adf_statistic=round(adf_stat, 4),
        adf_pvalue=round(adf_pval, 4),
        is_cointegrated=is_cointegrated,
        spread_zscore=round(float(current_zscore), 4),
        signal=signal,
        quality_score=round(score, 1),
        tradeable=score >= 70,
    )


def scan_pairs(
    data: dict[str, np.ndarray],
    pairs: list[tuple[str, str]],
    min_quality: float = 0.0,
) -> list[PairAnalysis]:
    """
    Scan multiple pairs and return analysis results.

    Iterates over a list of pair combinations, runs full cointegration
    analysis on each, and returns results sorted by quality score.

    Args:
        data: Dict mapping series names to price arrays.
        pairs: List of (name_a, name_b) tuples to analyze.
        min_quality: Minimum quality score to include in results.

    Returns:
        List of PairAnalysis results, sorted by quality score descending.
    """
    results = []
    for name_a, name_b in pairs:
        if name_a not in data or name_b not in data:
            continue
        try:
            analysis = analyze_pair(data[name_a], data[name_b], name_a, name_b)
            if analysis.quality_score >= min_quality:
                results.append(analysis)
        except Exception:
            continue

    results.sort(key=lambda x: x.quality_score, reverse=True)
    return results
