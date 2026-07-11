"""
Telegram Bot Commands — User-facing command handlers.

Commands:
- /start     — Register user, show welcome message
- /status    — Show account status
- /stats     — Show bot performance stats (public)
- /help      — Show help message
- /portfolio — Equity curve and stats
- /strategies — Performance by strategy
- /pairs     — Performance by pair
- /regimes   — Performance by market regime
- /drawdown  — Max drawdown info
- /history   — Recent trade history
"""

import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from user_manager import UserManager

logger = logging.getLogger(__name__)

# Initialize user manager
user_mgr = UserManager()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — register user and show welcome."""
    user = update.effective_user
    user_mgr.register_user(str(user.id), user.username)

    welcome = f"""Welcome to *TradeKnox* — SMC + False Breakout Signals

Hey {user.first_name}! I deliver professional trading signals for forex and gold.

*What I scan:*
- 8 pairs: XAUUSD, GBPJPY, EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD
- Smart Money Concepts: market structure, order blocks, FVGs, Fibonacci
- False Breakout Trap: reversal rejections at swing levels
- London, NY, and Overlap sessions only

*Your account:* Unlimited signals, instant delivery, $0 forever

*Commands:*
/status — Your account info
/stats — Bot performance
/help — Show this message

_Every signal is tracked. Full transparency._"""

    await update.message.reply_text(welcome, parse_mode="Markdown")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe — bot is 100% free."""
    text = """*TradeKnox is 100% Free*

No subscriptions. No paid tiers. No license keys.

Unlimited signals • Instant delivery • 8 pairs • SMC + False Breakout

Just /start and you're in. All features unlocked.

Use /stats to see performance or /status for your account."""

    await update.message.reply_text(text, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status — show user's current status."""
    user_id = str(update.effective_user.id)
    stats = user_mgr.get_user_stats(user_id)

    if not stats.get("registered"):
        await update.message.reply_text("Send /start to register first.")
        return

    joined = stats['joined_at'][:10] if stats['joined_at'] else 'N/A'
    username = stats['username'] or 'not set'

    text = f"""*Account Status*

*User:* @{username}
*Plan:* Unlimited (Free)
*Signals today:* Unlimited
*Delivery:* Instant
*Joined:* {joined}

_Every signal is tracked._"""

    await update.message.reply_text(text, parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats — show bot performance (public)."""
    from config import CONFIG
    from signal_output import TradeDatabase

    db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    stats = db.get_performance_stats(days=30)

    if stats["total_trades"] == 0:
        await update.message.reply_text("No signals sent yet. Stay tuned!")
        return

    text = f"""*TradeKnox Performance*

*Period:* Last 30 days
*Total signals:* {stats['total_trades']}
*Wins:* {stats['wins']}
*Losses:* {stats['losses']}
*Win rate:* {stats['win_rate']}%
*Avg R:R:* 1:{stats['avg_rr']}
*Best session:* {stats['best_session']}

_Past performance does not guarantee future results._"""

    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help — show help message."""
    text = """*TradeKnox Commands*

/start — Register and see welcome
/status — Your account info
/stats — Bot performance stats
/history — Recent trade history
/portfolio — Equity curve and stats
/strategies — Performance by strategy
/pairs — Performance by pair
/regimes — Performance by market regime
/drawdown — Max drawdown info
/help — This message

*About TradeKnox:*
We use Smart Money Concepts (market structure, order blocks, fair value gaps, Fibonacci) plus False Breakout Trap reversals to generate high-confidence trading signals for forex and gold.

*100% Free. 100% Transparent.*
Every signal is tracked. Full track record available.

_Signals are not financial advice. Trade at your own risk._"""

    await update.message.reply_text(text, parse_mode="Markdown")


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /portfolio — show equity curve and stats."""
    from config import CONFIG
    from signal_output import TradeDatabase

    db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    history = db.get_portfolio_history(days=30)
    stats = db.get_performance_stats(days=30)

    if not history and stats["total_trades"] == 0:
        await update.message.reply_text("No portfolio data yet. Signals will be tracked as they execute.")
        return

    if history:
        latest = history[-1]
        equity = latest["equity"]
        drawdown = latest["drawdown_pct"]
    else:
        equity = CONFIG.ACCOUNT_BALANCE
        drawdown = 0

    text = f"""*Portfolio Dashboard*

*Current Equity:* ${equity:,.2f}
*Drawdown:* {drawdown:.2f}%
*Starting Balance:* ${CONFIG.ACCOUNT_BALANCE:,.2f}

*Performance (30 days):*
- Total signals: {stats['total_trades']}
- Wins: {stats['wins']}
- Losses: {stats['losses']}
- Win rate: {stats['win_rate']}%
- Avg R:R: 1:{stats['avg_rr']}

_Equity curve updated with each trade._"""

    await update.message.reply_text(text, parse_mode="Markdown")


async def strategies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /strategies — show performance by strategy."""
    from config import CONFIG
    from signal_output import TradeDatabase

    db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    stats = db.get_strategy_stats(days=30)

    if not stats:
        await update.message.reply_text("No strategy data yet. Signals will be tracked as they execute.")
        return

    text = "*Strategy Performance (30 days)*\n\n"

    for strat, data in sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True):
        emoji = "🔥" if data["win_rate"] >= 65 else ("✅" if data["win_rate"] >= 55 else "⚠️")
        text += f"{emoji} *{strat}*: {data['wins']}W / {data['losses']}L ({data['win_rate']}%)\n"

    text += "\n_Strategies ranked by win rate._"

    await update.message.reply_text(text, parse_mode="Markdown")


async def pairs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pairs — show performance by pair."""
    from config import CONFIG
    from signal_output import TradeDatabase

    db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    stats = db.get_pair_stats(days=30)

    if not stats:
        await update.message.reply_text("No pair data yet. Signals will be tracked as they execute.")
        return

    text = "*Pair Performance (30 days)*\n\n"

    for pair, data in sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True):
        emoji = "🔥" if data["win_rate"] >= 65 else ("✅" if data["win_rate"] >= 55 else "⚠️")
        text += f"{emoji} *{pair}*: {data['wins']}W / {data['losses']}L ({data['win_rate']}%)\n"

    text += "\n_Pairs ranked by win rate._"

    await update.message.reply_text(text, parse_mode="Markdown")


async def regimes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /regimes — show performance by market regime."""
    from config import CONFIG
    from signal_output import TradeDatabase

    db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    stats = db.get_regime_stats(days=30)

    if not stats:
        await update.message.reply_text("No regime data yet. Signals will be tracked as they execute.")
        return

    text = "*Regime Performance (30 days)*\n\n"

    regime_emojis = {
        "TRENDING": "📈",
        "RANGING": "📊",
        "VOLATILE": "⚡",
        "QUIET": "😴",
        "UNKNOWN": "❓"
    }

    for regime, data in sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True):
        emoji = regime_emojis.get(regime, "❓")
        text += f"{emoji} *{regime}*: {data['wins']}W / {data['losses']}L ({data['win_rate']}%)\n"

    text += "\n_Regimes ranked by win rate._"

    await update.message.reply_text(text, parse_mode="Markdown")


