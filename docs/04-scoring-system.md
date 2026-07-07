# 04 — Scoring System

## Overview

Every signal goes through a scoring system that assigns **0-20 points** across 6 categories. Signals must score **at least 11/20 (55% confidence)** to be sent.

**Why scoring?** Not all signals are equal. Scoring filters out weak setups and only sends high-confidence trades.

## Score Categories

| Category | Max Points | Weight |
|----------|------------|--------|
| Market Structure | 5 | 25% |
| Entry Zone | 4 | 20% |
| Indicators | 3 | 15% |
| Strategy Confluence | 3 | 15% |
| Session Timing | 3 | 15% |
| News Clear | 2 | 10% |
| **Total** | **20** | **100%** |

## Category Breakdown

### 1. Market Structure (0-5 points)

The strongest signal component. Trend alignment is worth 2 points alone.

| Condition | Points |
|-----------|--------|
| Trend alignment (buy in uptrend, sell in downtrend) | +2 |
| Break of Structure (BOS) in trade direction | +2 |
| Change of Character (CHoCH) in trade direction | +1 |
| Price in discount zone (buy) or premium zone (sell) | +1 |
| **Maximum** | **5** |

**Example:**
```
BUY signal in BULLISH trend with BOS confirmation:
  Trend aligned:     +2
  BOS confirmed:     +2
  Discount zone:     +1
  Total:             5/5
```

### 2. Entry Zone (0-4 points)

Confirms the entry location is valid.

| Condition | Points |
|-----------|--------|
| Order Block present (strength ≥ 2) | +2 |
| Order Block present (strength 1) | +1 |
| Fair Value Gap (FVG) present | +1 |
| Fibonacci confluence (0.5, 0.618, 0.786) | +1 |
| Candlestick confirmation pattern | +1 |
| **Maximum** | **4** |

**Example:**
```
Entry at strong Order Block with FVG:
  Strong OB:         +2
  FVG present:       +1
  Total:             3/4
```

### 3. Indicators (0-3 points)

Technical indicator confluence.

| Condition | Points |
|-----------|--------|
| RSI signal matches trade direction | +1 |
| RSI divergence present | +1 |
| EMA bias matches trade direction | +1 |
| Volume elevated (RVOL > 1.2) | +1 |
| **Maximum** | **3** |

**Example:**
```
BUY signal with RSI bullish + EMA bullish:
  RSI signal:        +1
  EMA bias:          +1
  Total:             2/3
```

### 4. Strategy Confluence (0-3 points)

How many strategies agree with the trade direction.

| Condition | Points |
|-----------|--------|
| All active strategies agree | +3 |
| Most strategies agree | +2 |
| Few strategies agree | +1 |
| No strategies agree | 0 |
| **Maximum** | **3** |

**Calculation:**
```python
confluence_score = round((strategies_agreeing / total_active_strategies) * 3)
```

**Example:**
```
XAUUSD with 3 active strategies (Breakout, MA, EMA Crossover):
  Breakout:    bullish ✓
  MA:          bullish ✓
  EMA:         bullish ✓
  Score:       3/3
```

### 5. Session Timing (0-3 points)

Trade timing based on market sessions.

| Session | Points |
|---------|--------|
| Overlap (London + NY) | 3 |
| London | 2 |
| New York | 2 |
| Asia | 1 |
| Dead Zone | 0 |
| **Maximum** | **3** |

**Sessions (UTC):**
- Asia: 00:00-08:00
- London: 07:00-12:00
- New York: 12:00-21:00
- Overlap: 12:00-16:00

### 6. News Clear (0-2 points)

Only awarded when news API is configured.

| Condition | Points |
|-----------|--------|
| No high-impact news within 30min | +2 |
| News API not configured | 0 |
| High-impact news within 30min | 0 |
| **Maximum** | **2** |

**Why 0 when not configured?** Prevents always getting 2 free points. Honest scoring.

## Threshold Gate

```python
passed = (total >= MIN_SCORE_THRESHOLD and
          confidence >= MIN_CONFIDENCE_PCT)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| MIN_SCORE_THRESHOLD | 11 | Minimum points to pass |
| MIN_CONFIDENCE_PCT | 55.0 | Minimum confidence percentage |

**Logic:**
- Score ≥ 11 AND confidence ≥ 55% → **PASS** (signal sent)
- Score < 11 OR confidence < 55% → **REJECT** (no signal)

## Score Examples

### High-Quality Signal (16/20)

```
Market Structure:    5/5  (trend + BOS + discount)
Entry Zone:          4/4  (strong OB + FVG + Fib + candle)
Indicators:          2/3  (RSI + EMA)
Strategy Confluence: 3/3  (all strategies agree)
Session Timing:      2/3  (London session)
News Clear:          0/2  (not configured)
─────────────────────────
Total:              16/20 (80% confidence) → PASS ✓
```

### Medium Signal (12/20)

```
Market Structure:    3/5  (trend only)
Entry Zone:          2/4  (OB present)
Indicators:          2/3  (RSI + volume)
Strategy Confluence: 2/3  (most agree)
Session Timing:      3/3  (overlap)
News Clear:          0/2  (not configured)
─────────────────────────
Total:              12/20 (60% confidence) → PASS ✓
```

### Weak Signal (8/20)

```
Market Structure:    1/5  (flat trend)
Entry Zone:          1/4  (FVG only)
Indicators:          1/3  (RSI only)
Strategy Confluence: 1/3  (few agree)
Session Timing:      2/3  (London)
News Clear:          0/2  (not configured)
─────────────────────────
Total:               8/20 (40% confidence) → REJECT ✗
```

## Reject Reasons

When a signal is rejected, the bot logs the reason:

| Reason | Description |
|--------|-------------|
| Score X/20 below threshold (11) | Total score too low |
| Confidence X% below minimum (55%) | Confidence too low |
| News blackout active | High-impact event nearby |
| Max trades reached | Daily limit hit |
| Wrong session | Outside allowed sessions |

## Modifying Thresholds

In `config.py`:

```python
MIN_SCORE_THRESHOLD: int = 11    # Change to adjust sensitivity
MIN_CONFIDENCE_PCT: float = 55.0 # Change to adjust confidence
```

**Trade-off:**
- **Lower threshold (e.g., 9):** More signals, lower quality
- **Higher threshold (e.g., 13):** Fewer signals, higher quality

## Code Reference

Main scoring function: `scoring_engine.py:score_signal()`

```python
def score_signal(structure, entry_setup, indicator_signal,
                 session, news_clear, config, strategy_confluence):
    """
    Returns SignalScore with:
    - total: int (0-20)
    - confidence_pct: float (0-100)
    - passed: bool
    - reject_reason: str
    """
```
