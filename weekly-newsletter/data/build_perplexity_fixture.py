#!/usr/bin/env python3
"""Build a daybreak fixture from Perplexity-sourced price data.

Called by the /daybreak skill after running the three Perplexity queries.
Handles prev_close lookup, daily_pct computation, econ calendar, and news
automatically — Claude only needs to pass the extracted prices.

Usage:
    python weekly-newsletter/data/build_perplexity_fixture.py \\
        --date 2026-03-21 \\
        --prices '{
            "us":   {"sp500": 5500, "dow": 44000, "nasdaq": 18000, ...},
            "intl": {"nikkei": null, "nikkei_note": "Holiday", "hang_seng": 25000, ...},
            "fx":   {"eurusd": 1.08, "gbpusd": 1.27, "usdjpy": 150.5, ...}
        }'

Output:
    weekly-newsletter/fixtures/daybreak_DATE.json

Keys for --prices JSON:
  us:   sp500, dow, nasdaq, russell2000, gold_spot, ten_year_yield,
        usd_index, wti_crude,
        sp_futures, nasdaq_futures, dow_futures, gold_futures, wti_futures
  intl: nikkei, hang_seng, kospi, nifty50, asx200,
        dax, ftse100, cac40, eurostoxx50
        (append _note to any key for a session/holiday note, e.g. nikkei_note)
  fx:   eurusd, gbpusd, usdjpy, audusd, usdcnh, chfusd

Pass null for any price Perplexity could not find or for holiday-closed markets.
"""

import argparse
import json
import sys
from pathlib import Path

# Allow importing from the same data/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_daybreak_data import fetch_from_perplexity, FIXTURES_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Build daybreak fixture from Perplexity price data"
    )
    parser.add_argument("--date",      required=True,
                        help="Date in YYYY-MM-DD format (the brief date)")
    parser.add_argument("--prices",    required=True,
                        help='JSON string with "us", "intl", "fx" keys')
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite fixture if it already exists")
    args = parser.parse_args()

    # Parse and validate the prices JSON
    try:
        perplexity_data = json.loads(args.prices)
    except json.JSONDecodeError as e:
        print(f"ERROR: --prices is not valid JSON: {e}")
        sys.exit(1)

    missing = [k for k in ("us", "intl", "fx") if k not in perplexity_data]
    if missing:
        print(f"ERROR: --prices JSON is missing required keys: {missing}")
        sys.exit(1)

    out_path = FIXTURES_DIR / f"daybreak_{args.date}.json"
    if out_path.exists() and not args.overwrite:
        print(f"Fixture already exists: {out_path}")
        print("Use --overwrite to replace it.")
        sys.exit(0)

    print(f"Building Perplexity fixture for {args.date}...")
    payload = fetch_from_perplexity(args.date, perplexity_data)

    out_path.write_text(json.dumps(payload, indent=2))

    # Summary
    ec = payload["econ_calendar"]
    print(f"\nSaved: {out_path}")
    print(f"  generation_source : perplexity")
    print(f"  us_close assets   : {len(payload['us_close'])}")
    print(f"  intl indices      : {len(payload['intl_overnight'])}")
    print(f"  fx pairs          : {len(payload['fx'])}")
    print(f"  futures           : {len(payload['futures'])}")
    print(f"  econ events       : yesterday={len(ec['yesterday'])}, today={len(ec['today'])}")
    print(f"  news items        : {len(payload['market_news'])}")

    # Warn about any null prices
    nulls = [name for name, v in payload["us_close"].items() if v.get("close") is None]
    if nulls:
        print(f"\n  WARNING: Missing US closes: {nulls}")
    nulls_intl = [name for name, v in payload["intl_overnight"].items()
                  if v.get("close") is None and v.get("status") != "holiday"]
    if nulls_intl:
        print(f"  WARNING: Missing intl closes (non-holiday): {nulls_intl}")


if __name__ == "__main__":
    main()
