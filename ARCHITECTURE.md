# Architecture Decisions

## Why Engle-Granger over Johansen

The Johansen test is more general and handles multivariate cointegration (3+ series). But for bivariate pairs trading, Engle-Granger is simpler, faster, and equally powerful. The two-step approach (OLS regression then ADF on residuals) maps directly to the trading strategy: the OLS gives you the hedge ratio, and the ADF confirms the spread is tradeable.

Johansen would add complexity (eigenvalue decomposition, trace statistics) without improving the bivariate case. If you need to test 3+ series simultaneously, Johansen is the right tool — but that is a different problem than pairs scanning.

## Why Hurst Exponent

The ADF test has a binary outcome (reject/fail-to-reject at some significance level). A spread can fail the ADF at p=0.05 but still be strongly mean-reverting in practice. The Hurst exponent provides a continuous measure of mean-reversion strength, capturing cases that ADF misses at marginal significance.

The two tests are complementary:
- ADF tests whether the spread has a unit root (statistical hypothesis test).
- Hurst measures the degree of persistence (descriptive statistic).

A pair that passes both tests is more robust than one that passes only one.

## Why Quality Scoring

No single metric fully captures whether a pair is tradeable. Cointegration without reasonable half-life is useless. Low Hurst without cointegration may be noise. High correlation without stationarity is a trap.

The quality score is a simple weighted composite that penalizes pairs missing any key property. The weights (30/25/20/15/10) reflect practical importance:
1. Cointegration is necessary (30 pts).
2. Mean-reversion confirms it (25 pts).
3. Half-life must be practical (20 pts).
4. Correlation provides economic intuition (15 pts).
5. Current signal is a bonus (10 pts).

The 70-point threshold for "tradeable" requires at minimum cointegration + mean-reversion + one more factor.

## Why OLS Hedge Ratio

The hedge ratio (beta) from OLS regression is the simplest and most interpretable estimator. For pairs trading, you need to know: "for every unit of B I hold, how many units of A offset it?" OLS answers this directly.

More sophisticated estimators exist (Kalman filter for time-varying hedge ratio, total least squares for errors-in-variables), but they add complexity without clear benefit for the screening stage. The OLS ratio is sufficient for identifying candidates; refinement happens in the execution layer.

## Why Optional statsmodels

The `statsmodels` library provides a production-grade ADF implementation with proper lag selection, MacKinnon critical values, and exact p-values. It is the right choice for serious analysis.

However, requiring statsmodels as a hard dependency would block users who only have numpy installed (e.g., lightweight containers, embedded systems, quick prototyping). The fallback ADF implementation uses a simplified regression with approximate critical values. It is less precise but sufficient for screening.

The recommended installation is `pip install pairs-scanner[full]` which includes statsmodels.

## Known Limitations

1. **Linear cointegration only.** The Engle-Granger method assumes a linear long-run relationship. Non-linear cointegration (threshold, Markov-switching) is not detected.

2. **No regime changes.** The analysis assumes stationarity of the cointegrating relationship over the entire sample. In practice, pairs can break down during regime shifts (market crises, structural changes).

3. **No transaction costs.** The quality score and signals do not account for spreads, commissions, or market impact. A pair with a 2-day half-life may not be profitable after costs.

4. **Static hedge ratio.** The OLS hedge ratio is estimated once over the full sample. In practice, hedge ratios drift and should be re-estimated periodically (rolling window or Kalman filter).

5. **No multiple testing correction.** When scanning many pairs, some will appear cointegrated by chance. Users should apply Bonferroni or FDR correction when scanning large universes.

6. **Sample period sensitivity.** Results depend heavily on the lookback window. A pair cointegrated over 2 years may not be cointegrated over 6 months, and vice versa.
