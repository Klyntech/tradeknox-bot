# 10 — Backtest Report

## 3.5-Year Daily Data (Jan 2023 — Jul 2026)

---

## Executive Summary

**Total Pairs Tested:** 5  
**Total Strategies Tested:** 6  
**Data Source:** yfinance (daily candles)  
**Period:** January 2023 — July 2026 (3.5 years)

### Top Performers by Pair

| Pair | Best Strategy | WR | PF | Return | Status |
|------|---------------|-----|-----|--------|--------|
| **XAUUSD** | EMA Crossover (MM-008) | 58.0% | **2.17** | +66.08% | ✅ PRIMARY |
| **USDJPY** | EMA Crossover (MM-008) | 52.1% | **1.82** | +22.18% | ✅ NEW |
| **GBPJPY** | Stochastic Extreme (MM-016) | 54.2% | **1.69** | +7.08% | ✅ PRIMARY |
| **GBPUSD** | MA Crossover | 46.1% | 1.43 | +13.79% | ⚠️ EXCLUDED |
| **EURUSD** | MA Crossover | 40.3% | 1.28 | +8.61% | ❌ EXCLUDED |

---

## Detailed Results by Pair

### 1. XAUUSD (Gold) — PRIMARY PAIR

| Strategy | Trades | Win Rate | Profit Factor | Total Return | Verdict |
|----------|--------|----------|---------------|--------------|---------|
| **EMA Crossover (MM-008)** | 119 | 58.0% | **2.17** | +66.08% | 🏆 BEST |
| MA Crossover 9/21 | 132 | 56.1% | 2.01 | +66.83% | ✅ STRONG |
| Stochastic Extreme (MM-016) | 41 | 58.5% | 1.76 | +18.62% | ✅ GOOD |
| Heikin Ashi Trend (MM-017) | 118 | 55.9% | 1.67 | +47.61% | ✅ GOOD |
| Breakout 10 | 72 | 62.5% | 1.58 | +25.43% | ✅ GOOD |
| RSI Extremes | 4 | 75.0% | 1.94 | +3.42% | ⚠️ TOO FEW |

**Analysis:**
- All strategies profitable on XAUUSD
- EMA Crossover has highest PF (2.17) with good trade count (119)
- RSI Extremes has highest WR (75%) but only 4 trades — statistically insignificant
- **Recommendation:** Use EMA Crossover + MA Crossover as primary signals

---

### 2. GBPJPY (GBP/JPY) — SECONDARY PAIR

| Strategy | Trades | Win Rate | Profit Factor | Total Return | Verdict |
|----------|--------|----------|---------------|--------------|---------|
| **Stochastic Extreme (MM-016)** | 24 | 54.2% | **1.69** | +7.08% | 🏆 BEST |
| Heikin Ashi Trend (MM-017) | 79 | 45.6% | 1.40 | +13.66% | ✅ GOOD |
| Breakout 20 | 31 | 45.2% | 1.46 | +6.26% | ✅ GOOD |
| EMA Crossover (MM-008) | 74 | 45.9% | 1.39 | +12.44% | ✅ GOOD |
| MA Crossover 50/200 | 86 | 45.3% | 1.35 | +13.33% | ✅ GOOD |
| RSI Extremes | 5 | 40.0% | 0.50 | -2.66% | ❌ LOSING |

**Analysis:**
- 5 out of 6 strategies profitable
- Stochastic Extreme has best PF (1.69) with decent WR (54.2%)
- RSI Extremes is the only losing strategy (PF 0.50)
- **Recommendation:** Use Stochastic Extreme + Heikin Ashi as primary signals

---

### 3. USDJPY (USD/JPY) — NEW PROFITABLE PAIR

| Strategy | Trades | Win Rate | Profit Factor | Total Return | Verdict |
|----------|--------|----------|---------------|--------------|---------|
| **EMA Crossover (MM-008)** | 71 | 52.1% | **1.82** | +22.18% | 🏆 BEST |
| MA Crossover 9/21 | 79 | 51.9% | 1.78 | +24.16% | ✅ STRONG |
| Breakout 10 | 29 | 51.7% | 1.89 | +9.33% | ✅ STRONG |
| Heikin Ashi Trend (MM-017) | 85 | 47.1% | 1.61 | +20.78% | ✅ GOOD |
| Stochastic Extreme (MM-016) | 36 | 52.8% | 1.41 | +7.08% | ✅ GOOD |
| RSI Extremes | 6 | 50.0% | 0.63 | -1.87% | ❌ LOSING |

**Analysis:**
- **5 out of 6 strategies profitable** (previously excluded!)
- EMA Crossover has highest PF (1.82) with good trade count (71)
- Breakout has best PF (1.89) but lower trade count (29)
- **Recommendation:** Use EMA Crossover + Breakout as primary signals

---

### 4. EURUSD (EUR/USD) — EXCLUDED

| Strategy | Trades | Win Rate | Profit Factor | Total Return | Verdict |
|----------|--------|----------|---------------|--------------|---------|
| MA Crossover 21/50 | 72 | 40.3% | 1.28 | +8.61% | ⚠️ MARGINAL |
| RSI Extremes | 7 | 42.9% | 1.50 | +1.26% | ⚠️ TOO FEW |
| EMA Crossover (MM-008) | 65 | 38.5% | 1.12 | +3.67% | ⚠️ WEAK |
| Heikin Ashi Trend (MM-017) | 64 | 34.4% | 0.87 | -4.27% | ❌ LOSING |
| Stochastic Extreme (MM-016) | 45 | 31.1% | 0.79 | -5.09% | ❌ LOSING |
| Breakout 20 | 28 | 25.0% | 0.50 | -8.78% | ❌ LOSING |

