"""
Layers 7, 10, 14: Signal Output, Trade Management & Performance Analytics
The product layer — this is what users actually see and interact with.
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Layer 10: Signal Output Formatter
# ──────────────────────────────────────────────────────────────────────────────

DIRECTION_EMOJI = {"buy": "🟢", "sell": "🔴"}
CONFIDENCE_EMOJI = {range(80, 101): "🔥", range(65, 80): "✅", range(0, 65): "⚠️"}


def _conf_emoji(pct: float) -> str:
    for r, em in CONFIDENCE_EMOJI.items():
        if int(pct) in r:
            return em
    return "✅"


def format_price(price: float, symbol: str) -> str:
    """Format price with appropriate decimal places per instrument."""
    if symbol in ("XAUUSD",):
        return f"{price:.2f}"
    elif symbol in ("USDJPY", "GBPJPY"):
        return f"{price:.3f}"
    else:
        return f"{price:.5f}"


def format_signal_message(symbol: str, direction: str, entry: float,
                           stop_loss: float, tp1: float, tp2: float, tp3: float,
                           rr1: float, rr2: float, rr3: float,
                           confidence: float, score: int, max_score: int,
                           session: str, reason: str, expiry_hours: int = 4,
                           timeframe: str = "1h") -> str:
    """
    Format a clean, professional Telegram signal message.
    Uses MarkdownV2 formatting.
    """
    p = lambda x: format_price(x, symbol)
    dir_upper = direction.upper()
    emoji = DIRECTION_EMOJI[direction]
    conf_em = _conf_emoji(confidence)

    risk = abs(entry - stop_loss)
    # Calculate pip/point values for display
    sl_pts = abs(entry - stop_loss)
    tp1_pts = abs(tp1 - entry)
    tp2_pts = abs(tp2 - entry)
    tp3_pts = abs(tp3 - entry)

    session_display = {
        "overlap": "London–NY Overlap 🏆",
        "london": "London Session",
        "new_york": "New York Session",
        "asia": "Asian Session",
        "dead_zone": "Off-Hours",
    }.get(session, session.replace("_", " ").title())

    now_utc = datetime.now(timezone.utc)
    expiry_time = now_utc + timedelta(hours=expiry_hours)
    expiry_str = expiry_time.strftime("%H:%M UTC")

    msg = f"""{emoji} *{dir_upper} {symbol}*  {conf_em}
━━━━━━━━━━━━━━━━━━━━━━

📍 *Entry:*      `{p(entry)}`
🛑 *Stop Loss:*  `{p(stop_loss)}`  _\\(\\-{sl_pts:.2f}\\)_

🎯 *TP1:*   `{p(tp1)}`  _\\+{tp1_pts:.2f}_ \\| RR 1:{rr1}
🎯 *TP2:*   `{p(tp2)}`  _\\+{tp2_pts:.2f}_ \\| RR 1:{rr2}
🎯 *TP3:*   `{p(tp3)}`  _\\+{tp3_pts:.2f}_ \\| RR 1:{rr3}

━━━━━━━━━━━━━━━━━━━━━━
{conf_em} *Confidence:*  {confidence}%  \\({score}/{max_score}\\)
⏰ *Session:*    {session_display}
📊 *Timeframe:*  {timeframe}
⌛ *Expires:*    {expiry_str}

💡 *Reason:*
_{reason}_

