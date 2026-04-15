#!/usr/bin/env python3
"""Fetch, verify, and sanity-check Market Day Break data.

This script replaces the manual Perplexity process with a robust Python pipeline.
It fetches primary data from yfinance and cross-references it with FRED and Stooq.

Usage:
    python weekly-newsletter/data/fetch_and_verify_daybreak.py [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# Allow importing from current directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_daybreak_data import _fetch_live, FIXTURES_DIR

@dataclass
class AssetBounds:
    min_val: float
    max_val: float

# Hard sanity bounds
SANITY_BOUNDS = {
    "S&P 500":       AssetBounds(3000, 8000),
    "Dow Jones":     AssetBounds(20000, 55000),
    "Nasdaq":        AssetBounds(8000, 25000),
    "Russell 2000":  AssetBounds(1000, 4000),
    "Gold":          AssetBounds(1500, 6000),
    "WTI Crude Oil": AssetBounds(40, 200),
    "10Y Treasury":  AssetBounds(0.5, 8.0),
    "Nikkei 225":    AssetBounds(20000, 65000),
    "EUR/USD":       AssetBounds(0.80, 1.50),
    "USD/JPY":       AssetBounds(80, 200),
}

def _diff_pct(a, b):
    if not a or not b: return 0.0
    return abs(a - b) / abs(b) * 100

def verify_and_check(payload: dict):
    """Perform verification and sanity checks on the payload."""
    verification = payload.get("verification", {})
    fred = verification.get("fred", {})
    stooq = verification.get("stooq", {})
    
    flags = []
    
    # 1. US Closes
    for name, entry in payload.get("us_close", {}).items():
        val = entry.get("close")
        if val is None: continue
        
        # Sanity check
        bounds = SANITY_BOUNDS.get(name)
        if bounds and (val < bounds.min_val or val > bounds.max_val):
            flags.append(f"[SANITY] {name}: {val} is outside bounds ({bounds.min_val}-{bounds.max_val})")
            
        # Cross-verification
        sec_val = fred.get(name) or stooq.get(name)
        if sec_val:
            diff = _diff_pct(val, sec_val)
            if diff > 0.5:
                flags.append(f"[VERIFY] {name}: yfinance={val}, secondary={sec_val} (diff={diff:.2f}%)")

    # 2. Intl Overnight
    for name, entry in payload.get("intl_overnight", {}).items():
        val = entry.get("close")
        if val is None: continue
        
        bounds = SANITY_BOUNDS.get(name)
        if bounds and (val < bounds.min_val or val > bounds.max_val):
            flags.append(f"[SANITY] {name}: {val} is outside bounds")
            
        sec_val = stooq.get(name)
        if sec_val:
            diff = _diff_pct(val, sec_val)
            if diff > 1.0: # Intl indices can have slightly more drift
                flags.append(f"[VERIFY] {name}: yfinance={val}, stooq={sec_val} (diff={diff:.2f}%)")

    # 3. FX
    for name, entry in payload.get("fx", {}).items():
        val = entry.get("rate")
        if val is None: continue
        
        bounds = SANITY_BOUNDS.get(name)
        if bounds and (val < bounds.min_val or val > bounds.max_val):
            flags.append(f"[SANITY] {name}: {val} is outside bounds")
            
        sec_val = stooq.get(name)
        if sec_val:
            diff = _diff_pct(val, sec_val)
            if diff > 0.5:
                flags.append(f"[VERIFY] {name}: yfinance={val}, stooq={sec_val} (diff={diff:.2f}%)")

    return flags

def print_summary(payload: dict, flags: list):
    """Print a clean summary of the fetched data."""
    print("\n" + "="*80)
    print(f" MARKET DATA SUMMARY - {payload['meta']['date']}")
    print("="*80)
    
    print(f"\nUS CLOSES (Yesterday):")
    for name, v in payload["us_close"].items():
        change = f"{v['daily_pct']:+.2f}%" if v['daily_pct'] is not None else "N/A"
        print(f"  {name:<18}: {v['close']:>10.2f} ({change})")

    print(f"\nFUTURES (Pre-market):")
    for name, v in payload["futures"].items():
        change = f"{v['daily_pct']:+.2f}%" if v['daily_pct'] is not None else "N/A"
        print(f"  {name:<18}: {v['price']:>10.2f} ({change})")

    print(f"\nINTL OVERNIGHT:")
    for name, v in payload["intl_overnight"].items():
        if v['close']:
            change = f"{v['daily_pct']:+.2f}%" if v['daily_pct'] is not None else "N/A"
            print(f"  {name:<18}: {v['close']:>10.2f} ({change}) [{v['status']}]")
        else:
            print(f"  {name:<18}: {'N/A':>10} [{v['status']}]")

    print(f"\nFX RATES:")
    for name, v in payload["fx"].items():
        change = f"{v['daily_pct']:+.2f}%" if v['daily_pct'] is not None else "N/A"
        print(f"  {name:<18}: {v['rate']:>10.5f} ({change})")

    if flags:
        print("\n" + "!"*80)
        print(" FLAGS & WARNINGS")
        print("!"*80)
        for f in flags:
            print(f"  {f}")
    else:
        print("\n  [OK] All verification and sanity checks passed.")

def main():
    parser = argparse.ArgumentParser(description="Fetch and verify Market Day Break data.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    
    print(f"==> Fetching Market Day Break data for {date_str}...")
    try:
        payload = _fetch_live(date_str, include_secondaries=True)
    except Exception as e:
        print(f"ERROR: Fetch failed: {e}")
        sys.exit(1)

    flags = verify_and_check(payload)
    print_summary(payload, flags)
    
    if not args.no_confirm:
        print("\nDoes this data look correct? (y/n): ", end="", flush=True)
        choice = sys.stdin.readline().strip().lower()
        if choice != 'y':
            print("Aborted. Data not saved.")
            sys.exit(0)

    # Clean up verification data before saving
    if "verification" in payload:
        del payload["verification"]
    
    payload["meta"]["generation_source"] = "verified_code"
    
    out_path = FIXTURES_DIR / f"daybreak_{date_str}.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    
    print(f"\nSuccess! Fixture saved to {out_path}")

if __name__ == "__main__":
    main()
