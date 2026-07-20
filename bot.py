"""
Main Bot Orchestrator
Ties all layers together. Runs the scan loop, fires Telegram signals,
tracks trade management, handles security/anti-leak logic,
and processes user commands.
"""

import asyncio
import hashlib
import logging
import os
import signal
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ── Graceful shutdown ────────────────────────────────────────────────────────
_shutdown_requested = False


def _handle_shutdown(signum, frame):
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name} — shutting down gracefully...")
    _shutdown_requested = True


signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGINT, _handle_shutdown)

try:
    from telegram import Bot, constants, Update
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler, ContextTypes
    )
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Running in dry-run mode.")


class TradingSignalBot:
    """
    Main orchestrator. Runs the full pipeline:
    Data → Structure → Entry → Score → Risk → Output → Telegram
    """

    def __init__(self, config):
        self.config = config
        self.db = None
        self.bot = None
        self._fired_signals: Set[str] = set()   # prevent duplicate signals
        self._alerted_tp: Set[str] = set()       # prevent duplicate TP/SL alerts
        self._last_report: Optional[datetime] = None
        self._last_backup: Optional[datetime] = None

        # Lazy imports (so each module can be tested independently)
        from data_layer import sync_timeframes, add_indicators, get_current_session
        from market_structure import analyze_market_structure
        from entry_logic import find_best_entry
        from scoring_engine import assess_indicators, score_signal, is_news_blackout, build_risk_profile
        from signal_output import TradeDatabase, format_signal_message, format_performance_report, should_send_monthly_report
        from strategies import assess_strategies
        from false_breakout import detect_false_breakouts, pick_best_signal

        self._sync_timeframes = sync_timeframes
        self._add_indicators = add_indicators
        self._get_current_session = get_current_session
        self._analyze_structure = analyze_market_structure
        self._find_entry = find_best_entry
        self._assess_indicators = assess_indicators
        self._score_signal = score_signal
        self._is_news_blackout = is_news_blackout
        self._build_risk = build_risk_profile
        self._format_signal = format_signal_message
        self._format_report = format_performance_report
        self._should_report = should_send_monthly_report
        self._assess_strategies = assess_strategies
        self._detect_fb = detect_false_breakouts
        self._pick_fb = pick_best_signal

        self.db = TradeDatabase(config.TRADES_DB_PATH)

        # Chart renderer (lazy import)
        self._chart_available = False
        try:
            from charts import render_signal_chart, render_blurred_chart
            self._render_chart = render_signal_chart
            self._render_blurred = render_blurred_chart
            self._chart_available = True
        except ImportError:
            logger.warning("charts.py not available — signals will be text-only")

        if TELEGRAM_AVAILABLE and config.TELEGRAM_TOKEN != "YOUR_BOT_TOKEN":
            self.bot = Bot(token=config.TELEGRAM_TOKEN)

    async def send_telegram(self, chat_id: str, text: str, delay_seconds: int = 0):
        """Send a message to a Telegram channel with retry logic and optional delay."""
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        if not self.bot:
            logger.info(f"[DRY RUN → {chat_id}]\n{text}")
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=constants.ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=True
                )
                logger.info(f"Telegram message sent to {chat_id}")
                return
            except Exception as e:
                wait = 2 ** attempt  # 1s, 2s, 4s
                if attempt < max_retries - 1:
                    logger.warning(f"Telegram send attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Telegram send failed after {max_retries} attempts: {e}")

    async def send_telegram_with_chart(
        self, chat_id: str, text: str, chart_path: str,
        is_pro: bool = True, delay_seconds: int = 0
    ):
        """Send a chart image with text caption and retry logic."""
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        if not self.bot:
            logger.info(f"[DRY RUN → {chat_id}] (chart: {'full' if is_pro else 'blurred'})\n{text}")
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if is_pro:
                    with open(chart_path, "rb") as img:
                        await self.bot.send_photo(
                            chat_id=chat_id,
                            photo=img,
                            caption=text,
                            parse_mode=constants.ParseMode.MARKDOWN_V2,
                        )
                else:
                    blurred_bytes = self._render_blurred(chart_path)
                    if blurred_bytes:
                        from io import BytesIO
                        buf = BytesIO(blurred_bytes)
                        buf.name = "chart_blurred.png"
                        await self.bot.send_photo(
                            chat_id=chat_id,
                            photo=buf,
                            caption=text,
                            parse_mode=constants.ParseMode.MARKDOWN_V2,
                        )
                    else:
                        await self.send_telegram(chat_id, text)
                        return

                logger.info(f"Telegram chart sent to {chat_id}")
                return
            except Exception as e:
                wait = 2 ** attempt
                if attempt < max_retries - 1:
                    logger.warning(f"Telegram chart send attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Telegram chart send failed after {max_retries} attempts: {e}")
                    # Fallback to text-only
                    await self.send_telegram(chat_id, text)

    def _generate_signal_id(self, symbol: str, direction: str, entry: float) -> str:
        """Generate a deduplication key for a signal."""
        raw = f"{symbol}:{direction}:{round(entry, 2)}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _detect_primary_strategy(self, strategy_conv, symbol: str) -> str:
        """Only SMC 8-Gate — all other strategies removed (MarketMate graveyard)."""
        return "smc_8gate"

    def _detect_regime(self, df) -> str:
        """Detect current market regime based on ADX and ATR."""
        try:
            import numpy as np

            # Calculate ADX (simplified)
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values

            # True Range
            tr = np.maximum(high[1:] - low[1:],
                          np.maximum(abs(high[1:] - close[:-1]),
                                   abs(low[1:] - close[:-1])))

            # ATR
            atr = np.mean(tr[-14:]) if len(tr) >= 14 else np.mean(tr)

            # ATR average
            atr_avg = np.mean(tr[-50:]) if len(tr) >= 50 else np.mean(tr)

            # Volatility regime
            if atr > atr_avg * 1.5:
                return "VOLATILE"
            elif atr < atr_avg * 0.7:
                return "QUIET"

            # Trend strength (simplified ADX proxy)
            price_change = (close[-1] - close[-20]) / close[-20] * 100 if len(close) >= 20 else 0
            abs_change = abs(price_change)

            if abs_change > 3:
                return "TRENDING"
            else:
                return "RANGING"

        except Exception:
            return "UNKNOWN"

    async def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Full analysis pipeline for one symbol.
        Returns signal dict if a valid trade is found, None otherwise.
        """
        config = self.config

        # ── Layer 8: Session Filter ──────────────────────────────────────────
        session = self._get_current_session(config)
        if session not in config.ALLOWED_SESSIONS:
            logger.debug(f"{symbol}: Dead zone ({session}), skipping.")
            return None

        # ── Layer 9: News Blackout Filter ────────────────────────────────────
        in_blackout, blackout_reason = self._is_news_blackout(symbol, config)
        if in_blackout:
            logger.info(f"{symbol}: News blackout — {blackout_reason}")
            return None

        # ── Layer 5: Max trades per day/session check ────────────────────────
        trades_today = self.db.count_trades_today()
        trades_this_session = self.db.count_trades_today(session=session)
        if trades_today >= config.MAX_TRADES_PER_DAY:
            logger.info(f"{symbol}: Max daily trades reached ({trades_today})")
            return None
        if trades_this_session >= config.MAX_TRADES_PER_SESSION:
            logger.info(f"{symbol}: Max session trades reached ({trades_this_session})")
            return None

        # ── Layer 1: Fetch & Prepare Data ────────────────────────────────────
        # Run synchronous data fetch in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        frames = await loop.run_in_executor(None, self._sync_timeframes, symbol, config)
        if config.PRIMARY_TIMEFRAME not in frames:
            logger.warning(f"{symbol}: Primary TF data unavailable")
            return None

        df_primary = self._add_indicators(frames[config.PRIMARY_TIMEFRAME], config)
        df_htf = self._add_indicators(frames.get(config.HTF_TIMEFRAME, df_primary), config)

        if len(df_primary) < 50:
            logger.warning(f"{symbol}: Insufficient data ({len(df_primary)} candles)")
            return None

        # ── Layer 2: Market Structure ────────────────────────────────────────
        structure = self._analyze_structure(df_primary, config)

        # Detect regime once — used by both SMC and FB
        regime = self._detect_regime(df_primary)

        # ── Layer 4: Indicator Assessment ────────────────────────────────────
        # Determine direction from structure first
        from market_structure import Trend

        # Try both directions, score them, pick the winner
        signals_found = []

        for direction in ["buy", "sell"]:
            # Quick pre-filter: don't look for buys in a strong bearish trend
            if direction == "buy" and structure.trend == Trend.BEARISH:
                # Only proceed if we have a CHoCH (potential reversal)
                if structure.last_choch is None or structure.last_choch.direction != "bullish":
                    continue
            if direction == "sell" and structure.trend == Trend.BULLISH:
                if structure.last_choch is None or structure.last_choch.direction != "bearish":
                    continue

            # ── Layer 3: Entry Logic ─────────────────────────────────────────
            entry_setup = self._find_entry(df_primary, direction, structure, config)
            if entry_setup is None:
                continue

            # ── Layer 4: Indicators ──────────────────────────────────────────
            indicator_sig = self._assess_indicators(df_primary, direction, config)

            # ── Layer 4b: Strategy Confluence ────────────────────────────────
            strategy_conv = self._assess_strategies(df_primary, direction, config, symbol=symbol)

            # ── Layer 6: Scoring Engine ──────────────────────────────────────
            score = self._score_signal(
                structure, entry_setup, indicator_sig,
                session, news_clear=True, config=config,
                strategy_confluence=strategy_conv
            )

            if not score.passed:
                logger.debug(f"{symbol} {direction.upper()}: Rejected — {score.reject_reason}")
                continue

            # ── Layer 5: Risk Profile ────────────────────────────────────────
            risk = self._build_risk(
                entry_setup.entry_price, entry_setup.stop_loss,
                entry_setup.tp1, entry_setup.tp2, entry_setup.tp3,
                account_balance=config.ACCOUNT_BALANCE,
                config=config
            )

            if not risk.valid:
                continue

            # Build full indicator detail for reason string
            ind_details = []
            if indicator_sig.rsi_signal == direction:
                ind_details.append(f"RSI {indicator_sig.details['rsi']:.0f}")
            if indicator_sig.rsi_divergence:
                ind_details.append("RSI div")
            if indicator_sig.ema_bias == ("bullish" if direction == "buy" else "bearish"):
                ind_details.append(f"Above EMA{config.EMA_SLOW}" if direction == "buy" else f"Below EMA{config.EMA_SLOW}")
            if indicator_sig.volume_elevated:
                ind_details.append(f"RVOL {indicator_sig.details['rvol']:.1f}×")

            # Strategy confluence details
            strat_details = []
            if strategy_conv.day_filter:
                strat_details.append(f"Day: {strategy_conv.day_name} ({strategy_conv.day_filter})")

            full_reason = entry_setup.reason
            if ind_details:
                full_reason += ", " + ", ".join(ind_details)
            if strat_details:
                full_reason += " | " + ", ".join(strat_details)

            signals_found.append({
                "symbol": symbol,
                "direction": direction,
                "entry": entry_setup.entry_price,
                "stop_loss": entry_setup.stop_loss,
                "tp1": entry_setup.tp1,
                "tp2": entry_setup.tp2,
                "tp3": entry_setup.tp3,
                "rr_tp1": risk.rr_tp1,
                "rr_tp2": risk.rr_tp2,
                "rr_tp3": risk.rr_tp3,
                "confidence": score.confidence_pct,
                "score": score.total,
                "max_score": score.max_possible,
                "session": session,
                "reason": full_reason,
                "position_size": risk.position_size,
                "breakdown": score.breakdown,
                # Strategy and regime tracking
                "strategy_used": self._detect_primary_strategy(strategy_conv, symbol),
                "regime_at_entry": regime,
                # Chart data
                "_df": df_primary,
                "_order_blocks": getattr(entry_setup, 'order_blocks', []),
                "_fvgs": getattr(entry_setup, 'fvgs', []),
                "_bos": structure.last_bos,
            })

        # ── False Breakout Trap scan (secondary strategy) ─────────────────
        fb_signal = None
        if self.config.FALSE_BREAKOUT_ENABLED:
            try:
                fb_raw = self._detect_fb(
                    df_primary,
                    lookback=self.config.FALSE_BREAKOUT_LOOKBACK,
                    sl_atr_mult=self.config.FALSE_BREAKOUT_SL_ATR,
                    tp1_atr_mult=self.config.FALSE_BREAKOUT_TP1_ATR,
                    tp2_atr_mult=self.config.FALSE_BREAKOUT_TP2_ATR,
                    tp3_atr_mult=self.config.FALSE_BREAKOUT_TP3_ATR,
                    symbol=symbol,
                )
                fb_best = self._pick_fb(fb_raw)
                if fb_best and fb_best["confidence"] >= self.config.FALSE_BREAKOUT_MIN_CONFIDENCE:
                    risk = self._build_risk(
                        fb_best["entry"], fb_best["stop_loss"],
                        fb_best["tp1"], fb_best["tp2"], fb_best["tp3"],
                        account_balance=self.config.ACCOUNT_BALANCE,
                        config=self.config
                    )
                    if risk.valid:
                        fb_signal = {
                            "symbol": symbol,
                            "direction": fb_best["direction"],
                            "entry": fb_best["entry"],
                            "stop_loss": fb_best["stop_loss"],
                            "tp1": fb_best["tp1"],
                            "tp2": fb_best["tp2"],
                            "tp3": fb_best["tp3"],
                            "rr_tp1": risk.rr_tp1,
                            "rr_tp2": risk.rr_tp2,
                            "rr_tp3": risk.rr_tp3,
                            "confidence": fb_best["confidence"],
                            "score": 14,
                            "max_score": 20,
                            "session": session,
                            "reason": fb_best["reason"],
                            "position_size": risk.position_size,
                            "breakdown": {"false_breakout": 14},
                            "strategy_used": "false_breakout",
                            "regime_at_entry": regime,
                            "_df": df_primary,
                            "_order_blocks": [],
                            "_fvgs": [],
                            "_bos": None,
                        }
                        logger.info(f"{symbol}: FB signal {fb_best['direction'].upper()} "
                                    f"@ {fb_best['entry']:.5f} (conf {fb_best['confidence']:.0f}%)")
            except Exception as e:
                logger.warning(f"{symbol}: FB scan error: {e}")

        # ── Dual-Strategy Decision ──────────────────────────────────────────
        smc_best = max(signals_found, key=lambda s: s["confidence"]) if signals_found else None

        if smc_best and fb_signal:
            # Regime-based routing
            if regime in ("VOLATILE", "TRENDING"):
                chosen = smc_best
            elif regime in ("RANGING", "QUIET"):
                chosen = fb_signal
            else:
                # MIXED, UNKNOWN — higher confidence wins
                chosen = smc_best if smc_best["confidence"] >= fb_signal["confidence"] else fb_signal
            logger.info(f"{symbol}: Regime {regime} → chosen {chosen['strategy_used']} "
                        f"({chosen['direction'].upper()} conf {chosen['confidence']:.0f}%)")
            return chosen

        if smc_best:
            return smc_best
        if fb_signal:
            return fb_signal
        return None

    async def fire_signal(self, signal: Dict):
        """Send the signal to Telegram channels with anti-leak logic."""
        config = self.config

        sig_id = self._generate_signal_id(
            signal["symbol"], signal["direction"], signal["entry"]
        )

        if sig_id in self._fired_signals:
            logger.debug(f"Duplicate signal suppressed: {sig_id}")
            return

        self._fired_signals.add(sig_id)

        # Format message
        msg = self._format_signal(
            symbol=signal["symbol"],
            direction=signal["direction"],
            entry=signal["entry"],
            stop_loss=signal["stop_loss"],
            tp1=signal["tp1"],
            tp2=signal["tp2"],
            tp3=signal["tp3"],
            rr1=signal["rr_tp1"],
            rr2=signal["rr_tp2"],
            rr3=signal["rr_tp3"],
            confidence=signal["confidence"],
            score=signal["score"],
            max_score=signal["max_score"],
            session=signal["session"],
            reason=signal["reason"],
            timeframe=config.PRIMARY_TIMEFRAME
        )

        # Save to database
        self.db.save_trade(
            signal_id=sig_id,
            symbol=signal["symbol"],
            direction=signal["direction"],
            entry=signal["entry"],
            sl=signal["stop_loss"],
            tp1=signal["tp1"],
            tp2=signal["tp2"],
            tp3=signal["tp3"],
            rr1=signal["rr_tp1"],
            confidence=signal["confidence"],
            score=signal["score"],
            session=signal["session"],
            reason=signal["reason"],
            strategy_used=signal.get("strategy_used"),
            regime_at_entry=signal.get("regime_at_entry")
        )

        # ── Generate chart if available ───────────────────────────────────────
        chart_path = None
        if self._chart_available and "_df" in signal:
            try:
                chart_path = await self._render_chart(
                    signal=signal,
                    df=signal["_df"],
                    order_blocks=signal.get("_order_blocks", []),
                    fvgs=signal.get("_fvgs", []),
                    bos=signal.get("_bos"),
                )
            except Exception as e:
                logger.warning(f"Chart generation failed: {e}")

        # ── Layer 13: Security — Private channel first ─────────────────────
        # Text always goes through — chart is optional follow-up
        await self.send_telegram(config.PRIVATE_CHANNEL_ID, msg)
        if chart_path:
            asyncio.create_task(self.send_telegram_with_chart(
                config.PRIVATE_CHANNEL_ID, msg, chart_path, is_pro=True
            ))

        # Public channel with delay (anti-leak)
        if config.PUBLIC_CHANNEL_ID:
            delay = config.PUBLIC_DELAY_MINUTES * 60
            if chart_path:
                asyncio.create_task(
                    self.send_telegram_with_chart(
                        config.PUBLIC_CHANNEL_ID, msg, chart_path,
                        is_pro=True, delay_seconds=delay
                    )
                )
            else:
                asyncio.create_task(
                    self.send_telegram(config.PUBLIC_CHANNEL_ID, msg, delay_seconds=delay)
                )

        # Clean up chart file
        if chart_path:
            from charts import _cleanup
            _cleanup(chart_path)

        logger.info(
            f"Signal fired: {signal['symbol']} {signal['direction'].upper()} "
            f"@ {signal['entry']} | Conf: {signal['confidence']}% "
            f"| Score: {signal['score']}/{signal['max_score']}"
        )

    async def monitor_open_trades(self):
        """
        Layer 7: Trade Management
        Check open trades against current prices and send TP/SL alerts.
        """
        # Skip trade monitoring outside market hours (prevents false TP/SL from stale weekend data)
        from data_layer import is_session_allowed
        if not is_session_allowed(self.config):
            return

        open_trades = self.db.get_open_trades()
        if not open_trades:
            return

        from data_layer import fetch_ohlcv

        for trade in open_trades:
            symbol = trade["symbol"]
            df = fetch_ohlcv(symbol, "1m", limit=5, source=self.config.DATA_SOURCE)
            if df is None or df.empty:
                continue

            current_price = df["close"].iloc[-1]
            direction = trade["direction"]
            entry = trade["entry"]
            sl = trade["stop_loss"]

            from signal_output import format_tp_hit_alert, format_sl_hit_alert

            # Check TP hits
            for tp_num in [1, 2, 3]:
                alert_key = f"{trade['id']}_tp{tp_num}"
                if alert_key in self._alerted_tp:
                    continue
                if trade.get(f"tp{tp_num}_hit"):
                    self._alerted_tp.add(alert_key)
                    continue
                tp_price = trade[f"tp{tp_num}"]

                if (direction == "buy" and current_price >= tp_price) or \
                   (direction == "sell" and current_price <= tp_price):

                    self.db.update_tp_hit(trade["id"], tp_num)
                    self._alerted_tp.add(alert_key)
                    alert = format_tp_hit_alert(symbol, direction, tp_num, tp_price, trade["id"])
                    await self.send_telegram(self.config.PRIVATE_CHANNEL_ID, alert)

                    # After TP1, move SL to breakeven
                    if tp_num == 1:
                        logger.info(f"TP1 hit on {symbol} — SL moved to breakeven ({entry})")
                    break

            # Check SL hit
            sl_key = f"{trade['id']}_sl"
            if sl_key not in self._alerted_tp and \
               ((direction == "buy" and current_price <= sl) or \
                (direction == "sell" and current_price >= sl)):

                self._alerted_tp.add(sl_key)

                # Determine if BE was set (trade was partially profitable)
                if trade.get("be_moved"):
                    self.db.close_trade(trade["id"], result="win", actual_rr=0.0)
                else:
                    self.db.close_trade(trade["id"], result="loss", actual_rr=-1.0)

                alert = format_sl_hit_alert(symbol, direction, sl)
                await self.send_telegram(self.config.PRIVATE_CHANNEL_ID, alert)

    async def check_monthly_report(self):
        """Layer 14: Send monthly performance report if due."""
        if self._should_report(self._last_report):
            stats = self.db.get_performance_stats(days=30)
            if stats["total_trades"] > 0:
                from signal_output import format_performance_report
                report = format_performance_report(stats)
                await self.send_telegram(self.config.PRIVATE_CHANNEL_ID, report)
                if self.config.PUBLIC_CHANNEL_ID:
                    await self.send_telegram(self.config.PUBLIC_CHANNEL_ID, report)
            self._last_report = datetime.now(timezone.utc)

    async def run_scan_cycle(self):
        """Scan a subset of symbols each cycle (round-robin) to spread API load."""
        all_symbols = self.config.SYMBOLS
        batch_size = min(4, len(all_symbols))
        offset = getattr(self, "_scan_offset", 0)
        if offset >= len(all_symbols):
            offset = 0
        batch = all_symbols[offset:offset + batch_size]
        self._scan_offset = offset + batch_size

        logger.info(f"Scan cycle started — {len(batch)}/{len(all_symbols)} symbols")
        tasks = [self.analyze_symbol(sym) for sym in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for sym, result in zip(batch, results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing {sym}: {result}")
            elif result is not None:
                await self.fire_signal(result)

        await self.monitor_open_trades()
        await self.check_monthly_report()

        # Daily backup check
        now = datetime.now(timezone.utc)
        if self._last_backup is None or (now - self._last_backup).days >= 1:
            self.db.backup()
            self._last_backup = now

    async def run(self):
        """Main loop — runs forever, scanning on interval."""
        logger.info("🤖 Trading Signal Bot started")
        logger.info(f"   Symbols: {', '.join(self.config.SYMBOLS)}")
        logger.info(f"   Scan interval: {self.config.SCAN_INTERVAL_SECONDS}s")
        logger.info(f"   Min confidence: {self.config.MIN_CONFIDENCE_PCT}%")
        logger.info(f"   Min score: {self.config.MIN_SCORE_THRESHOLD}/{sum(self.config.SCORE_WEIGHTS.values())}")

        while not _shutdown_requested:
            try:
                await self.run_scan_cycle()
            except Exception as e:
                logger.exception(f"Scan cycle error: {e}")

            if _shutdown_requested:
                break

            logger.debug(f"Sleeping {self.config.SCAN_INTERVAL_SECONDS}s...")
            await asyncio.sleep(self.config.SCAN_INTERVAL_SECONDS)

        logger.info("Bot shut down gracefully")


# ──────────────────────────────────────────────────────────────────────────────
# Telegram Bot with Command Handlers
# ──────────────────────────────────────────────────────────────────────────────

def run_bot_with_commands():
    """Run the bot with both signal scanning and command handlers."""
    from config import CONFIG
    from commands import (
        start_command,
        status_command, stats_command, help_command,
        portfolio_command, strategies_command, pairs_command,
        regimes_command, drawdown_command, history_command
    )

    # Validate config at startup
    if not CONFIG.validate_or_exit():
        logger.error("Startup aborted due to configuration errors")
        return

    if not TELEGRAM_AVAILABLE or CONFIG.TELEGRAM_TOKEN == "YOUR_BOT_TOKEN":
        logger.warning("Telegram not available — running in dry-run mode")
        bot = TradingSignalBot(CONFIG)
        asyncio.run(bot.run())
        return

    # Build the Application
    application = Application.builder().token(CONFIG.TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("portfolio", portfolio_command))
    application.add_handler(CommandHandler("strategies", strategies_command))
    application.add_handler(CommandHandler("pairs", pairs_command))
    application.add_handler(CommandHandler("regimes", regimes_command))
    application.add_handler(CommandHandler("drawdown", drawdown_command))
    application.add_handler(CommandHandler("history", history_command))

    # Create bot instance for signal scanning
    bot = TradingSignalBot(CONFIG)

    # Schedule scan loop via job queue
    async def scheduled_scan(context: ContextTypes.DEFAULT_TYPE):
        await bot.run_scan_cycle()

    job_queue = application.job_queue
    if job_queue is not None:
        job_queue.run_repeating(
            scheduled_scan,
            interval=CONFIG.SCAN_INTERVAL_SECONDS,
            first=10,
            name="signal_scan",
        )
    else:
        logger.warning("Job queue not available (APScheduler not installed). Scan loop disabled.")

    logger.info("TradeKnox bot starting with command handlers")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    run_bot_with_commands()