async def drawdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /drawdown — show max drawdown info."""
    from config import CONFIG
    from signal_output import TradeDatabase

    db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    dd = db.get_max_drawdown(days=30)

    if dd["peak_equity"] == 0:
        await update.message.reply_text("No drawdown data yet. Signals will be tracked as they execute.")
        return

    text = f"""*Drawdown Report*

*Peak Equity:* ${dd['peak_equity']:,.2f}
*Max Drawdown:* {dd['max_drawdown']:.2f}%
*Current Drawdown:* {dd['current_drawdown']:.2f}%

_Drawdown = distance from peak equity._"""

    await update.message.reply_text(text, parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history — show recent trade history."""
    from config import CONFIG
    from signal_output import TradeDatabase
    from signal_output import format_price

    db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    trades = db.get_recent_trades(limit=10)

    if not trades:
        await update.message.reply_text("No trade history yet. Signals will appear here as they execute.")
        return

    text = "*Recent Trades*\n\n"

    for t in trades:
        symbol = t["symbol"]
        direction = t["direction"].upper()
        entry = format_price(t["entry"], symbol)
        sl = format_price(t["stop_loss"], symbol)
        opened = t["opened_at"][:16].replace("T", " ") if t["opened_at"] else "?"

        if t["status"] == "open":
            status = "OPEN"
        elif t["result"] == "win":
            status = "WIN"
        elif t["result"] == "loss":
            status = "LOSS"
        else:
            status = "CLOSED"

        strat = t.get("strategy_used") or "smc"
        text += f"*{symbol}* {direction} — {status}\n"
        text += f"Entry: `{entry}` SL: `{sl}` | {strat.upper()}\n"
        text += f"Opened: {opened}\n\n"

    text += "_Showing last 10 trades._"

    await update.message.reply_text(text, parse_mode="Markdown")