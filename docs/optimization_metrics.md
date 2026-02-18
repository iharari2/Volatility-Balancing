# Optimization Metrics Reference

This document describes each metric computed during parameter optimization, including its formula, units, and interpretation.

## Metrics

### Total Return
- **Source**: `algorithm_return_pct` (direct from simulation)
- **Formula**: `(final_value - initial_cash) / initial_cash * 100`
- **Units**: Percentage (%)
- **Better**: Higher
- **Interpretation**: The total percentage gain or loss over the simulation period.

### Sharpe Ratio
- **Source**: `algorithm_sharpe_ratio` (direct from simulation)
- **Formula**: `(mean_daily_return * 252) / (std_daily_return * sqrt(252))`
- **Units**: Ratio (dimensionless)
- **Better**: Higher
- **Interpretation**: Risk-adjusted return. Values above 1.0 are generally considered good; above 2.0 is excellent.

### Max Drawdown
- **Source**: `algorithm_max_drawdown` (direct from simulation)
- **Formula**: `max((peak - trough) / peak) * 100` over all time points
- **Units**: Percentage (%)
- **Better**: Lower (closer to 0)
- **Interpretation**: The largest peak-to-trough decline during the simulation. Represents worst-case loss from a high point.

### Volatility
- **Source**: `algorithm_volatility` (direct from simulation)
- **Formula**: `std(daily_returns) * sqrt(252)` (annualized)
- **Units**: Ratio (dimensionless, annualized)
- **Better**: Lower
- **Interpretation**: Annualized standard deviation of daily returns. Measures overall risk.

### Trade Count
- **Source**: `algorithm_trades` (direct from simulation)
- **Formula**: Count of executed trades
- **Units**: Integer
- **Better**: Context-dependent (fewer trades = lower costs; more trades = more responsive)
- **Interpretation**: Total number of trades the algorithm executed during the simulation period.

### Calmar Ratio
- **Formula**: `annualized_return_pct / abs(max_drawdown_pct)`
- **Units**: Ratio (dimensionless)
- **Better**: Higher
- **Interpretation**: Return relative to maximum drawdown risk. Higher values indicate better risk-adjusted performance relative to worst-case losses.

### Sortino Ratio
- **Formula**: `(mean_daily_return * 252) / (downside_deviation * sqrt(252))`
- **Units**: Ratio (dimensionless)
- **Better**: Higher
- **Interpretation**: Like the Sharpe ratio but only penalizes downside volatility. A better measure when returns are asymmetric.

### Win Rate
- **Formula**: `positive_return_days / total_days`
- **Units**: Ratio (0 to 1)
- **Better**: Higher
- **Interpretation**: Fraction of days with positive returns. Values above 0.5 mean more winning days than losing days.

### Profit Factor
- **Formula**: `sum(positive_daily_returns) / abs(sum(negative_daily_returns))`
- **Units**: Ratio (dimensionless)
- **Better**: Higher (above 1.0 means profitable)
- **Interpretation**: Ratio of gross profits to gross losses. A profit factor of 2.0 means the strategy earned twice as much on winning days as it lost on losing days.

### Avg Trade Duration
- **Formula**: `total_trading_days / trade_count`
- **Units**: Days
- **Better**: Context-dependent
- **Interpretation**: Average number of trading days between trades. Lower values indicate more frequent trading.

## Data Resolution

The `intraday_interval_minutes` setting controls the granularity of price data used in simulation:

| Resolution | Data Points (1 year) | Speed | Accuracy |
|---|---|---|---|
| 5 min | ~18,720 | Slowest | Highest |
| 15 min | ~6,240 | Moderate | High |
| 30 min | ~3,120 | Fast | Good (default) |
| 60 min | ~1,560 | Fastest | Moderate |

Higher resolution captures more intraday price movements, potentially triggering more trades. Lower resolution runs faster but may miss short-lived price swings. For optimization across many parameter combinations, 30-minute or 60-minute resolution is recommended to keep total runtime manageable.

## Include After-Hours

When enabled, the simulation includes pre-market (4:00-9:30 ET) and after-hours (16:00-20:00 ET) price data. This increases the number of data points and may trigger additional trades during extended hours sessions.
