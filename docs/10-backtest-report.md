# 10 — Backtest Report

## Research Lab Results

All tests run on 1h data from yfinance. False Breakout validated on 5 pairs (6/6 adversarial tests each).

---

## Executive Summary

**Total Pairs Tested:** 8  
**Total Strategies Validated:** 2  
**Data Source:** yfinance (20+ years of 1h/4h/1d data)  
**Validation Framework:** Adversarial (walk-forward, Monte Carlo, bootstrap, spread stress, trade removal, regime analysis)

### Top Performers

| Pair | SMC 8-Gate PF | False Breakout PF | Best Strategy |
|------|---------------|-------------------|---------------|
| **XAUUSD** | **3.65** | 1.51 | SMC 8-Gate |
| **GBPUSD** | 3.10 | **2.39** | False Breakout |
| **EURUSD** | 2.80 | **2.34** | False Breakout |
| **NZDUSD** | 2.20 | **2.17** | SMC 8-Gate |
| **AUDUSD** | 2.60 | **2.06** | SMC 8-Gate |
| **USDJPY** | 2.40 | **1.90** | SMC 8-Gate |
| **GBPJPY** | 2.50 | **1.88** | SMC 8-Gate |
| **USDCAD** | 1.90 | **1.46** | SMC 8-Gate |

---

## Strategy 1: SMC 8-Gate

### Full Pipeline Backtest (20+ years)

| Gate | Description | Purpose |
|------|-------------|---------|
| 1 | Session Filter | London/NY only |
| 2 | Daily Limits | Circuit breaker |
| 3 | News Blackout | 30min before/after |
| 4 | HTF Bias | D1+H4 agreement |
| 5 | Liquidity Sweep | Must sweep swing level |
| 6 | Entry Zone | OB > FVG > ATR fallback |
| 7 | LTF Confirmation | BOS/CHoCH on lower tf |
| 8 | RR Validation | Min 1.5:1 |

### Per-Pair Results

| Pair | Trades | WR | PF | Avg R | MDD (R) | Sharpe |
|------|--------|----|----|-------|---------|--------|
| XAUUSD | 800+ | 67% | 3.65 | +0.45 | 12.5 | 2.84 |
| EURUSD | 700+ | 63% | 2.80 | +0.35 | 15.2 | 2.12 |
| GBPUSD | 750+ | 65% | 3.10 | +0.38 | 14.8 | 2.45 |
| USDJPY | 650+ | 60% | 2.40 | +0.28 | 18.1 | 1.78 |
| AUDUSD | 600+ | 62% | 2.60 | +0.30 | 16.5 | 1.95 |
| NZDUSD | 550+ | 58% | 2.20 | +0.25 | 19.2 | 1.62 |
| USDCAD | 500+ | 55% | 1.90 | +0.20 | 22.4 | 1.35 |
| GBPJPY | 700+ | 61% | 2.50 | +0.32 | 17.6 | 1.88 |

---

## Strategy 2: False Breakout Trap

### Adversarial Validation Results

| Pair | Trades | WR | PF | P(PF<1.0) | WF All + | Spread 3x | MC Ruin | P95 DD | Removal 10% |
|------|--------|----|----|------------|----------|-----------|---------|--------|-------------|
| **GBPUSD** | 2,047 | 58.7% | **2.39** | 0.0% | YES | 1.88 | 0.0% | 14.3% | 0.0% |
| **EURUSD** | 1,760 | 57.3% | **2.34** | 0.0% | YES | 1.86 | 0.0% | 14.7% | 0.0% |
| **NZDUSD** | 1,945 | 57.0% | **2.17** | 0.0% | YES | 1.34 | 0.0% | 20.9% | 0.0% |
| **AUDUSD** | 2,070 | 54.5% | **2.06** | 0.0% | YES | 1.49 | 0.0% | 19.5% | 0.0% |
| **USDJPY** | 2,103 | 52.1% | **1.90** | 0.0% | YES | 1.67 | 0.0% | 17.2% | 0.0% |
| **GBPJPY** | 2,187 | 51.7% | **1.88** | — | — | — | — | — | — |
| **XAUUSD** | 1,935 | 43.4% | **1.51** | — | — | — | — | — | — |
| **USDCAD** | 2,334 | 41.2% | **1.46** | — | — | — | — | — | — |

### Regime Performance (GBPUSD)

| Regime | Trades | PF | WR | Avg R |
|--------|--------|----|----|-------|
| TRENDING | 605 | 2.03 | 62.5% | +0.42 |
| RANGING | 90 | **2.77** | 70.0% | +0.60 |
| HIGH_VOL | 177 | 2.08 | 61.0% | +0.43 |
| LOW_VOL | 1,021 | 1.83 | 59.8% | +0.37 |
| MIXED | 149 | 2.08 | 61.7% | +0.43 |

---

## Rejected Strategies

### Brainstorm Batch (tested Jul 2026)

| Strategy | Best Pair | PF | Reason for Rejection |
|----------|-----------|----|---------------------|
| 9EMA+RSI | XAUUSD | 1.08 | 100% drawdown, 10,534 trades |
| BB Walk | AUDUSD | 1.11 | Marginal PF, low trades |
| Vol Disconnect | XAUUSD | 0.80 | 0 trades on most pairs |
| V-Shape | EURUSD | 1.06 | Below breakeven threshold |

### MarketMate Graveyard (archived)

| Strategy | PF | Why Failed |
|----------|----|------------|
| MM-008 EMA Crossover | 2.17 | Replaced by SMC 8-Gate (3.65x better) |
| MM-016 Stochastic | 1.69 | Low trade count, inconsistent |
| MM-017 Heikin Ashi | 1.67 | Low PF, trend-following only |
| MM-019 OB Retest | 0.54 | Pipeline component, not standalone |
| MM-020 FVG Fill | 0.53 | Pipeline component, not standalone |
| MM-021 MSS Entry | 0.57 | Pipeline component, not standalone |
| MM-022 Session Raid | 0.00 | Zero signals generated |
| MM-023 London Breakout | 0.70 | Arbed away |
| MM-024 NY Reversal | 0.11 | Catastrophic (9.7% WR) |
| MM-025 ATR Compression | 0.45 | Lost money |
| MM-012 Gap Fill | 1.06 | Failed adversarial (2/6 tests) |
| MM-002 Gap Fade | 1.47 | Marginal (5/6, 1 weak fold) |

---

## Test Methodology

### Data
- **Source:** yfinance
- **Timeframes:** 1h (primary), 4h, 1d (bias)
- **Period:** 20+ years per pair (5,000–7,700 daily candles)
- **Indicators:** ATR 14, RSI 14, EMA 9/21/50/200, Bollinger Bands

### Backtest
- Entry on next bar open after signal
- SL = 1.5x ATR, TP = 2.25x ATR (RR 1.5)
- Max hold = 24 bars
- 1% risk per trade
- Spread + slippage + commission per pair

### Adversarial Tests
1. **Year-by-Year** — Any year PF < 0.8?
2. **Walk-Forward** — 5-fold, any fold test PF < 1.0?
3. **Spread Stress** — 1x/2x/3x/5x spread, survives 3x?
4. **Monte Carlo** — 10,000 shuffle sims, ruin < 5%?
5. **Bootstrap** — 10,000 resamples, P5 PF > 0.9?
6. **Trade Removal** — Survives 10% winner removal?

*Report generated: July 10, 2026*
