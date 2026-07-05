"""
Telegram Bot Commands — User-facing command handlers.

Commands:
- /start     — Register user, show welcome message
- /subscribe — Show subscription plans and payment link
- /status    — Show current tier, signals used, license info
- /stats     — Show bot performance stats (public)
- /key       — Activate a license key
- /help      — Show help message
"""

import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from user_manager import UserManager
from subscriptions import get_tier_limits, generate_license_key, TIER_DURATIONS

logger = logging.getLogger(__name__)

# Initialize user manager
user_mgr = UserManager()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — register user and show welcome."""
    user = update.effective_user
    user_data = user_mgr.register_user(str(user.id), user.username)

    tier = user_mgr.get_user_tier(str(user.id))
    limits = get_tier_limits(tier)

    welcome = f"""Welcome to *TradeKnox* — SMC Trading Signals

Hey {user.first_name}! I deliver Smart Money Concept-based signals for forex and gold.

*What I scan:*
- XAUUSD, EURUSD, GBPUSD, USDJPY, GBPJPY
- Market structure, order blocks, FVGs, Fibonacci
- London, NY, and Overlap sessions only

*Your plan:* `{tier.upper()}`
- Signals per day: {limits['signals_per_day']}
- Delivery delay: {limits['delay_minutes']} minutes

*Commands:*
/subscribe — Upgrade to Pro or VIP
/status — Check your account
/stats — Bot performance
/key — Activate a license key
/help — Show this message"""

    await update.message.reply_text(welcome, parse_mode="Markdown")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe — show subscription plans."""
    user_id = str(update.effective_user.id)
    current_tier = user_mgr.get_user_tier(user_id)

    keyboard = [
        [
            InlineKeyboardButton("Pro — $29/mo", callback_data="subscribe_pro"),
            InlineKeyboardButton("VIP — $49/mo", callback_data="subscribe_vip"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"""*Upgrade Your Signals*

*Current plan:* `{current_tier.upper()}`

| Feature | Free | Pro | VIP |
|---|---|---|---|
| Signals/day | 3 | Unlimited | Unlimited |
| Delay | 15 min | Instant | Instant |
| Risk mgmt | - | - | Yes |
| Course | - | - | Yes |

*Pro — $29/mo*
Unlimited signals, instant delivery

*VIP — $49/mo*
Everything in Pro + risk management alerts + "SMC Trading Blueprint" course

Choose a plan to get started:"""

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription button clicks."""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    tier = query.data.replace("subscribe_", "")

    if tier not in ("pro", "vip"):
        return

    # Generate license key directly (simplified — no Stripe yet)
    key = generate_license_key(user_id, tier, TIER_DURATIONS[tier])
    success, message = user_mgr.activate_license(user_id, key)

    if success:
        await query.edit_message_text(
            f"Activated!\n\n"
            f"Your `{tier.upper()}` license:\n"
            f"`{key}`\n\n"
            f"Use /status to verify your plan.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(f"Error: {message}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status — show user's current status."""
    user_id = str(update.effective_user.id)
    stats = user_mgr.get_user_stats(user_id)

    if not stats.get("registered"):
        await update.message.reply_text("Send /start to register first.")
        return

    tier = stats["tier"]
    limits = get_tier_limits(tier)

    text = f"""*Account Status*

*User:* @{stats['username'] or 'N/A'}
*Plan:* `{tier.upper()}`
*Signals today:* {stats['signals_used_today']}/{stats['signals_limit']}
*Delivery delay:* {stats['delay_minutes']} minutes
*Joined:* {stats['joined_at'][:10] if stats['joined_at'] else 'N/A'}

Use /subscribe to upgrade."""

    await update.message.reply_text(text, parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats — show bot performance (public)."""
    from signal_output import TradeDatabase

    db = TradeDatabase("trades.db")
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


async def key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /key — activate a license key."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/key YOUR-LICENSE-KEY`\n\n"
            "Get a key after purchasing a plan with /subscribe",
            parse_mode="Markdown"
        )
        return

    key = context.args[0]
    user_id = str(update.effective_user.id)

    success, message = user_mgr.activate_license(user_id, key)

    if success:
        await update.message.reply_text(f"License activated!\n\n{message}")
    else:
        await update.message.reply_text(f"Activation failed:\n\n{message}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help — show help message."""
    text = """*TradeKnox Commands*

/start — Register and see welcome
/subscribe — View plans and upgrade
/status — Your account status
/stats — Bot performance stats
/key — Activate a license key
/help — This message

*About TradeKnox:*
We use Smart Money Concepts (market structure, order blocks, fair value gaps, Fibonacci) to generate high-confidence trading signals for forex and gold.

_Signals are not financial advice. Trade at your own risk._"""

    await update.message.reply_text(text, parse_mode="Markdown")
