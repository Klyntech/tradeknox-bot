"""
Master Script: Run Full Research Pipeline
Downloads data, analyzes market profile, discovers strategies, tests combinations.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    start = time.time()

    print("\n" + "=" * 70)
    print("  TRADEKNOX RESEARCH PIPELINE")
    print("=" * 70 + "\n")

    # Phase 1: Download Data
    print("\n>>> PHASE 1: Downloading Historical Data")
    print("-" * 50)
    from download_data import main as download_main
    download_main()

    # Phase 2: Market Profile
    print("\n\n>>> PHASE 2: Market Character Profile")
    print("-" * 50)
    from market_profile import main as profile_main
    profile_main()

    # Phase 3: Strategy Discovery
    print("\n\n>>> PHASE 3: Strategy Discovery")
    print("-" * 50)
    from strategy_tester import main as tester_main
    tester_main()

    # Phase 4: Combination Analysis
    print("\n\n>>> PHASE 4: Strategy Combinations")
    print("-" * 50)
    from combination_test import main as combo_main
    combo_main()

    elapsed = time.time() - start
    print(f"\n{'='*70}")
    print(f"  RESEARCH COMPLETE — {elapsed:.1f}s")
    print(f"{'='*70}")
    print(f"\nReports saved to research/data/:")
    print(f"  - market_profile.txt")
    print(f"  - strategy_results.csv")
    print(f"  - combination_results.csv")


if __name__ == "__main__":
    main()