━━━━━━━━━━━━━━━━━━━━━━
⚠️ _Manage risk\\. Move SL to breakeven after TP1\\._
_This is not financial advice\\._"""

    return msg


def format_tp_hit_alert(symbol: str, direction: str, tp_num: int,
                         tp_price: float, remaining_signal_id: str) -> str:
    """Alert when a TP level is hit."""
    return (
        f"✅ *TP{tp_num} HIT\\!* {symbol}\n"
        f"Price reached `{format_price(tp_price, symbol)}`\n\n"
        f"📌 *Action:* Move SL to breakeven now\\.\n"
        f"🎯 TP{tp_num + 1} still open\\."
    )


def format_sl_hit_alert(symbol: str, direction: str, sl_price: float) -> str:
    """Alert when SL is hit."""
    return (
        f"🛑 *SL HIT* {symbol}\n"
        f"Stopped out at `{format_price(sl_price, symbol)}`\n\n"
        f"_Review the setup\\. Next signal incoming when conditions realign\\._"
    )


def format_performance_report(stats: Dict) -> str:
    """Monthly performance summary for the channel."""
    wr = stats.get("win_rate", 0)
    total = stats.get("total_trades", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    avg_rr = stats.get("avg_rr", 0)
    best_session = stats.get("best_session", "N/A")
    month = stats.get("month", datetime.now(timezone.utc).strftime("%B %Y"))

    emoji = "🔥" if wr >= 65 else ("✅" if wr >= 55 else "⚠️")

    return f"""{emoji} *Monthly Performance Report*
📅 *{month}*
━━━━━━━━━━━━━━━━━━━━━━

📊 *Total Signals:*  {total}
✅ *Wins:*           {wins}
❌ *Losses:*         {losses}
🎯 *Win Rate:*       {wr:.1f}%

📈 *Avg RR:*         1:{avg_rr:.2f}
🏆 *Best Session:*   {best_session}

