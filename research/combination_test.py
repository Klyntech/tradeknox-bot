"""
Phase 4: Strategy Combination Analysis
Tests 2-strategy and 3-strategy combinations.
Finds optimal confluence setups.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from itertools import combinations

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Import strategies from Phase 3
from strategy_tester import (
    strategy_ma_crossover, strategy_rsi_mean_reversion,
    strategy_bollinger_bounce, strategy_breakout,
    strategy_volume_spike, strategy_ema_alignment,
    backtest_strategy
)


def load_data(symbol: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_1h.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, index_col=True, parse_dates=True)


def combined_signal(df: pd.DataFrame, strategies: list, min_agree: int = 2) -> pd.DataFrame:
    """
    Combine multiple strategy signals.
    Signal = majority vote (at least min_agree strategies must agree).
    """
    df = df.copy()
    df["combined_signal"] = 0

    signals = []
    for strat_func in strategies:
        df_strat = strat_func(df.copy())
        signals.append(df_strat["signal"].values)

    signal_matrix = np.array(signals)

    for i in range(len(df)):
        votes = signal_matrix[:, i]
        bull_votes = (votes == 1).sum()
        bear_votes = (votes == -1).sum()

        if bull_votes >= min_agree:
            df.iloc[i, df.columns.get_loc("combined_signal")] = 1
        elif bear_votes >= min_agree:
            df.iloc[i, df.columns.get_loc("combined_signal")] = -1

    return df


STRATEGY_POOL = [
    ("ma_9_21", lambda df: strategy_ma_crossover(df, 9, 21)),
    ("ma_21_50", lambda df: strategy_ma_crossover(df, 21, 50)),
    ("rsi_30_70", lambda df: strategy_rsi_mean_reversion(df, 30, 70)),
    ("bollinger_bounce", strategy_bollinger_bounce),
    ("breakout_20", lambda df: strategy_breakout(df, 20)),
    ("vol_1.5x", lambda df: strategy_volume_spike(df, 1.5)),
    ("ema_alignment", strategy_ema_alignment),
]


def main():
    print("=" * 70)
    print("Phase 4: Strategy Combination Analysis")
    print("=" * 70)

    symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY"]
    all_results = []

    for symbol in symbols:
        df = load_data(symbol)
        if df.empty or len(df) < 200:
            continue

        print(f"\n{'='*70}")
        print(f"  {symbol}")
        print(f"{'='*70}")

        # Test all 2-strategy combinations
        print(f"\n  2-Strategy Combinations:")
        for combo in combinations(range(len(STRATEGY_POOL)), 2):
            strat_names = [STRATEGY_POOL[i][0] for i in combo]
            strat_funcs = [STRATEGY_POOL[i][1] for i in combo]
            combo_name = " + ".join(strat_names)

            try:
                df_combo = combined_signal(df, strat_funcs, min_agree=2)
                df_combo = df_combo.rename(columns={"combined_signal": "signal"})
                stats = backtest_strategy(df_combo)

                stats["symbol"] = symbol
                stats["strategy"] = combo_name
                all_results.append(stats)

                marker = ""
                if stats["win_rate"] >= 55 and stats["sharpe"] > 0.3:
                    marker = " *** GOOD ***"

                print(f"    {combo_name:<40} trades={stats['trades']:>4}  "
                      f"WR={stats['win_rate']:>5.1f}%  "
                      f"PF={stats['profit_factor']:>5.2f}  "
                      f"Sharpe={stats['sharpe']:>6.3f}{marker}")

            except Exception as e:
                print(f"    {combo_name:<40} ERROR: {e}")

        # Test all 3-strategy combinations (top strategies only)
        print(f"\n  3-Strategy Combinations (top candidates):")
        for combo in combinations(range(len(STRATEGY_POOL)), 3):
            strat_names = [STRATEGY_POOL[i][0] for i in combo]
            strat_funcs = [STRATEGY_POOL[i][1] for i in combo]
            combo_name = " + ".join(strat_names)

            try:
                df_combo = combined_signal(df, strat_funcs, min_agree=2)
                df_combo = df_combo.rename(columns={"combined_signal": "signal"})
                stats = backtest_strategy(df_combo)

                stats["symbol"] = symbol
                stats["strategy"] = combo_name
                all_results.append(stats)

                marker = ""
                if stats["win_rate"] >= 55 and stats["sharpe"] > 0.3:
                    marker = " *** GOOD ***"

                print(f"    {combo_name:<50} trades={stats['trades']:>4}  "
                      f"WR={stats['win_rate']:>5.1f}%  "
                      f"PF={stats['profit_factor']:>5.2f}  "
                      f"Sharpe={stats['sharpe']:>6.3f}{marker}")

            except Exception as e:
                print(f"    {combo_name:<50} ERROR: {e}")

    # Sort by Sharpe
    all_results.sort(key=lambda x: x.get("sharpe", 0), reverse=True)

    # Save results
    results_df = pd.DataFrame(all_results)
    csv_path = os.path.join(REPORT_DIR, "combination_results.csv")
    results_df.to_csv(csv_path, index=False)

    # Print top 10
    print(f"\n{'='*70}")
    print("  TOP 10 COMBINATIONS BY SHARPE RATIO")
    print(f"{'='*70}")
    for i, r in enumerate(all_results[:10], 1):
        print(f"  {i}. {r['symbol']} {r['strategy']:<50} "
              f"WR={r['win_rate']}%  PF={r['profit_factor']}  "
              f"Sharpe={r['sharpe']}")

    print(f"\nFull results saved to {csv_path}")


if __name__ == "__main__":
    main()
