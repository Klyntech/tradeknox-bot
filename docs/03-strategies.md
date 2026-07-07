# 03 — Strategies

## Overview

TradeKnox uses **8 backtested strategies** across 3 pairs. Each strategy is tested on 3.5 years of daily data (Jan 2023 — Jul 2026) from yfinance.

## Active Pairs

| Pair | Status | Best Strategy | Profit Factor |
|------|--------|---------------|---------------|
| **XAUUSD** | ✅ Active | EMA Crossover (MM-008) | 2.17 |
| **GBPJPY** | ✅ Active | Stochastic Extreme (MM-016) | 1.69 |
| **USDJPY** | ✅ Active | EMA Crossover (MM-008) | 1.82 |
| EURUSD | ❌ Excluded | — | — |
| GBPUSD | ❌ Excluded | — | — |

## Strategy List

### 1. MA Crossover (Original)

**Type:** Trend Following  
**File:** `strategies.py:detect_ma_crossover()`

| Parameter | Value |
|-----------|-------|
| Fast Period | 9 (XAUUSD/USDJPY), 50 (GBPJPY) |
| Slow Period | 21 (XAUUSD/USDJPY), 200 (GBPJPY) |
| Timeframe | 4h |

**Entry Logic:**
- **BUY:** Fast MA crosses above Slow MA (Golden Cross)
- **SELL:** Fast MA crosses below Slow MA (Death Cross)

**Backtest Results:**
| Pair | Trades | WR | PF | Return |
|------|--------|-----|-----|--------|
| XAUUSD | 132 | 56.1% | 2.01 | +66.83% |
| USDJPY | 79 | 51.9% | 1.78 | +24.16% |
| GBPJPY | 86 | 45.3% | 1.35 | +13.33% |

---

### 2. Breakout (N-Bar High/Low)

**Type:** Breakout  
**File:** `strategies.py:detect_breakout()`

| Parameter | Value |
|-----------|-------|
| Lookback | 10 (XAUUSD/USDJPY), 20 (GBPJPY) |
| Timeframe | 4h |

**Entry Logic:**
- **BUY:** Price breaks above N-bar high
- **SELL:** Price breaks below N-bar low

**Backtest Results:**
| Pair | Trades | WR | PF | Return |
|------|--------|-----|-----|--------|
| USDJPY | 29 | 51.7% | 1.89 | +9.33% |
| GBPJPY | 31 | 45.2% | 1.46 | +6.26% |
| XAUUSD | 72 | 62.5% | 1.58 | +25.43% |

---

### 3. RSI Extreme Reversal

**Type:** Reversal  
**File:** `strategies.py:detect_rsi_extremes()`

| Parameter | Value |
|-----------|-------|
| Oversold | 20 (USDJPY/GBPJPY), 30 (XAUUSD) |
| Overbought | 80 (USDJPY/GBPJPY), 70 (XAUUSD) |
| Timeframe | 4h |

**Entry Logic:**
- **BUY:** RSI < oversold level
- **SELL:** RSI > overbought level

**Backtest Results:**
| Pair | Trades | WR | PF | Return |
|------|--------|-----|-----|--------|
| XAUUSD | 4 | 75.0% | 1.94 | +3.42% |
| GBPJPY | 5 | 40.0% | 0.50 | -2.66% |
| USDJPY | 6 | 50.0% | 0.63 | -1.87% |

**Note:** Low trade count — statistically less reliable.

---

### 4. EMA Crossover (MM-008) — NEW

**Type:** Trend Following  
**File:** `strategies.py:detect_ema_crossover()`  
**Source:** MarketMate MM-008

| Parameter | Value |
|-----------|-------|
| Fast EMA | 9 |
| Slow EMA | 21 |
| Trend EMA | 100 |
| Timeframe | 4h |

**Entry Logic:**
- **BUY:** Fast EMA crosses above Slow EMA AND close > Trend EMA (100)
- **SELL:** Fast EMA crosses below Slow EMA AND close < Trend EMA (100)

**Confirmation:** Requires trend alignment (price above/below 100 EMA)

**Backtest Results:**
| Pair | Trades | WR | PF | Return |
|------|--------|-----|-----|--------|
| XAUUSD | 119 | 58.0% | **2.17** | +66.08% |
| USDJPY | 71 | 52.1% | **1.82** | +22.18% |
| GBPJPY | 74 | 45.9% | 1.39 | +12.44% |

**Why It Works:**
- Trend confirmation reduces false signals
- 100 EMA acts as dynamic support/resistance
- High trade count (71-119) for statistical significance

---

### 5. Heikin Ashi Trend (MM-017) — NEW

**Type:** Trend Following  
**File:** `strategies.py:detect_heikin_ashi_trend()`  
**Source:** MarketMate MM-017

| Parameter | Value |
|-----------|-------|
| Min Consecutive | 3 candles |
| Trend Filter | EMA 50 |
| Timeframe | 4h |

**Entry Logic:**
- **BUY:** 3+ consecutive bullish Heikin Ashi candles
- **SELL:** 3+ consecutive bearish Heikin Ashi candles

**Confirmation:** Must align with EMA 50 trend

**Backtest Results:**
| Pair | Trades | WR | PF | Return |
|------|--------|-----|-----|--------|
| XAUUSD | 118 | 55.9% | 1.67 | +47.61% |
| GBPJPY | 79 | 45.6% | 1.40 | +13.66% |
| USDJPY | 85 | 47.1% | 1.61 | +20.78% |

**Why It Works:**
- Heikin Ashi smooths price action, reducing noise
- Consecutive candles confirm momentum
- Trend filter prevents counter-trend entries

