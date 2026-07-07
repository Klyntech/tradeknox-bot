"""
charts.py — Professional candlestick chart renderer for TradeKnox signals.

Adapted from MarketMate's chart_renderer.py. Renders a dark-theme
institutional chart with Entry/SL/TP overlays, Order Blocks, FVGs,
and BOS/CHoCH markers. Runs matplotlib in a dedicated ThreadPoolExecutor.

Returns the path to a PNG file, or None on any failure. Never raises.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger("chart_renderer")

# ─── Pre-import matplotlib at module load time ─────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.ticker as mticker
    import matplotlib.dates as mdates
    import matplotlib.gridspec as gridspec

    # Warmup: create and immediately close a dummy figure
    _warmup_fig = plt.figure()
    plt.close(_warmup_fig)

    _MPL_AVAILABLE = True
    log.info("chart_renderer_ready", extra={"backend": matplotlib.get_backend()})
except ImportError as _mpl_err:
    _MPL_AVAILABLE = False
    log.warning("matplotlib_not_installed", extra={"error": str(_mpl_err)})

# ─── Dedicated render executor ────────────────────────────────────────────────
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="chart_render")


# ─── Colour palette ───────────────────────────────────────────────────────────
# TradingView dark theme

C_BG       = "#131722"    # outermost background
C_PANEL    = "#1e222d"    # chart panel background
C_GRID     = "#2a2e39"    # grid lines
C_GRID_DAY = "#3a3f4b"    # date separator lines
C_TEXT     = "#787b86"    # axis labels and minor text
C_WHITE    = "#d1d4dc"    # primary text
C_BULL     = "#26a69a"    # teal — bull candles
C_BEAR     = "#ef5350"    # red — bear candles
C_ENTRY    = "#ffd700"    # gold — entry level
C_SL       = "#ef5350"    # red — stop loss
C_TP1      = "#26a69a"    # teal — TP1
C_TP2      = "#4caf50"    # green — TP2
C_TP3      = "#81c784"    # light green — TP3

# TradeKnox-specific annotation colours
C_OB_DEMAND  = "#22c55e"  # green — demand zone
C_OB_SUPPLY  = "#ef4444"  # red — supply zone
C_FVG        = "#94a3b8"  # gray — fair value gap
C_BOS        = "#ffd700"  # gold — break of structure
C_CHOCH      = "#a855f7"  # purple — change of character


# ─── Synchronous render (called via executor) ─────────────────────────────────

def _render_sync(
    df: pd.DataFrame,
    signal: Dict,
    output_path: str,
    order_blocks: Optional[List[Dict]] = None,
    fvgs: Optional[List[Dict]] = None,
    bos: Optional[Dict] = None,
    timezone_str: str = "UTC",
) -> str:
    """
    Pure matplotlib candlestick chart renderer. Runs in a thread pool executor.

    Chart composition:
      - TradingView dark palette
      - Real datetime x-axis with date separator lines
      - Candlestick bodies + wicks with subtle edge borders
      - Dual y-axis (left + right price labels)
      - Volume sub-panel (when volume data is available)
      - Horizontal overlays: Entry (gold), SL (dashed red), TP1/TP2/TP3 (dotted green)
      - Order Block zones (semi-transparent rectangles)
      - Fair Value Gap zones (semi-transparent rectangles)
      - BOS/CHoCH markers (horizontal dashed lines with labels)
      - Label collision avoidance with dark bbox background
    """

    # ── Defensive prep ────────────────────────────────────────────────────────
    df = df.copy()

    # Normalise timestamp into a proper column
    if "timestamp" not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index().rename(columns={"index": "timestamp"})
        else:
            df["timestamp"] = pd.RangeIndex(len(df))

    # Sanitise: drop rows with NaN/Inf in OHLC columns
    ohlc_cols = ["open", "high", "low", "close"]
    for col in ohlc_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    pre_len = len(df)
    df = df.dropna(subset=ohlc_cols).reset_index(drop=True)
    if len(df) < pre_len:
        log.warning("chart_dropped_nan_rows", extra={"dropped": pre_len - len(df)})
    if df.empty:
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
        fig.patch.set_facecolor(C_BG)
        ax.set_facecolor(C_PANEL)
        ax.text(0.5, 0.5, "No valid price data",
                transform=ax.transAxes, fontsize=24,
                color=C_TEXT, ha="center", va="center")
        plt.savefig(output_path, dpi=100, facecolor=C_BG, format="png")
        plt.close(fig)
        return output_path

    # Use last 100 candles, ordered oldest → newest
    df = df.tail(100).reset_index(drop=True)
    n = len(df)

    opens  = df["open"].astype(float).values
    highs  = df["high"].astype(float).values
    lows   = df["low"].astype(float).values
    closes = df["close"].astype(float).values

    # Sanitise volume
    has_volume = False
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        df["volume"] = df["volume"].replace([np.inf, -np.inf], 0).clip(lower=0)
        has_volume = df["volume"].notna().any() and float(df["volume"].max()) > 0

    # ── X-axis: real datetime vs integer fallback ─────────────────────────────
    has_dates = False
    is_weekend_render = False
    x = np.arange(n, dtype=float)
    candle_width = 0.55

    try:
        ts_series = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        if ts_series.notna().all():
            x_naive = ts_series.dt.tz_convert(None)

            df_tail_backup = df.copy()
            x_naive_backup = x_naive.copy()

            weekend_mask = x_naive.dt.dayofweek < 5
            if weekend_mask.any():
                df = df[weekend_mask.values]
                x_naive = x_naive[weekend_mask]
            else:
                is_weekend_render = True

            if df.empty:
                df = df_tail_backup.copy()
                x_naive = x_naive_backup.copy()
                is_weekend_render = True

            opens  = df["open"].astype(float).values
            highs  = df["high"].astype(float).values
            lows   = df["low"].astype(float).values
            closes = df["close"].astype(float).values
            n = len(df)

            x = mdates.date2num(x_naive.to_numpy())

            deltas = np.diff(x)
            median_delta = float(np.median(deltas)) if len(deltas) > 0 else (1 / 24 / 4)
            candle_width = median_delta * 0.6

            has_dates = True
    except Exception as exc:
        log.debug("chart_datetime_fallback", extra={"reason": str(exc)})

    half_w = candle_width / 2

    # ── Extract signal values ─────────────────────────────────────────────────
    def _safe_last_close() -> float:
        valid = closes[~np.isnan(closes)]
        return float(valid[-1]) if len(valid) > 0 else 0.0

    entry_raw = signal.get("entry", signal.get("entry_mid"))
    entry = float(entry_raw) if entry_raw is not None else _safe_last_close()
    sl        = float(signal.get("stop_loss", signal.get("sl", 0.0)))
    tp1       = float(signal.get("tp1", 0.0))
    tp2       = float(signal.get("tp2", 0.0))
    tp3_raw   = signal.get("tp3")
    tp3       = float(tp3_raw) if (tp3_raw is not None and tp3_raw != 0) else None
    direction = str(signal.get("direction", "BUY")).upper()
    symbol    = str(signal.get("symbol", "XAUUSD"))
    score     = signal.get("score", 0)
    confidence = signal.get("confidence", 0)

    # ── Figure & GridSpec ─────────────────────────────────────────────────────
    if has_volume:
        fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=C_BG)
        gs = gridspec.GridSpec(
            2, 1, height_ratios=[4, 1], hspace=0.02, figure=fig,
        )
        ax = fig.add_subplot(gs[0])
        ax_vol = fig.add_subplot(gs[1], sharex=ax)
    else:
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
        fig.patch.set_facecolor(C_BG)
        ax_vol = None

    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_PANEL)

    # ── Draw candlestick bodies and wicks ─────────────────────────────────────
    visible_range = highs.max() - lows.min()
    min_body = visible_range * 0.001

    for i in range(n):
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        bull = c >= o
        color = C_BULL if bull else C_BEAR
        body_lo = min(o, c)
        body_hi = max(o, c)
        body_height = max(body_hi - body_lo, min_body)

        xi = x[i]

        ax.plot([xi, xi], [l, h],
                color=color, linewidth=0.9, zorder=2, solid_capstyle="round")

        edge_col = "#c8e6c9" if bull else "#ffcdd2"
        body = mpatches.Rectangle(
            (xi - half_w, body_lo),
            candle_width, body_height,
            facecolor=color, edgecolor=edge_col,
            linewidth=0.4, zorder=3,
        )
        ax.add_patch(body)

    # ── Date separator lines ──────────────────────────────────────────────────
    if has_dates:
        try:
            ts_arr = pd.to_datetime(df["timestamp"], utc=True)
            day_changes = ts_arr[ts_arr.dt.hour == 0]
            for dt in day_changes:
                xv = mdates.date2num(dt.to_pydatetime())
                ax.axvline(xv, color=C_GRID_DAY, linewidth=0.7,
                           linestyle="--", alpha=0.5, zorder=1)
        except Exception:
            pass

    # ── Overlay lines: Entry / SL / TP levels ─────────────────────────────────
    placed_labels: list[float] = []
    MIN_LABEL_GAP = visible_range * 0.02

    def _next_clear_y(price: float) -> float:
        final_y = price
        while True:
            if all(abs(final_y - py) >= MIN_LABEL_GAP for py in placed_labels):
                break
            final_y += MIN_LABEL_GAP * 1.2
        placed_labels.append(final_y)
        return final_y

    if has_dates and n > 0:
        label_x = x[-1] + candle_width * 2.5
    else:
        label_x = n + 0.5

    def _hline(price, color, style, lw, label, alpha=0.92):
        if price <= 0 or np.isnan(price):
            return
        ax.axhline(price, color=color, linewidth=lw,
                   linestyle=style, zorder=5, alpha=alpha)
        label_y = _next_clear_y(price)
        ax.text(
            label_x, label_y,
            f" {label}  {price:,.2f}",
            color=color, fontsize=8.5, va="center", ha="left",
            fontfamily="monospace", zorder=6, clip_on=False,
            bbox=dict(
                facecolor=C_BG, edgecolor=color, alpha=0.88,
                pad=1.5, boxstyle="round,pad=0.2",
            ),
        )

    _hline(entry, C_ENTRY, "-",  1.6, "Entry")
    _hline(sl,    C_SL,    "--", 1.3, "SL   ")
    _hline(tp1,   C_TP1,   "--", 1.3, "TP1  ")
    _hline(tp2,   C_TP2,   ":",  1.1, "TP2  ", alpha=0.85)
    if tp3:
        _hline(tp3, C_TP3, ":",  1.0, "TP3  ", alpha=0.70)

    # ── Order Block zones ─────────────────────────────────────────────────────
    if order_blocks:
        for ob in order_blocks:
            ob_high = ob.get("high", 0)
            ob_low = ob.get("low", 0)
            ob_type = ob.get("type", "demand")
            if ob_high > 0 and ob_low > 0 and ob_high > ob_low:
                color = C_OB_DEMAND if ob_type == "demand" else C_OB_SUPPLY
                ax.axhspan(ob_low, ob_high, alpha=0.12, color=color, zorder=1)
                label_y = _next_clear_y(ob_high)
                ax.text(
                    label_x, label_y,
                    f" OB ({ob_type[:3].upper()})",
                    color=color, fontsize=7, va="center", ha="left",
                    fontfamily="monospace", zorder=6, clip_on=False,
                    bbox=dict(
                        facecolor=C_BG, edgecolor=color, alpha=0.8,
                        pad=1.0, boxstyle="round,pad=0.2",
                    ),
                )

    # ── Fair Value Gap zones ──────────────────────────────────────────────────
    if fvgs:
        for fvg in fvgs:
            fvg_high = fvg.get("high", 0)
            fvg_low = fvg.get("low", 0)
            if fvg_high > 0 and fvg_low > 0 and fvg_high > fvg_low:
                ax.axhspan(fvg_low, fvg_high, alpha=0.10, color=C_FVG, zorder=1)
                label_y = _next_clear_y(fvg_high)
                ax.text(
                    label_x, label_y,
                    " FVG",
                    color=C_FVG, fontsize=7, va="center", ha="left",
                    fontfamily="monospace", zorder=6, clip_on=False,
                    bbox=dict(
                        facecolor=C_BG, edgecolor=C_FVG, alpha=0.8,
                        pad=1.0, boxstyle="round,pad=0.2",
                    ),
                )

    # ── BOS / CHoCH markers ──────────────────────────────────────────────────
    if bos:
        bos_price = bos.get("price", 0)
        bos_dir = bos.get("direction", "bullish")
        bos_type = bos.get("type", "BOS")
        if bos_price > 0:
            color = C_BOS if bos_type.upper() == "BOS" else C_CHOCH
            ax.axhline(bos_price, color=color, linewidth=1.2,
                       linestyle="--", alpha=0.85, zorder=4)
            label_y = _next_clear_y(bos_price)
            ax.text(
                label_x, label_y,
                f" {bos_type.upper()} {'▲' if bos_dir == 'bullish' else '▼'}",
                color=color, fontsize=7, va="center", ha="left",
                fontfamily="monospace", zorder=6, clip_on=False,
                bbox=dict(
                    facecolor=C_BG, edgecolor=color, alpha=0.85,
                    pad=1.0, boxstyle="round,pad=0.2",
                ),
            )

    # ── Dual y-axis ──────────────────────────────────────────────────────────
    ax_right = ax.twinx()
    ax_right.set_ylim(ax.get_ylim())
    ax_right.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:,.2f}")
    )
    ax_right.tick_params(colors=C_TEXT, labelsize=8.5, length=3)
    ax_right.set_facecolor(C_PANEL)
    ax_right.grid(False)

    # ── X-axis formatting ─────────────────────────────────────────────────────
    if has_dates:
        span_days = x[-1] - x[0]
        if span_days <= 2:
            major_fmt = mdates.DateFormatter('%H:%M')
        else:
            major_fmt = mdates.DateFormatter('%m/%d\n%H:%M')

        ax.xaxis.set_major_formatter(major_fmt)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=6, maxticks=12))
        if span_days <= 1:
            ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=15))
        elif span_days <= 7:
            ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 4)))
        for label in ax.get_xticklabels():
            label.set_rotation(0)
    else:
        tick_step = max(n // 10, 1)
        xticks = list(range(0, n, tick_step))
        ts_col = df["timestamp"]

        def _fmt_ts(idx: int) -> str:
            try:
                t = ts_col.iloc[idx]
                return t.strftime("%m/%d\n%H:%M") if hasattr(t, "strftime") else str(t)
            except Exception:
                return ""

        ax.set_xticks(xticks)
        ax.set_xticklabels([_fmt_ts(i) for i in xticks],
                           fontsize=7.5, color=C_TEXT, linespacing=1.2)

    ax.tick_params(axis="y", colors=C_TEXT, labelsize=8.5, length=4)
    ax.tick_params(axis="x", colors=C_TEXT, labelsize=7.5, length=4, pad=4)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:,.2f}")
    )

    # ── Grid ──────────────────────────────────────────────────────────────────
    ax.grid(True, color=C_GRID, linewidth=0.5,
            linestyle=(0, (0.5, 2.0)), alpha=0.6)
    ax.set_axisbelow(True)

    # ── Spines ────────────────────────────────────────────────────────────────
    for spine in ax.spines.values():
        spine.set_edgecolor("#252a35")
        spine.set_linewidth(0.7)

    # ── Title ─────────────────────────────────────────────────────────────────
    dir_arrow = "▲" if direction == "BUY" else "▼"
    score_str = f"  ·  {score}/20" if score else ""
    conf_str = f"  ·  {confidence}%" if confidence else ""
    tz_label = timezone_str if timezone_str and timezone_str != "UTC" else "UTC"
    weekend_tag = "  ·  WEEKEND" if is_weekend_render else ""
    ax.set_title(
        f"{symbol}   {dir_arrow} {direction}{score_str}{conf_str}{weekend_tag}   [{tz_label}]",
        color=C_WHITE, fontsize=13, fontweight="bold",
        loc="left", pad=10,
    )

    # ── Weekend watermark ─────────────────────────────────────────────────────
    if is_weekend_render:
        ax.text(
            0.5, 0.5, "MARKET CLOSED",
            transform=ax.transAxes, fontsize=42, fontweight="bold",
            color="#ef5350", alpha=0.15, ha="center", va="center",
            rotation=25, zorder=0,
        )

    # ── Y limits ──────────────────────────────────────────────────────────────
    all_levels = [v for v in [entry, sl, tp1, tp2, tp3] if v and v > 0]
    y_min = min(lows.min(), min(all_levels) if all_levels else lows.min())
    y_max = max(highs.max(), max(all_levels) if all_levels else highs.max())
    pad = max((y_max - y_min) * 0.07, 0.5)
    ax.set_ylim(y_min - pad, y_max + pad)
    ax_right.set_ylim(y_min - pad, y_max + pad)

    if has_dates and n > 0:
        ax.set_xlim(x[0] - candle_width, x[-1] + candle_width * 18)
    else:
        ax.set_xlim(-1, n + 12)

    # ── Volume sub-panel ──────────────────────────────────────────────────────
    if has_volume and ax_vol is not None:
        ax_vol.set_facecolor(C_PANEL)
        vol = df["volume"].astype(float).values
        v_cols = [C_BULL if closes[i] >= opens[i] else C_BEAR for i in range(n)]
        ax_vol.bar(x, vol, width=candle_width,
                   color=v_cols, edgecolor="none", linewidth=0, alpha=0.7)
        ax_vol.set_ylabel("Vol", color=C_TEXT, fontsize=8)
        ax_vol.tick_params(colors=C_TEXT, labelsize=7, length=3)
        ax_vol.yaxis.set_major_locator(mticker.MaxNLocator(3))
        ax_vol.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:.0f}")
        )
        ax_vol.grid(True, color=C_GRID, linewidth=0.4, alpha=0.5)
        for spine in ax_vol.spines.values():
            spine.set_edgecolor("#252a35")
        plt.setp(ax.get_xticklabels(), visible=False)

    # ── TradeKnox watermark ──────────────────────────────────────────────────
    ax.text(
        0.99, 0.02, "TradeKnox",
        transform=ax.transAxes, fontsize=10, fontweight="bold",
        color="#D4A843", alpha=0.3, ha="right", va="bottom",
        fontfamily="monospace", zorder=10,
    )

    # ── Save ──────────────────────────────────────────────────────────────────
    try:
        plt.tight_layout(pad=1.2)
    except Exception:
        pass  # tight_layout can fail with twinx, ignore

    save_kwargs: dict = dict(
        dpi=100, bbox_inches="tight", facecolor=C_BG, format="png",
    )
    try:
        import PIL  # noqa: F401
        save_kwargs["pil_kwargs"] = {"optimize": True, "compress_level": 9}
    except ImportError:
        pass

    plt.savefig(output_path, **save_kwargs)
    plt.close(fig)
    return output_path


# ─── Public async entry point ─────────────────────────────────────────────────

async def render_signal_chart(
    signal: Dict,
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    order_blocks: Optional[List[Dict]] = None,
    fvgs: Optional[List[Dict]] = None,
    bos: Optional[Dict] = None,
    timezone_str: str = "UTC",
) -> Optional[str]:
    """
    Render a candlestick chart for a signal and return the PNG file path.

    Args:
        signal:       Signal dict with entry, stop_loss, tp1/tp2/tp3, direction, etc.
        df:           OHLCV DataFrame. Needs open/high/low/close columns.
        output_path:  Optional output path. A temp file is created if None.
        order_blocks: List of OB dicts with {high, low, type, strength}.
        fvgs:         List of FVG dicts with {high, low}.
        bos:          BOS/CHoCH dict with {price, direction, type}.

    Returns:
        Absolute path to the generated PNG, or None if rendering failed.
    """
    if not _MPL_AVAILABLE:
        log.warning("chart_skipped", extra={"reason": "matplotlib_not_installed"})
        return None

    if df is None or df.empty:
        log.warning("chart_skipped", extra={"reason": "empty_dataframe"})
        return None

    if len(df) < 10:
        log.warning("chart_skipped", extra={"reason": "insufficient_candles", "count": len(df)})
        return None

    if output_path is None:
        try:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".png", prefix="tk_chart_", delete=False
            )
            tmp.close()
            output_path = tmp.name
        except Exception as exc:
            log.error("chart_tempfile_failed", extra={"error": str(exc)})
            return None

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            _EXECUTOR, _render_sync, df, signal, output_path,
            order_blocks, fvgs, bos, timezone_str,
        )
    except Exception as exc:
        log.error("chart_render_error", extra={"error": str(exc)}, exc_info=True)
        _cleanup(output_path)
        return None

    if not os.path.exists(output_path):
        log.warning("chart_render_failed", extra={"reason": "output_file_missing"})
        return None

    size = os.path.getsize(output_path)
    if size < 2048:
        log.warning("chart_render_failed", extra={"reason": "output_too_small", "bytes": size})
        _cleanup(output_path)
        return None

    log.info("chart_rendered", extra={
        "path": output_path,
        "size_kb": round(size / 1024, 1),
        "has_volume": "volume" in df.columns,
    })
    return output_path


# ─── Blur effect for free tier ────────────────────────────────────────────────

def render_blurred_chart(chart_path: str) -> Optional[bytes]:
    """
    Generate a blurred version of the chart with 'Upgrade to Pro' watermark.
    Returns PNG bytes, or None on failure.
    """
    try:
        from PIL import Image, ImageFilter, ImageDraw, ImageFont

        img = Image.open(chart_path)
        blurred = img.filter(ImageFilter.GaussianBlur(radius=15))

        # Add watermark
        draw = ImageDraw.Draw(blurred)
        w, h = blurred.size

        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 48)
            small_font = ImageFont.truetype("arial.ttf", 24)
        except (OSError, IOError):
            font = ImageFont.load_default()
            small_font = font

        # Draw main watermark
        text = "Upgrade to Pro"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((w - tw) // 2, (h - th) // 2),
            text, fill="#ffd700", font=font,
        )

        # Draw subtitle
        sub = "Instant charts + full analysis"
        bbox_sub = draw.textbbox((0, 0), sub, font=small_font)
        sw = bbox_sub[2] - bbox_sub[0]
        draw.text(
            ((w - sw) // 2, (h - th) // 2 + th + 10),
            sub, fill="#ffd700", font=small_font,
        )

        # Convert to bytes
        from io import BytesIO
        buf = BytesIO()
        blurred.save(buf, format="PNG", optimize=True)
        buf.seek(0)
        return buf.getvalue()

    except Exception as exc:
        log.warning("chart_blur_failed", extra={"error": str(exc)})
        return None


# ─── Cleanup helper ───────────────────────────────────────────────────────────

def _cleanup(path: str) -> None:
    """Remove a temp file, ignoring errors."""
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass
