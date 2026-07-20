# 06 — Signal Pipeline

## Overview

The signal pipeline is a **12-layer system** that processes raw market data into actionable trading signals. Each layer filters, analyzes, or validates the signal before it reaches the Telegram channel.

## Pipeline Flow

```
Layer 1:  Session Filter
Layer 2:  News Blackout
Layer 3:  Max Trades Check
Layer 4:  Data Fetch
Layer 5:  Calculate Indicators
Layer 6:  Market Structure
Layer 7:  Entry Logic
Layer 8:  Strategy Confluence
Layer 9:  Scoring
Layer 10: Risk Management
Layer 11: Trade Management
Layer 12: Telegram Output
```

## Layer-by-Layer Breakdown

### Layer 1: Session Filter

**File:** `config.py:SESSIONS`  
**Purpose:** Only trade during active market sessions

```python
ALLOWED_SESSIONS = ["london", "new_york", "overlap"]
```

| Session | Hours (UTC) | Status |
|---------|-------------|--------|
| Asia | 00:00-08:00 | ❌ Blocked |
| London | 07:00-12:00 | ✅ Allowed |
| Overlap | 12:00-16:00 | ✅ Allowed (best) |
| New York | 12:00-21:00 | ✅ Allowed |
| Dead Zone | 21:00-00:00 | ❌ Blocked |

**Why:** Low liquidity outside active sessions = wider spreads, more noise.

---

### Layer 2: News Blackout

**File:** `scoring_engine.py:is_news_blackout()`  
**Purpose:** Avoid trading during high-impact economic events

```python
NEWS_BLACKOUT_BEFORE_MIN = 30  # Block 30min before
NEWS_BLACKOUT_AFTER_MIN = 15   # Block 15min after
```

**Logic:**
1. Fetch upcoming news events (ForexFactory API)
2. Check if any high-impact event affects the pair's currencies
3. Block if event is within blackout window

**When API not configured:** Returns False (no filter applied). News score = 0 (honest scoring).

---

### Layer 3: Max Trades Check

**File:** `bot.py:scan_loop()`  
**Purpose:** Prevent overtrading

```python
MAX_TRADES_PER_DAY = 5
MAX_TRADES_PER_SESSION = 3
```

**Logic:**
```python
if trades_today >= MAX_TRADES_PER_DAY:
    log("Max daily trades reached")
    return

if trades_this_session >= MAX_TRADES_PER_SESSION:
    log("Session limit reached")
    return
```

---

### Layer 4: Data Fetch

**File:** `data_layer.py:fetch_ohlcv()`  
**Purpose:** Get candle data from yfinance

```python
# Multi-timeframe data
primary_tf = "1h"      # Main analysis
confirm_tf = "15m"      # Entry confirmation
htf_tf = "4h"           # Higher timeframe
strategy_tf = "4h"      # Strategy signals
```

**Output:** OHLCV DataFrame with columns:
- `open`, `high`, `low`, `close`, `volume`
- `timestamp` (datetime index)

---

### Layer 5: Calculate Indicators

**File:** `data_layer.py:calculate_indicators()`  
**Purpose:** Compute technical indicators

| Indicator | Period | Purpose |
|-----------|--------|---------|
| ATR | 14 | Volatility, SL/TP distance |
| RSI | 14 | Overbought/oversold |
| EMA Fast | 21 | Short-term trend |
| EMA Slow | 50 | Medium-term trend |
| EMA Trend | 200 | Long-term trend |
| RVOL | 20 | Volume relative to average |

**Output:** DataFrame with indicator columns added.

---

### Layer 6: Market Structure

**File:** `market_structure.py`  
**Purpose:** Classify trend and identify key levels

```python
@dataclass
class Structure:
    trend: Trend              # BULLISH, BEARISH, FLAT
    last_bos: Optional[BOS]   # Break of Structure
    last_choch: Optional[CHoCH]  # Change of Character
    current_price_zone: str   # "premium" or "discount"
    liquidity_zones: List     # Support/resistance levels
```

**Trend Classification:**
- **BULLISH:** Higher highs, higher lows
- **BEARISH:** Lower highs, lower lows
- **FLAT:** No clear direction (ranging)

**BOS/CHoCH:**
- **BOS:** Break of previous swing high/low (trend continuation)
- **CHoCH:** Change in market structure (potential reversal)

---

### Layer 7: Entry Logic

**File:** `entry_logic.py`  
**Purpose:** Identify valid entry zones

```python
@dataclass
class EntrySetup:
    direction: str              # "buy" or "sell"
    order_block: Optional[OB]   # Order block
    fvg: Optional[FVG]          # Fair value gap
    fib_confluence: bool        # Near Fibonacci level
    candle_confirmed: bool      # Candlestick pattern
    entry_price: float          # Recommended entry
```

