# 05 — Risk Management

## Overview

Every signal includes risk management: position sizing, stop loss, take profit levels, and risk-reward validation. The goal is to protect capital while maximizing returns.

## Core Rules

| Rule | Value | Description |
|------|-------|-------------|
| Max Risk per Trade | 1% | Never risk more than 1% of account |
| Min R:R Ratio | 1.5:1 | Minimum risk-reward to validate |
| Max Trades per Day | 5 | Prevent overtrading |
| Max Trades per Session | 3 | Prevent concentration |
| ATR SL Multiplier | 1.5x | Stop loss distance |
| ATR TP1 Multiplier | 1.5x | First take profit |
| ATR TP2 Multiplier | 2.5x | Second take profit |
| ATR TP3 Multiplier | 3.5x | Third take profit |

## Position Sizing Formula

```
Lots = (Account Balance × Risk%) / (SL Distance × Pip Value)
```

### For Gold (XAUUSD):

```python
risk_amount = account_balance × (risk_pct / 100)
sl_distance = abs(entry - stop_loss)
pips = sl_distance  # Gold: 1 point = $1 per lot
pip_value = 100     # $100 per lot per point

lots = risk_amount / (pips * pip_value)
```

### For Forex (GBPJPY, USDJPY):

```python
risk_amount = account_balance × (risk_pct / 100)
sl_distance = abs(entry - stop_loss)
pips = sl_distance × 10000  # 4-decimal forex
pip_value = 10              # $10 per pip per standard lot

lots = risk_amount / (pips * pip_value)
```

## Example Calculations

### XAUUSD (Gold)

```
Account:     $10,000
Risk:        1% = $100
Entry:       2,350.00
Stop Loss:   2,345.00
SL Distance: 5.00 points

Lots = $100 / (5.00 × $100) = 0.20 lots
Risk Amount: $100
```

### GBPJPY

```
Account:     $10,000
Risk:        1% = $100
Entry:       192.500
Stop Loss:   192.000
SL Distance: 0.500 = 500 pips

Lots = $100 / (500 × $10) = 0.02 lots
Risk Amount: $100
```

## Take Profit Levels

Each signal includes 3 take profit levels:

| Level | ATR Multiplier | Purpose |
|-------|----------------|---------|
| TP1 | 1.5x ATR | Partial profit (50% close) |
| TP2 | 2.5x ATR | Remaining profit (25% close) |
| TP3 | 3.5x ATR | Runner (25% close) |

### Example (XAUUSD)

```
ATR (14):    15.00
Entry:       2,350.00

TP1: 2,350.00 + (15.00 × 1.5) = 2,372.50
TP2: 2,350.00 + (15.00 × 2.5) = 2,387.50
TP3: 2,350.00 + (15.00 × 3.5) = 2,402.50

SL:  2,350.00 - (15.00 × 1.5) = 2,327.50
```

## Risk-Reward Validation

```python
rr_tp1 = abs(tp1 - entry) / abs(entry - stop_loss)
```

| R:R Ratio | Verdict |
|-----------|---------|
| ≥ 1.5 | ✅ Valid |
| < 1.5 | ❌ Rejected |

**Why 1.5 minimum?** Ensures potential profit justifies the risk.

## Max Trades Enforcement

### Per Day

```python
if trades_today >= MAX_TRADES_PER_DAY:
    reject("Max trades reached")
```

| Limit | Value |
|-------|-------|
| Max Trades per Day | 5 |
| Max Trades per Session | 3 |

### Per Session

```python
if trades_this_session >= MAX_TRADES_PER_SESSION:
    reject("Session limit reached")
```

## Risk Profile Output

Each signal generates a `RiskProfile`:

```python
@dataclass
class RiskProfile:
    stop_loss: float      # Exit price if wrong
    tp1: float           # First take profit
    tp2: float           # Second take profit
    tp3: float           # Third take profit
    rr_tp1: float        # R:R to TP1
    rr_tp2: float        # R:R to TP2
    rr_tp3: float        # R:R to TP3
    position_size: float  # Lots to trade
    risk_amount: float    # Dollar amount at risk
    valid: bool          # Passed validation
```

## Signal Output

Signals include full risk info:

```
📊 XAUUSD BUY @ 2,350.00

🎯 Take Profit:
   TP1: 2,372.50 (1.5:1)
   TP2: 2,387.50 (2.5:1)
   TP3: 2,402.50 (3.5:1)

🛑 Stop Loss: 2,327.50

💰 Risk Management:
   Position: 0.20 lots
   Risk: $100 (1%)
   Account: $10,000
```

## Configuration

In `config.py`:

```python
ACCOUNT_BALANCE: float = 10000      # Account size
DEFAULT_RISK_PCT: float = 1.0       # Risk per trade (%)
MIN_RR_RATIO: float = 1.5          # Minimum R:R
ATR_SL_MULTIPLIER: float = 1.5     # SL distance
ATR_TP1_MULT: float = 1.5          # TP1 distance
ATR_TP2_MULT: float = 2.5          # TP2 distance
ATR_TP3_MULT: float = 3.5          # TP3 distance
MAX_TRADES_PER_SESSION: int = 3
MAX_TRADES_PER_DAY: int = 5
```

## Code Reference

Main risk function: `scoring_engine.py:build_risk_profile()`

```python
def build_risk_profile(entry, stop_loss, tp1, tp2, tp3,
                       account_balance, config):
    """
    Returns RiskProfile with:
    - position_size: float
    - risk_amount: float
    - rr_tp1, rr_tp2, rr_tp3: float
    - valid: bool
    """
```

Position sizing: `scoring_engine.py:calculate_position_size()`

```python
def calculate_position_size(account_balance, risk_pct,
                           entry, stop_loss, pip_value=0.1):
    """
    Returns position size in lots.
    Formula: (Balance × Risk%) / (SL Distance × Pip Value)
    """
```