━━━━━━━━━━━━━━━━━━━━━━
_Powered by structure\\-first analysis\\._"""


# ──────────────────────────────────────────────────────────────────────────────
# Layer 7: Trade Management & Database
# ──────────────────────────────────────────────────────────────────────────────

class TradeDatabase:
    """SQLite-backed trade log for performance tracking and management."""

    def __init__(self, db_path: str = "trades.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id          TEXT PRIMARY KEY,
                        symbol      TEXT NOT NULL,
                        direction   TEXT NOT NULL,
                        entry       REAL,
                        stop_loss   REAL,
                        tp1         REAL,
                        tp2         REAL,
                        tp3         REAL,
                        rr_tp1      REAL,
                        confidence  REAL,
                        score       INTEGER,
                        session     TEXT,
                        reason      TEXT,
                        status      TEXT DEFAULT 'open',
                        result      TEXT,
                        actual_rr   REAL,
                        opened_at   TEXT,
                        closed_at   TEXT,
                        tp1_hit     INTEGER DEFAULT 0,
                        tp2_hit     INTEGER DEFAULT 0,
                        tp3_hit     INTEGER DEFAULT 0,
                        be_moved    INTEGER DEFAULT 0,
                        strategy_used TEXT,
                        regime_at_entry TEXT,
                        equity_after REAL,
                        drawdown_pct REAL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_signals (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id     TEXT NOT NULL,
                        signal_id   TEXT NOT NULL,
                        received_at TEXT NOT NULL,
                        tier_at_time TEXT DEFAULT 'free'
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        date        TEXT NOT NULL,
                        equity      REAL NOT NULL,
                        drawdown_pct REAL,
                        trades_today INTEGER DEFAULT 0,
                        wins_today  INTEGER DEFAULT 0,
                        losses_today INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database init failed: {e}")

    def save_trade(self, signal_id: str, symbol: str, direction: str,
                   entry: float, sl: float, tp1: float, tp2: float, tp3: float,
                   rr1: float, confidence: float, score: int,
                   session: str, reason: str, strategy_used: str = None,
                   regime_at_entry: str = None):
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO trades
                    (id, symbol, direction, entry, stop_loss, tp1, tp2, tp3,
                     rr_tp1, confidence, score, session, reason, status, opened_at,
                     strategy_used, regime_at_entry)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'open',?,?,?)
                """, (signal_id, symbol, direction, entry, sl, tp1, tp2, tp3,
                      rr1, confidence, score, session, reason,
                      datetime.now(timezone.utc).isoformat(),
                      strategy_used, regime_at_entry))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to save trade {signal_id}: {e}")

    def update_tp_hit(self, signal_id: str, tp_num: int):
        try:
            col = f"tp{tp_num}_hit"
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute(f"UPDATE trades SET {col}=1 WHERE id=?", (signal_id,))
                if tp_num == 1:
                    conn.execute("UPDATE trades SET be_moved=1 WHERE id=?", (signal_id,))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to update TP hit for {signal_id}: {e}")

    def close_trade(self, signal_id: str, result: str, actual_rr: float):
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                    UPDATE trades SET status='closed', result=?, actual_rr=?, closed_at=?
                    WHERE id=?
                """, (result, actual_rr, datetime.now(timezone.utc).isoformat(), signal_id))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to close trade {signal_id}: {e}")

    def get_open_trades(self) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM trades WHERE status='open' ORDER BY opened_at DESC"
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get open trades: {e}")
            return []

    def get_performance_stats(self, days: int = 30) -> Dict:
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                rows = conn.execute("""
                    SELECT result, session, actual_rr FROM trades
                    WHERE status='closed' AND opened_at >= ?
                """, (cutoff,)).fetchall()

            if not rows:
                return {"total_trades": 0, "win_rate": 0, "avg_rr": 0}

            total = len(rows)
            wins = sum(1 for r in rows if r[0] == "win")
            losses = total - wins
            win_rate = (wins / total * 100) if total > 0 else 0

            rrs = [r[2] for r in rows if r[2] and r[0] == "win"]
            avg_rr = sum(rrs) / len(rrs) if rrs else 0

            session_wins = {}
            for r in rows:
                sess = r[1] or "unknown"
                if r[0] == "win":
                    session_wins[sess] = session_wins.get(sess, 0) + 1
            best_session = max(session_wins, key=session_wins.get) if session_wins else "N/A"

            return {
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 1),
                "avg_rr": round(avg_rr, 2),
                "best_session": best_session,
                "month": datetime.now(timezone.utc).strftime("%B %Y"),
            }
        except sqlite3.Error as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"total_trades": 0, "win_rate": 0, "avg_rr": 0}

    def count_trades_today(self, session: str = None) -> int:
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                if session:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM trades WHERE opened_at LIKE ? AND session=?",
                        (f"{today}%", session)
                    ).fetchone()[0]
                else:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM trades WHERE opened_at LIKE ?",
                        (f"{today}%",)
                    ).fetchone()[0]
            return count
        except sqlite3.Error as e:
            logger.error(f"Failed to count trades today: {e}")
            return 0

    def record_user_signal(self, user_id: str, signal_id: str, tier: str = "free"):
        """Record that a user received a specific signal."""
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                    INSERT INTO user_signals (user_id, signal_id, received_at, tier_at_time)
                    VALUES (?, ?, ?, ?)
                """, (user_id, signal_id, datetime.now(timezone.utc).isoformat(), tier))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to record user signal: {e}")

    def update_portfolio(self, equity: float, drawdown_pct: float = 0.0,
                        trades_today: int = 0, wins_today: int = 0, losses_today: int = 0):
        """Update daily portfolio snapshot."""
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO portfolio (date, equity, drawdown_pct, trades_today, wins_today, losses_today)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (today, equity, drawdown_pct, trades_today, wins_today, losses_today))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to update portfolio: {e}")

    def get_portfolio_history(self, days: int = 30) -> List[Dict]:
        """Get portfolio equity curve over time."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM portfolio WHERE date >= ? ORDER BY date ASC",
                    (cutoff,)
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return []

    def get_strategy_stats(self, days: int = 30) -> Dict:
        """Get performance breakdown by strategy."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                rows = conn.execute("""
                    SELECT strategy_used, result, COUNT(*) as total
                    FROM trades
                    WHERE status='closed' AND opened_at >= ? AND strategy_used IS NOT NULL
                    GROUP BY strategy_used, result
                """, (cutoff,)).fetchall()

            stats = {}
            for row in rows:
                strat = row[0]
                result = row[1]
                count = row[2]
                if strat not in stats:
                    stats[strat] = {"wins": 0, "losses": 0, "total": 0}
                stats[strat]["total"] += count
                if result == "win":
                    stats[strat]["wins"] += count
                else:
                    stats[strat]["losses"] += count

            # Calculate win rates
            for strat in stats:
                total = stats[strat]["total"]
                wins = stats[strat]["wins"]
                stats[strat]["win_rate"] = round((wins / total * 100) if total > 0 else 0, 1)

            return stats
        except sqlite3.Error as e:
            logger.error(f"Failed to get strategy stats: {e}")
            return {}

    def get_pair_stats(self, days: int = 30) -> Dict:
        """Get performance breakdown by pair."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                rows = conn.execute("""
                    SELECT symbol, result, COUNT(*) as total
                    FROM trades
                    WHERE status='closed' AND opened_at >= ?
                    GROUP BY symbol, result
                """, (cutoff,)).fetchall()

            stats = {}
            for row in rows:
                pair = row[0]
                result = row[1]
                count = row[2]
                if pair not in stats:
                    stats[pair] = {"wins": 0, "losses": 0, "total": 0}
                stats[pair]["total"] += count
                if result == "win":
                    stats[pair]["wins"] += count
                else:
                    stats[pair]["losses"] += count

            # Calculate win rates
            for pair in stats:
                total = stats[pair]["total"]
                wins = stats[pair]["wins"]
                stats[pair]["win_rate"] = round((wins / total * 100) if total > 0 else 0, 1)

            return stats
        except sqlite3.Error as e:
            logger.error(f"Failed to get pair stats: {e}")
            return {}

    def get_regime_stats(self, days: int = 30) -> Dict:
        """Get performance breakdown by market regime."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                rows = conn.execute("""
                    SELECT regime_at_entry, result, COUNT(*) as total
                    FROM trades
                    WHERE status='closed' AND opened_at >= ? AND regime_at_entry IS NOT NULL
                    GROUP BY regime_at_entry, result
                """, (cutoff,)).fetchall()

            stats = {}
            for row in rows:
                regime = row[0]
                result = row[1]
                count = row[2]
                if regime not in stats:
                    stats[regime] = {"wins": 0, "losses": 0, "total": 0}
                stats[regime]["total"] += count
                if result == "win":
                    stats[regime]["wins"] += count
                else:
                    stats[regime]["losses"] += count

            # Calculate win rates
            for regime in stats:
                total = stats[regime]["total"]
                wins = stats[regime]["wins"]
                stats[regime]["win_rate"] = round((wins / total * 100) if total > 0 else 0, 1)

            return stats
        except sqlite3.Error as e:
            logger.error(f"Failed to get regime stats: {e}")
            return {}

    def get_max_drawdown(self, days: int = 30) -> Dict:
        """Calculate maximum drawdown from portfolio history."""
        try:
            history = self.get_portfolio_history(days)
            if not history:
                return {"max_drawdown": 0, "current_drawdown": 0, "peak_equity": 0}

            peak = 0
            max_dd = 0
            for entry in history:
                equity = entry["equity"]
                if equity > peak:
                    peak = equity
                dd = ((peak - equity) / peak * 100) if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd

            current_equity = history[-1]["equity"] if history else 0
            current_dd = ((peak - current_equity) / peak * 100) if peak > 0 else 0

            return {
                "max_drawdown": round(max_dd, 2),
                "current_drawdown": round(current_dd, 2),
                "peak_equity": round(peak, 2)
            }
        except sqlite3.Error as e:
            logger.error(f"Failed to get max drawdown: {e}")
            return {"max_drawdown": 0, "current_drawdown": 0, "peak_equity": 0}


# ──────────────────────────────────────────────────────────────────────────────
# Layer 14: Performance Analytics
# ──────────────────────────────────────────────────────────────────────────────

def should_send_monthly_report(last_report_date: Optional[datetime]) -> bool:
    """Return True if it's time for the monthly report (first day of month)."""
    now = datetime.now(timezone.utc)
    if last_report_date is None:
        return now.day == 1
    return now.month != last_report_date.month and now.day == 1