**Order Blocks (OB):**
- Last opposing candle before a strong move
- Institutional supply/demand zones
- Strength rated 1-3 based on displacement

**Fair Value Gaps (FVG):**
- 3-candle imbalance pattern
- Price tends to return to fill the gap
- Minimum size: 0.3x ATR

**Fibonacci Levels:**
- 0.5, 0.618, 0.786 retracement levels
- Confluence with OB/FVG increases score

---

### Layer 8: Strategy Confluence

**File:** `strategies.py:assess_strategies()`  
**Purpose:** Run all strategies and check alignment

```python
@dataclass
class StrategyConfluence:
    ma_direction: str           # MA crossover signal
    breakout_direction: str     # Breakout signal
    rsi_direction: str          # RSI extremes signal
    ema_crossover_direction: str  # EMA crossover signal
    heikin_ashi_direction: str  # Heikin Ashi signal
    stochastic_direction: str   # Stochastic signal
    confluence_score: int       # 0-3 (how many agree)
    confluence_direction: str   # Overall direction
```

**Logic:**
1. Run all active strategies for the pair
2. Count how many agree with the trade direction
3. Calculate confluence score (0-3)
4. Require minimum 2/3 agreement

---

### Layer 9: Scoring

**File:** `scoring_engine.py:score_signal()`  
**Purpose:** Score signal quality (0-20 points)

See [04 - Scoring System](04-scoring-system.md) for full breakdown.

**Categories:**
1. Market Structure (0-5)
2. Entry Zone (0-4)
3. Indicators (0-3)
4. Strategy Confluence (0-3)
5. Session Timing (0-3)
6. News Clear (0-2)

**Gate:** Score ≥ 11 AND confidence ≥ 55% → PASS

---

### Layer 10: Risk Management

**File:** `scoring_engine.py:build_risk_profile()`  
**Purpose:** Calculate position size, SL/TP, R:R

See [05 - Risk Management](05-risk-management.md) for full breakdown.

**Output:**
```python
@dataclass
class RiskProfile:
    stop_loss: float
    tp1, tp2, tp3: float
    rr_tp1, rr_tp2, rr_tp3: float
    position_size: float
    risk_amount: float
    valid: bool
```

**Validation:** R:R must be ≥ 1.5:1 to pass.

---

### Layer 11: Trade Management

**File:** `signal_output.py`  
**Purpose:** Prepare trade for delivery

**Actions:**
1. Format price for pair (2 decimals for XAUUSD, 3 for GBPJPY)
2. Calculate pip values
3. Prepare chart image
4. Log trade to SQLite database
5. Track performance metrics

---

### Layer 12: Telegram Output

**File:** `signal_output.py:send_signal()`  
**Purpose:** Deliver signal to Telegram channel

**Free Tier:**
- Blurred chart preview
- "Upgrade to Pro for full chart"
- 15-minute delay

**Pro/VIP Tier:**
- Full chart with OB/FVG/BOS overlays
- Instant delivery
- Entry, SL, TP levels

**Message Format:**
```
📊 {PAIR} {DIRECTION} @ {ENTRY}

🎯 Take Profit:
   TP1: {TP1} ({RR1}:1)
   TP2: {TP2} ({RR2}:1)
   TP3: {TP3} ({RR3}:1)

🛑 Stop Loss: {SL}

💰 Risk Management:
   Position: {LOTS} lots
   Risk: ${RISK} ({RISK_PCT}%)
   Account: ${ACCOUNT}

📈 Signal Score: {SCORE}/{MAX} ({CONFIDENCE}%)
⏱️ Session: {SESSION}
📅 Day: {DAY}
```

## Pipeline Timing

```
Total scan time: ~3-5 seconds per pair
├── Data fetch:     ~1-2s
├── Indicators:     ~0.1s
├── Structure:      ~0.2s
├── Entry logic:    ~0.3s
├── Strategies:     ~0.5s
├── Scoring:        ~0.1s
├── Risk mgmt:     ~0.1s
├── Chart render:   ~1-2s
└── Telegram send:  ~0.5s
```

## Error Handling

Each layer has try/except blocks:

```python
try:
    result = layer_function(data)
except Exception as e:
    logger.error(f"Layer X failed: {e}")
    return None  # Skip this pair
```

**Fail-safe:** If any layer fails, the pair is skipped. No partial signals are sent.

## Code Reference

Main pipeline: `bot.py:scan_loop()`

```python
async def scan_loop():
    """Main scan loop — runs every SCAN_INTERVAL_SECONDS."""
    while not _shutdown_requested:
        for pair in CONFIG.SYMBOLS:
            try:
                # Layer 1-12 here
                pass
            except Exception as e:
                logger.error(f"Scan failed for {pair}: {e}")
        
        await asyncio.sleep(CONFIG.SCAN_INTERVAL_SECONDS)
```
