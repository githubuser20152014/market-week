#!/usr/bin/env python3
"""Fetch, verify, and sanity-check Global Investor Edition data.

This script replaces the manual Perplexity process with a robust Python pipeline.
It fetches data from yfinance and cross-references it with FRED and Stooq.

Usage:
    python weekly-newsletter/data/fetch_and_verify_global.py [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# Allow importing from current directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_global_data import (
    _fetch_live_global_equity,
    _fetch_live_global_fx,
    _fetch_live_global_commodities,
    _fetch_secondary_verification_global,
    _fetch_live_futures_global,
    FIXTURES_DIR
)

@dataclass
class AssetBounds:
    min_val: float
    max_val: float

# Hard sanity bounds from global.md
SANITY_BOUNDS = {
    "S&P 500":       AssetBounds(3000, 8000),
    "Dow Jones":     AssetBounds(20000, 55000),
    "Nasdaq":        AssetBounds(8000, 25000),
    "Nikkei 225":    AssetBounds(20000, 60000),
    "Gold":          AssetBounds(1500, 6000),
    "WTI Crude Oil": AssetBounds(40, 200),
    "10Y Treasury":  AssetBounds(0.5, 8.0),
    "US 30Y":        AssetBounds(0.5, 8.0),
    "EUR/USD":       AssetBounds(0.80, 1.50),
    "JPY/USD":       AssetBounds(0.004, 0.013),
    "VIX":           AssetBounds(9, 80),
}

def _diff_pct(a, b):
    if not a or not b: return 0.0
    return abs(a - b) / abs(b) * 100

def verify_and_check(equity, fx, commodities, verification):
    """Perform verification and sanity checks."""
    fred = verification.get("fred", {})
    stooq = verification.get("stooq", {})
    
    flags = []
    
    # 1. Equity
    for name, info in equity.items():
        data = info.get("data", [])
        if not data: continue
        val = data[-1]["close"]
        
        # Sanity
        bounds = SANITY_BOUNDS.get(name)
        if bounds and (val < bounds.min_val or val > bounds.max_val):
            flags.append(f"[SANITY] {name}: {val} is outside bounds")
            
        # Verify
        sec_val = fred.get(name) or stooq.get(name)
        if sec_val:
            diff = _diff_pct(val, sec_val)
            if diff > 0.5:
                flags.append(f"[VERIFY] {name}: yfinance={val}, secondary={sec_val} (diff={diff:.2f}%)")

    # 2. FX
    for name, info in fx.items():
        data = info.get("data", [])
        if not data: continue
        val = data[-1]["close"]
        
        bounds = SANITY_BOUNDS.get(name)
        if bounds and (val < bounds.min_val or val > bounds.max_val):
            flags.append(f"[SANITY] {name}: {val} is outside bounds")
            
        sec_val = stooq.get(name)
        if sec_val:
            diff = _diff_pct(val, sec_val)
            if diff > 0.5:
                flags.append(f"[VERIFY] {name}: yfinance={val}, stooq={sec_val} (diff={diff:.2f}%)")

    # 3. Commodities
    for name, info in commodities.items():
        data = info.get("data", [])
        if not data: continue
        val = data[-1]["close"]
        
        bounds = SANITY_BOUNDS.get(name)
        if bounds and (val < bounds.min_val or val > bounds.max_val):
            flags.append(f"[SANITY] {name}: {val} is outside bounds")
            
        sec_val = fred.get(name) or stooq.get(name)
        if sec_val:
            diff = _diff_pct(val, sec_val)
            if diff > 0.5:
                flags.append(f"[VERIFY] {name}: yfinance={val}, secondary={sec_val} (diff={diff:.2f}%)")

    return flags

def _get_weekly_pct(data):
    if len(data) < 2: return None
    start = data[0]["open"]
    end = data[-1]["close"]
    if start == 0: return None
    return (end - start) / start * 100

def print_summary(date_str, equity, fx, commodities, futures, flags):
    """Print a clean summary of the fetched data."""
    print("\n" + "="*80)
    print(f" GLOBAL INVESTOR EDITION SUMMARY - Week Ending {date_str}")
    print("="*80)
    
    print(f"\nUS EQUITIES & YIELDS:")
    for name in ["S&P 500", "Dow Jones", "Nasdaq", "Russell 2000", "10Y Treasury", "USD Index", "VIX"]:
        v = equity.get(name)
        if v and v.get("data"):
            val = v["data"][-1]["close"]
            pct = _get_weekly_pct(v["data"])
            pct_str = f"{pct:+.2f}%" if pct is not None else "N/A"
            print(f"  {name:<18}: {val:>10.2f} ({pct_str})")

    print(f"\nINTERNATIONAL EQUITIES:")
    for name in ["DAX", "FTSE 100", "CAC 40", "Euro Stoxx 50", "Nikkei 225", "Hang Seng", "ASX 200", "MSCI EM"]:
        v = equity.get(name)
        if v and v.get("data"):
            val = v["data"][-1]["close"]
            pct = _get_weekly_pct(v["data"])
            pct_str = f"{pct:+.2f}%" if pct is not None else "N/A"
            print(f"  {name:<18}: {val:>10.2f} ({pct_str})")

    print(f"\nCOMMODITIES & FIXED INCOME:")
    for name in ["WTI Crude Oil", "Natural Gas", "Gold", "Silver", "US 30Y"]:
        v = commodities.get(name)
        if v and v.get("data"):
            val = v["data"][-1]["close"]
            pct = _get_weekly_pct(v["data"])
            pct_str = f"{pct:+.2f}%" if pct is not None else "N/A"
            print(f"  {name:<18}: {val:>10.2f} ({pct_str})")

    print(f"\nFX RATES:")
    for name, v in fx.items():
        if v.get("data"):
            val = v["data"][-1]["close"]
            pct = _get_weekly_pct(v["data"])
            pct_str = f"{pct:+.2f}%" if pct is not None else "N/A"
            print(f"  {name:<18}: {val:>10.5f} ({pct_str})")

    if futures:
        print(f"\nFUTURES (Current/Pre-market Sentiment):")
        for name, v in futures.items():
            pct_str = f"{v['daily_pct']:+.2f}%" if v['daily_pct'] is not None else "N/A"
            print(f"  {name:<18}: {v['price']:>10.2f} ({pct_str})")

    if flags:
        print("\n" + "!"*80)
        print(" FLAGS & WARNINGS")
        print("!"*80)
        for f in flags:
            print(f"  {f}")
    else:
        print("\n  [OK] All verification and sanity checks passed.")

def main():
    parser = argparse.ArgumentParser(description="Fetch and verify Global Investor Edition data.")
    parser.add_argument("--date", help="Week-end date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    
    print(f"==> Fetching Global Investor Edition data for week ending {date_str}...")
    try:
        equity = _fetch_live_global_equity(date_str)
        fx = _fetch_live_global_fx(date_str)
        commodities = _fetch_live_global_commodities(date_str)
        verification = _fetch_secondary_verification_global(date_str)
        futures = _fetch_live_futures_global(date_str)
    except Exception as e:
        print(f"ERROR: Fetch failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    flags = verify_and_check(equity, fx, commodities, verification)
    print_summary(date_str, equity, fx, commodities, futures, flags)
    
    if not args.no_confirm:
        print("\nDoes this data look correct? (y/n): ", end="", flush=True)
        choice = sys.stdin.readline().strip().lower()
        if choice != 'y':
            print("Aborted. Data not saved.")
            sys.exit(0)

    # Save fixtures
    for prefix, data in [
        ("global_equity", equity),
        ("global_fx", fx),
        ("global_commodity", commodities),
    ]:
        out_path = FIXTURES_DIR / f"{prefix}_{date_str}.json"
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {out_path.name}")
    
    print(f"\nSuccess! All fixtures saved for {date_str}")

if __name__ == "__main__":
    main()