---

### 6. Stochastic Extreme Reversal (MM-016) — NEW

**Type:** Reversal  
**File:** `strategies.py:detect_stochastic_extreme()`  
**Source:** MarketMate MM-016

| Parameter | Value |
|-----------|-------|
| K Period | 14 |
| D Period | 3 |
| Oversold Zone | < 35 |
| Overbought Zone | > 65 |
| Timeframe | 4h |

**Entry Logic:**
- **BUY:** K crosses above D while K is near oversold (< 35)
- **SELL:** K crosses below D while K is near overbought (> 65)

**Backtest Results:**
| Pair | Trades | WR | PF | Return |
|------|--------|-----|-----|--------|
| GBPJPY | 24 | 54.2% | **1.69** | +7.08% |
| XAUUSD | 41 | 58.5% | 1.76 | +18.62% |
| USDJPY | 36 | 52.8% | 1.41 | +7.08% |

**Why It Works:**
- Catches reversals at exhaustion points
- K/D crossover confirms momentum shift
- Best on GBPJPY where reversals are more common

---

### 7. Session Timing

**Type:** Filter  
**File:** `strategies.py:detect_session_entry()`

| Session | Hours (UTC) | Score |
|---------|-------------|-------|
| Overlap | 12:00-16:00 | 3/3 |
| London | 07:00-12:00 | 2/3 |
| New York | 12:00-21:00 | 2/3 |
| Asia | 00:00-08:00 | 1/3 |
| Dead Zone | 21:00-00:00 | 0/3 |

**Logic:** Only trade during active sessions. Overlap (London+NY) gets highest score.

---

### 8. EMA Alignment

**Type:** Trend Filter  
**File:** `strategies.py:detect_ema_alignment()`

| Parameter | Value |
|-----------|-------|
| EMA 9 | Fast |
| EMA 21 | Medium |
| EMA 50 | Slow |
| EMA 200 | Trend |

**Entry Logic:**
- **BUY:** EMA 9 > EMA 21 > EMA 50 AND price > EMA 200
- **SELL:** EMA 9 < EMA 21 < EMA 50 AND price < EMA 200

**Logic:** All EMAs must be aligned in the same direction for maximum confluence.

---

## Per-Pair Configurations

### XAUUSD (Gold)

```python
PAIR_STRATEGIES["XAUUSD"] = {
    "timeframe": "4h",
    "ma_fast": 9,
    "ma_slow": 21,
    "breakout_lookback": 10,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "ema_fast": 9,
    "ema_slow": 21,
    "ema_trend": 100,
    "weights": {
        "breakout": 2,
        "ma": 1,
        "ema_crossover": 1,
        "heikin_ashi": 0,
        "stochastic": 0
    },
    "best_days": ["Thursday", "Friday"],
    "avoid_days": ["Monday"]
}
```

### GBPJPY (GBP/JPY)

```python
PAIR_STRATEGIES["GBPJPY"] = {
    "timeframe": "4h",
    "ma_fast": 50,
    "ma_slow": 200,
    "breakout_lookback": 20,
    "rsi_oversold": 20,
    "rsi_overbought": 80,
    "ema_fast": 9,
    "ema_slow": 21,
    "ema_trend": 100,
    "weights": {
        "rsi": 2,
        "ma": 1,
        "heikin_ashi": 1,
        "stochastic": 1,
        "ema_crossover": 0,
        "breakout": 0
    },
    "best_days": ["Thursday", "Wednesday"],
    "avoid_days": ["Wednesday"]
}
```

### USDJPY (USD/JPY)

```python
PAIR_STRATEGIES["USDJPY"] = {
    "timeframe": "4h",
    "ma_fast": 9,
    "ma_slow": 21,
    "breakout_lookback": 10,
    "rsi_oversold": 20,
    "rsi_overbought": 80,
    "ema_fast": 9,
    "ema_slow": 21,
    "ema_trend": 100,
    "weights": {
        "ema_crossover": 2,
        "ma": 1,
        "heikin_ashi": 1,
        "breakout": 1,
        "stochastic": 1
    },
    "best_days": ["Monday", "Wednesday"],
    "avoid_days": ["Friday"]
}
```

## Day-of-Week Filters

| Pair | Best Days | Avoid Days |
|------|-----------|------------|
| XAUUSD | Thursday, Friday | Monday |
| GBPJPY | Thursday, Wednesday | Wednesday |
| USDJPY | Monday, Wednesday | Friday |

**Logic:** Strategies perform differently on different days. Filters avoid low-probability days.

## Strategy Confluence

The bot runs all active strategies for a pair and checks if they agree:

```
Confluence Score = (Strategies Agreeing) / (Active Strategies) × 3
```

- **Score 3/3:** All strategies agree — highest confidence
- **Score 2/3:** Most strategies agree — moderate confidence
- **Score 1/3:** Few strategies agree — low confidence
- **Score 0/3:** No strategies agree — no trade

**Minimum Required:** 2/3 strategies must agree for a signal to be sent.

## Adding a New Strategy

1. Create detection function in `strategies.py`
2. Return dataclass with `direction`, `strength`, `bars_since_cross`
3. Add to `PAIR_STRATEGIES` weights for each pair
4. Backtest on 3+ years of data
5. Only add if PF > 1.5 and trades > 20

## Backtest Methodology

- **Data:** 3.5 years daily candles (Jan 2023 — Jul 2026)
- **Source:** yfinance
- **Entry:** 1% take profit or 0.5% stop loss
- **Metrics:** Win Rate, Profit Factor, Total Return
- **Validation:** Cross-checked with Dukascopy data (when available)
