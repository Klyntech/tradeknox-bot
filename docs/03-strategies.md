# 03 — Strategies

## Overview

TradeKnox has **2 production-validated strategies** tested on **8 forex pairs** with **20+ years of hourly data**. Both survived full adversarial validation (walk-forward, Monte Carlo, bootstrap, spread stress, trade removal).

## Active Strategies

| # | Strategy | Type | PF Range | Best Pair | Test Coverage |
|---|----------|------|----------|-----------|---------------|
| 1 | **SMC 8-Gate** | Trend Following | 1.5–3.65 | XAUUSD | All 8 pairs, 4 timeframes |
| 2 | **False Breakout Trap** | Reversal | 1.49–2.39 | GBPUSD | All 8 pairs, 1h data |

---

## Strategy 1: SMC 8-Gate

**Type:** Smart Money Concepts — Trend Following  
**Pipeline:** `market_structure.py` → `entry_logic.py` → `scoring_engine.py`  
**Timeframe:** Multi-timeframe (15m for entry, 1h for structure, 4h for trend, 1d for bias)

### 8 Gates (Sequential, Fail-Fast)

| Gate | Component | File | Function |
|------|-----------|------|----------|
| 1 | Session Filter | `bot.py` | London (07–16 UTC) or NY (12–21 UTC) only |
| 2 | Daily Limits + Drawdown | `bot.py` | Max trades/day, circuit breaker |
| 3 | News Blackout | `scoring_engine.py` | Block 30min before/after high-impact events |
| 4 | HTF Bias | `market_structure.py` | D1 + H4 must agree; neutral = reject |
| 5 | Liquidity Sweep | `market_structure.py` | Must sweep a swing level FIRST |
| 6 | Entry Zone | `entry_logic.py` | OB (priority) or FVG, with 2x ATR displacement |
| 7 | LTF Confirmation | `market_structure.py` | BOS/CHoCH on M15/M5 |
| 8 | RR Validation | `entry_logic.py` | Minimum 1.5R |

### Backtest Results

| Pair | PF | WR | Trades | Sample Period |
|------|----|----|--------|---------------|
| XAUUSD | 3.65 | 67% | 800+ | 20+ years |
| EURUSD | 2.8 | 63% | 700+ | 22 years |
| GBPUSD | 3.1 | 65% | 750+ | 22 years |
| USDJPY | 2.4 | 60% | 650+ | 30 years |
| AUDUSD | 2.6 | 62% | 600+ | 20 years |
| NZDUSD | 2.2 | 58% | 550+ | 22 years |
| USDCAD | 1.9 | 55% | 500+ | 23 years |
| GBPJPY | 2.5 | 61% | 700+ | 22 years |

**Regime Performance:** Best in TRENDING/HIGH_VOL regimes.

---

## Strategy 2: False Breakout Trap

**Type:** Counter-Trend — Reversal  
**File:** `research/adversarial_false_breakout.py`  
**Timeframe:** 1h  
**Parameters:** Lookback = 10 bars

### Rule

Price exceeds a 10-bar swing high → fails to sustain, closes back below within 2 bars → SHORT  
Price breaks below a 10-bar swing low → fails to sustain, closes back above within 2 bars → LONG  

No liquidity narrative. No intent assumption. Pure statistical edge: failed breakouts predict reversals.

### Adversarial Validation Results (5 pairs, 6/6 tests each)

| Test | GBPUSD | EURUSD | NZDUSD | AUDUSD | USDJPY |
|------|--------|--------|--------|--------|--------|
| **PF** | **2.39** | **2.34** | **2.17** | **2.06** | **1.90** |
| WR | 58.7% | 57.3% | 57.0% | 54.5% | 52.1% |
| Trades | 2,047 | 1,760 | 1,945 | 2,070 | 2,103 |
| P(PF<1.0) | **0.0%** | **0.0%** | **0.0%** | **0.0%** | **0.0%** |
| Walk-Forward | All + | All + | All + | All + | All + |
| Spread 3x | 1.88 | 1.86 | 1.34 | 1.49 | 1.67 |
| MC Ruin | 0% | 0% | 0% | 0% | 0% |
| P95 DD | 14.3% | 14.7% | 20.9% | 19.5% | 17.2% |
| Removal 30% | 1.37 | 1.33 | 1.04 | 1.09 | 1.19 |

### Regime Performance

Works in ALL regimes. Best in RANGING/MIXED (PF 2.77 on GBPUSD ranging).

---

## Per-Pair Configuration (8 Pairs)

| Pair | SMC 8-Gate PF | False Breakout PF | Best Days | Avoid Days |
|------|---------------|-------------------|-----------|------------|
| EURUSD | 2.8 | 2.34 | Tue, Thu | Mon |
| GBPUSD | 3.1 | **2.39** | Wed, Thu | Fri |
| USDJPY | 2.4 | 1.90 | Mon, Wed | Fri |
| XAUUSD | **3.65** | 1.51 | Thu, Fri | Mon |
| AUDUSD | 2.6 | 2.06 | Tue, Thu | Wed |
| NZDUSD | 2.2 | 2.17 | Tue, Wed | Mon |
| USDCAD | 1.9 | 1.46 | Wed, Fri | Tue |
| GBPJPY | 2.5 | 1.88 | Thu, Wed | Wed |

---

## Strategy Confluence

Two strategies cover opposite market regimes:

```
TRENDING / HIGH_VOL  →  SMC 8-Gate (PF 3.65)
RANGING / LOW_VOL    →  False Breakout Trap (PF 2.77 in ranging)
```

They naturally deconflict: SMC rides trend continuations, False Breakout fades failed reversals.

---

## Rejected Strategies

All 8 indicator-based strategies previously documented here were deleted (MarketMate Graveyard):
- MM-008 (EMA Crossover), MM-016 (Stochastic Extreme), MM-017 (Heikin Ashi Trend)
- MA Crossover, Breakout, RSI Extremes, Session Timing, EMA Alignment

Historical context: `archive/scripts/backtest_strategies.py.old`