**Analysis:**
- 3 out of 6 strategies losing money
- Best strategy (MA Crossover) only PF 1.28 — barely profitable
- Low win rates across all strategies (25-43%)
- **Recommendation:** Keep excluded from live trading

---

### 5. GBPUSD (GBP/USD) — EXCLUDED

| Strategy | Trades | Win Rate | Profit Factor | Total Return | Verdict |
|----------|--------|----------|---------------|--------------|---------|
| MA Crossover 9/21 | 76 | 46.1% | 1.43 | +13.79% | ⚠️ MARGINAL |
| RSI Extremes | 7 | 42.9% | 1.56 | +1.30% | ⚠️ TOO FEW |
| EMA Crossover (MM-008) | 65 | 44.6% | 1.33 | +9.73% | ⚠️ MARGINAL |
| Breakout 20 | 30 | 33.3% | 0.79 | -3.21% | ❌ LOSING |
| Heikin Ashi Trend (MM-017) | 67 | 38.8% | 1.02 | +0.55% | ⚠️ BREAKEVEN |
| Stochastic Extreme (MM-016) | 46 | 28.3% | 0.70 | -7.49% | ❌ LOSING |

**Analysis:**
- Mixed results — some strategies profitable, others losing
- Best strategy (MA Crossover) only PF 1.43 — inconsistent
- 2 out of 6 strategies losing money
- **Recommendation:** Keep excluded from live trading

---

## Strategy Performance Summary

### By Strategy Type

| Strategy | Avg PF (Profitable Pairs) | Best Pair | Worst Pair |
|----------|---------------------------|-----------|------------|
| **EMA Crossover (MM-008)** | 1.79 | XAUUSD (2.17) | EURUSD (1.12) |
| **Heikin Ashi Trend (MM-017)** | 1.56 | XAUUSD (1.67) | EURUSD (0.87) |
| **Stochastic Extreme (MM-016)** | 1.62 | GBPJPY (1.69) | GBPUSD (0.70) |
| MA Crossover | 1.71 | XAUUSD (2.01) | EURUSD (1.28) |
| Breakout | 1.64 | USDJPY (1.89) | EURUSD (0.50) |
| RSI Extremes | 1.31 | XAUUSD (1.94) | GBPJPY (0.50) |

### Trade Frequency

| Strategy | Avg Trades/Pair | Frequency |
|----------|-----------------|-----------|
| MA Crossover | 91 | High |
| EMA Crossover (MM-008) | 79 | High |
| Heikin Ashi Trend (MM-017) | 83 | High |
| Stochastic Extreme (MM-016) | 38 | Medium |
| Breakout | 38 | Medium |
| RSI Extremes | 6 | Low |

---

## Recommendations

### Live Deployment Strategy

**Primary Pairs (Deploy Now):**
1. **XAUUSD** — Use EMA Crossover + MA Crossover (PF 2.0+)
2. **USDJPY** — Use EMA Crossover + Breakout (PF 1.8+)
3. **GBPJPY** — Use Stochastic Extreme + Heikin Ashi (PF 1.4-1.7)

**Excluded Pairs (Do Not Trade):**
- EURUSD — Consistently unprofitable
- GBPUSD — Mixed results, unreliable

### Signal Generation Rules

1. **Minimum Confluence Score:** 2/3 strategies must agree
2. **Minimum Profit Factor:** 1.5+ (from backtest)
3. **Minimum Trade Count:** 20+ trades (statistical significance)
4. **Day Filter:** Avoid Friday for USDJPY, Avoid Monday for XAUUSD

### Risk Management

- **Max Risk per Trade:** 1% of account
- **Stop Loss:** 1.5x ATR from entry
- **Take Profit:** 2.5x ATR (1.67:1 R:R)
- **Max Concurrent Trades:** 3
- **Max Daily Trades:** 5

---

## Annualized Returns

| Pair | Strategy | Total Return (3.5y) | Per Annum | Per Day |
|------|----------|---------------------|-----------|---------|
| XAUUSD | EMA Crossover | +66.08% | ~18.9% | ~0.05% |
| USDJPY | EMA Crossover | +22.18% | ~6.3% | ~0.02% |
| GBPJPY | Stochastic | +7.08% | ~2.0% | ~0.01% |

**Context:**
- XAUUSD 18.9%/year — Good (beat S&P 500 average ~10%)
- USDJPY 6.3%/year — Decent (below stock market average)
- GBPJPY 2.0%/year — Low (barely beats inflation)

---

## Next Steps

1. **Dukascopy Validation** — Download hourly data from dukascopy.com to validate results
2. **Walk-Forward Testing** — Test strategies on rolling 6-month windows
3. **Monte Carlo Simulation** — Stress-test returns with random trade sequences
4. **Live Paper Trading** — Run strategies on demo account for 30 days
5. **Deploy to Production** — Go live with proven strategies

---

*Report generated: July 7, 2026*  
*Data source: yfinance (daily candles)*  
*Period: January 2023 — July 2026*
