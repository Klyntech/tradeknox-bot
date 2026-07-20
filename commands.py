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
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_db = None


def get_db():
    global _db
    if _db is None:
        from config import CONFIG
        from signal_output import TradeDatabase
        _db = TradeDatabase(CONFIG.TRADES_DB_PATH)
    return _db


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = update.effective_user
    name = escape(user.first_name or "there")

    text = (
        f"<b>Welcome to TradeKnox</b> — SMC + False Breakout Signals\n\n"
        f"Hey {name}! I deliver professional trading signals for forex and gold.\n\n"
        f"<b>What I scan:</b>\n"
        f"- 8 pairs: XAUUSD, GBPJPY, EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD\n"
        f"- Smart Money Concepts: market structure, order blocks, FVGs, Fibonacci\n"
        f"- False Breakout Trap: reversal rejections at swing levels\n"
        f"- London, NY, and Overlap sessions only\n\n"
        f"<b>Your account:</b> Unlimited signals, instant delivery, $0 forever\n\n"
        f"<b>Commands:</b>\n"
        f"/status — Your account info\n"
        f"/stats — Bot performance\n"
        f"/help — Show this message\n\n"
        f"<i>Every signal is tracked. Full transparency.</i>"
    )

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"start_command reply failed: {e}")
        try:
            await update.message.reply_text(
                f"Welcome to TradeKnox, {user.first_name}! Type /help to see available commands."
            )
        except Exception:
            logger.exception("Even fallback reply failed")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = update.effective_user
    username = escape(user.username or "not set")

    text = (
        f"<b>Account Status</b>\n\n"
        f"<b>User:</b> @{username}\n"
        f"<b>Plan:</b> Unlimited (Free)\n"
        f"<b>Signals today:</b> Unlimited\n"
        f"<b>Delivery:</b> Instant\n\n"
        f"<i>Every signal is tracked.</i>"
    )

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"status_command reply failed: {e}")
        try:
            await update.message.reply_text("Account status unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    db = get_db()
    stats = db.get_performance_stats(days=30)

    if stats["total_trades"] == 0:
        try:
            await update.message.reply_text("No signals sent yet. Stay tuned!")
        except Exception:
            logger.exception("stats_command empty reply failed")
        return

    text = (
        f"<b>TradeKnox Performance</b>\n\n"
        f"<b>Period:</b> Last 30 days\n"
        f"<b>Total signals:</b> {stats['total_trades']}\n"
        f"<b>Wins:</b> {stats['wins']}\n"
        f"<b>Losses:</b> {stats['losses']}\n"
        f"<b>Win rate:</b> {stats['win_rate']}%\n"
        f"<b>Avg R:R:</b> 1:{stats['avg_rr']}\n"
        f"<b>Best session:</b> {stats['best_session']}\n\n"
        f"<i>Past performance does not guarantee future results.</i>"
    )

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"stats_command reply failed: {e}")
        try:
            await update.message.reply_text("Stats unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    text = (
        f"<b>TradeKnox Commands</b>\n\n"
        f"/start — See welcome message\n"
        f"/status — Your account info\n"
        f"/stats — Bot performance stats\n"
        f"/history — Recent trade history\n"
        f"/portfolio — Equity curve and stats\n"
        f"/strategies — Performance by strategy\n"
        f"/pairs — Performance by pair\n"
        f"/regimes — Performance by market regime\n"
        f"/drawdown — Max drawdown info\n"
        f"/help — This message\n\n"
        f"<b>About TradeKnox:</b>\n"
        f"We use Smart Money Concepts (market structure, order blocks, fair value gaps, Fibonacci) "
        f"plus False Breakout Trap reversals to generate high-confidence trading signals for forex and gold.\n\n"
        f"<b>100% Free. 100% Transparent.</b>\n"
        f"Every signal is tracked. Full track record available.\n\n"
        f"<i>Signals are not financial advice. Trade at your own risk.</i>"
    )

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"help_command reply failed: {e}")
        try:
            await update.message.reply_text("Help unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    from config import CONFIG
    db = get_db()
    stats = db.get_performance_stats(days=30)

    if stats["total_trades"] == 0:
        try:
            await update.message.reply_text("No portfolio data yet. Signals will be tracked as they execute.")
        except Exception:
            logger.exception("portfolio_command empty reply failed")
        return

    text = (
        f"<b>Portfolio Dashboard</b>\n\n"
        f"<b>Performance (30 days):</b>\n"
        f"- Total signals: {stats['total_trades']}\n"
        f"- Wins: {stats['wins']}\n"
        f"- Losses: {stats['losses']}\n"
        f"- Win rate: {stats['win_rate']}%\n"
        f"- Avg R:R: 1:{stats['avg_rr']}\n\n"
        f"<b>Starting Balance:</b> ${CONFIG.ACCOUNT_BALANCE:,.2f}\n\n"
        f"<i>Every signal is tracked. Full transparency.</i>"
    )

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"portfolio_command reply failed: {e}")
        try:
            await update.message.reply_text("Portfolio unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def strategies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    db = get_db()
    stats = db.get_strategy_stats(days=30)

    if not stats:
        try:
            await update.message.reply_text("No strategy data yet. Signals will be tracked as they execute.")
        except Exception:
            logger.exception("strategies_command empty reply failed")
        return

    text = "<b>Strategy Performance (30 days)</b>\n\n"

    for strat, data in sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True):
        emoji = "🔥" if data["win_rate"] >= 65 else ("✅" if data["win_rate"] >= 55 else "⚠️")
        text += f"{emoji} <b>{escape(strat)}</b>: {data['wins']}W / {data['losses']}L ({data['win_rate']}%)\n"

    text += "\n<i>Strategies ranked by win rate.</i>"

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"strategies_command reply failed: {e}")
        try:
            await update.message.reply_text("Strategy data unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def pairs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    db = get_db()
    stats = db.get_pair_stats(days=30)

    if not stats:
        try:
            await update.message.reply_text("No pair data yet. Signals will be tracked as they execute.")
        except Exception:
            logger.exception("pairs_command empty reply failed")
        return

    text = "<b>Pair Performance (30 days)</b>\n\n"

    for pair, data in sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True):
        emoji = "🔥" if data["win_rate"] >= 65 else ("✅" if data["win_rate"] >= 55 else "⚠️")
        text += f"{emoji} <b>{escape(pair)}</b>: {data['wins']}W / {data['losses']}L ({data['win_rate']}%)\n"

    text += "\n<i>Pairs ranked by win rate.</i>"

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"pairs_command reply failed: {e}")
        try:
            await update.message.reply_text("Pair data unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def regimes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    db = get_db()
    stats = db.get_regime_stats(days=30)

    if not stats:
        try:
            await update.message.reply_text("No regime data yet. Signals will be tracked as they execute.")
        except Exception:
            logger.exception("regimes_command empty reply failed")
        return

    text = "<b>Regime Performance (30 days)</b>\n\n"

    regime_emojis = {
        "TRENDING": "📈",
        "RANGING": "📊",
        "VOLATILE": "⚡",
        "QUIET": "😴",
        "UNKNOWN": "❓"
    }

    for regime, data in sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True):
        emoji = regime_emojis.get(regime, "❓")
        text += f"{emoji} <b>{escape(regime)}</b>: {data['wins']}W / {data['losses']}L ({data['win_rate']}%)\n"

    text += "\n<i>Regimes ranked by win rate.</i>"

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"regimes_command reply failed: {e}")
        try:
            await update.message.reply_text("Regime data unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def drawdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    db = get_db()
    dd = db.get_max_drawdown(days=30)

    if dd["peak_equity"] == 0:
        try:
            await update.message.reply_text("No drawdown data yet. Signals will be tracked as they execute.")
        except Exception:
            logger.exception("drawdown_command empty reply failed")
        return

    text = (
        f"<b>Drawdown Report</b>\n\n"
        f"<b>Peak Equity:</b> ${dd['peak_equity']:,.2f}\n"
        f"<b>Max Drawdown:</b> {dd['max_drawdown']:.2f}%\n"
        f"<b>Current Drawdown:</b> {dd['current_drawdown']:.2f}%\n\n"
        f"<i>Drawdown = distance from peak equity.</i>"
    )

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"drawdown_command reply failed: {e}")
        try:
            await update.message.reply_text("Drawdown data unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    from signal_output import format_price

    db = get_db()
    trades = db.get_recent_trades(limit=10)

    if not trades:
        try:
            await update.message.reply_text("No trade history yet. Signals will appear here as they execute.")
        except Exception:
            logger.exception("history_command empty reply failed")
        return

    text = "<b>Recent Trades</b>\n\n"

    for t in trades:
        symbol = escape(t["symbol"])
        direction = t["direction"].upper()
        entry = format_price(t["entry"], t["symbol"])
        sl = format_price(t["stop_loss"], t["symbol"])
        opened = t["opened_at"][:16].replace("T", " ") if t["opened_at"] else "?"

        if t["status"] == "open":
            status = "OPEN"
        elif t["result"] == "win":
            status = "WIN"
        elif t["result"] == "loss":
            status = "LOSS"
        else:
            status = "CLOSED"

        strat = escape(t.get("strategy_used") or "smc")
        text += f"<b>{symbol}</b> {direction} — {status}\n"
        text += f"Entry: <code>{entry}</code> SL: <code>{sl}</code> | {strat.upper()}\n"
        text += f"Opened: {opened}\n\n"

    text += "<i>Showing last 10 trades.</i>"

    try:
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"history_command reply failed: {e}")
        try:
            await update.message.reply_text("History unavailable. Try again later.")
        except Exception:
            logger.exception("Even fallback reply failed")
