#!/usr/bin/env python3
"""
TradeKnox Data Cross-Validation Script
Compares data across yfinance and Dukascopy sources.

Usage:
    python scripts/cross_validate.py              # Validate all pairs
    python scripts/cross_validate.py --pair XAUUSD  # Validate specific pair
"""

import os
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
YFINANCE_DIR = DATA_DIR / "yfinance"
DUKASCOPY_DIR = DATA_DIR / "dukascopy"

PAIRS = ["XAUUSD", "GBPJPY", "EURUSD", "GBPUSD", "USDJPY"]


def load_data(source_dir: Path, pair: str, interval: str) -> pd.DataFrame:
    """Load data from CSV file."""
    filename = f"{pair}_{interval}.csv"
    filepath = source_dir / filename

    if not filepath.exists():
        print(f"  WARNING: File not found: {filepath}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        print(f"  Loaded {len(df)} rows from {filepath.name}")
        return df
    except Exception as e:
        print(f"  ERROR loading {filepath}: {e}")
        return pd.DataFrame()


def validate_pair(pair: str) -> dict:
    """Validate data for a single pair across sources."""
    print(f"\n{'='*60}")
    print(f"VALIDATING: {pair}")
    print(f"{'='*60}")

    results = {
        "pair": pair,
        "yfinance_rows": 0,
        "dukascopy_rows": 0,
        "yfinance_range": None,
        "dukascopy_range": None,
        "price_diff_pct": None,
        "status": "UNKNOWN",
    }

    # Load yfinance data
    yf_df = load_data(YFINANCE_DIR, pair, "daily")
    if not yf_df.empty:
        results["yfinance_rows"] = len(yf_df)
        results["yfinance_range"] = f"{yf_df.index[0].date()} to {yf_df.index[-1].date()}"

    # Load Dukascopy data
    dc_df = load_data(DUKASCOPY_DIR, pair, "hourly")
    if not dc_df.empty:
        results["dukascopy_rows"] = len(dc_df)
        results["dukascopy_range"] = f"{dc_df.index[0].date()} to {dc_df.index[-1].date()}"

    # Compare prices if both sources have data
    if not yf_df.empty and not dc_df.empty:
        # Resample Dukascopy to daily for comparison
        dc_daily = dc_df.resample("1D").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
        }).dropna()

        # Find common dates
        common_dates = yf_df.index.intersection(dc_daily.index)

        if len(common_dates) > 0:
            yf_close = yf_df.loc[common_dates, "close"]
            dc_close = dc_daily.loc[common_dates, "close"]

            # Calculate percentage difference
            diff = abs(yf_close - dc_close) / dc_close * 100
            avg_diff = diff.mean()
            max_diff = diff.max()

            results["price_diff_pct"] = f"avg: {avg_diff:.4f}%, max: {max_diff:.4f}%"

            # Determine status
            if avg_diff < 0.1:
                results["status"] = "PASS"
            elif avg_diff < 0.5:
                results["status"] = "WARNING"
            else:
                results["status"] = "FAIL"

            print(f"\n  Price Comparison (Close prices):")
            print(f"    Common dates: {len(common_dates)}")
            print(f"    Avg difference: {avg_diff:.4f}%")
            print(f"    Max difference: {max_diff:.4f}%")
            print(f"    Status: {results['status']}")
        else:
            results["status"] = "NO_OVERLAP"
            print(f"\n  WARNING: No common dates between sources")
    else:
        results["status"] = "INCOMPLETE_DATA"
        print(f"\n  WARNING: Missing data from one or both sources")

    # Print summary
    print(f"\n  Summary:")
    print(f"    yfinance: {results['yfinance_rows']} rows ({results['yfinance_range']})")
    print(f"    Dukascopy: {results['dukascopy_rows']} rows ({results['dukascopy_range']})")
    print(f"    Price diff: {results['price_diff_pct']}")
    print(f"    Status: {results['status']}")

    return results


def generate_report(all_results: list):
    """Generate summary report."""
    print(f"\n{'='*60}")
    print("CROSS-VALIDATION REPORT")
    print(f"{'='*60}")

    # Count statuses
    statuses = [r["status"] for r in all_results]
    pass_count = statuses.count("PASS")
    warning_count = statuses.count("WARNING")
    fail_count = statuses.count("FAIL")
    incomplete_count = statuses.count("INCOMPLETE_DATA") + statuses.count("NO_OVERLAP")

    print(f"\nOverall Results:")
    print(f"  PASS: {pass_count}/{len(all_results)}")
    print(f"  WARNING: {warning_count}/{len(all_results)}")
    print(f"  FAIL: {fail_count}/{len(all_results)}")
    print(f"  INCOMPLETE: {incomplete_count}/{len(all_results)}")

    # Recommendations
    print(f"\nRecommendations:")
    if pass_count == len(all_results):
        print("  All pairs validated successfully. Data is consistent across sources.")
        print("  Ready to backtest strategies on both datasets.")
    elif warning_count > 0:
        print("  Some pairs have minor price differences (< 0.5%).")
        print("  This is normal due to different data providers and timestamps.")
        print("  Proceed with caution when comparing strategy results.")
    else:
        print("  Data validation issues detected.")
        print("  Check the data files and re-download if necessary.")

    # Save report to file
    report_path = DATA_DIR / "validation_report.txt"
    with open(report_path, "w") as f:
        f.write("TradeKnox Data Cross-Validation Report\n")
        f.write(f"Generated: {pd.Timestamp.now()}\n\n")
        f.write(f"Pairs Validated: {len(all_results)}\n")
        f.write(f"PASS: {pass_count}\n")
        f.write(f"WARNING: {warning_count}\n")
        f.write(f"FAIL: {fail_count}\n")
        f.write(f"INCOMPLETE: {incomplete_count}\n\n")

        for r in all_results:
            f.write(f"\n{r['pair']}:\n")
            f.write(f"  Status: {r['status']}\n")
            f.write(f"  yfinance: {r['yfinance_rows']} rows ({r['yfinance_range']})\n")
            f.write(f"  Dukascopy: {r['dukascopy_rows']} rows ({r['dukascopy_range']})\n")
            f.write(f"  Price diff: {r['price_diff_pct']}\n")

    print(f"\nReport saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Cross-validate forex data")
    parser.add_argument(
        "--pair",
        choices=PAIRS,
        default=None,
        help="Validate specific pair (default: all)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("TradeKnox Data Cross-Validation")
    print("=" * 60)

    pairs_to_validate = [args.pair] if args.pair else PAIRS
    all_results = []

    for pair in pairs_to_validate:
        result = validate_pair(pair)
        all_results.append(result)

    generate_report(all_results)


if __name__ == "__main__":
    main()
