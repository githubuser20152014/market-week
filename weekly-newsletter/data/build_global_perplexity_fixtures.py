#!/usr/bin/env python3
"""Build global edition fixtures from Perplexity-sourced weekly price data.

Writes three fixture files for the week ending DATE:
  fixtures/global_equity_DATE.json
  fixtures/global_fx_DATE.json
  fixtures/global_commodity_DATE.json

Called by the /global skill after running the four Perplexity queries.
Requires only Friday closes + weekly % changes — prev_close and
synthetic OHLCV are computed automatically.

Usage:
    python weekly-newsletter/data/build_global_perplexity_fixtures.py \\
        --date 2026-03-21 \\
        --prices '{
            "equity": {
                "sp500": 5500, "sp500_weekly_pct": -0.8,
                "dow": 44000, "dow_weekly_pct": -0.5,
                "nasdaq": 18000, "nasdaq_weekly_pct": -1.2,
                "russell2000": 2100, "russell2000_weekly_pct": -1.5,
                "ten_year_yield": 4.35, "ten_year_yield_week_start": 4.28,
                "usd_index": 104.2, "usd_index_weekly_pct": 0.3,
                "vix": 18.5, "vix_weekly_pct": 5.2,
                "dax": 22000, "dax_weekly_pct": 0.8,
                "ftse100": 9800, "ftse100_weekly_pct": -0.2,
                "cac40": 7600, "cac40_weekly_pct": 0.5,
                "eurostoxx50": 5400, "eurostoxx50_weekly_pct": 0.6,
                "nikkei": 54000, "nikkei_weekly_pct": -1.5,
                "hang_seng": 25000, "hang_seng_weekly_pct": 0.3,
                "asx200": 8200, "asx200_weekly_pct": -0.4,
                "msci_em": 1100, "msci_em_weekly_pct": 0.2
            },
            "fx": {
                "eurusd": 1.08, "eurusd_weekly_pct": 0.5,
                "gbpusd": 1.27, "gbpusd_weekly_pct": 0.3,
                "jpyusd": 0.00667, "jpyusd_weekly_pct": -0.2,
                "audusd": 0.63, "audusd_weekly_pct": 0.1,
                "chfusd": 1.12, "chfusd_weekly_pct": 0.4
            },
            "commodities": {
                "wti_crude": 72.5, "wti_crude_weekly_pct": -2.1,
                "nat_gas": 2.8, "nat_gas_weekly_pct": 1.5,
                "gold": 3200, "gold_weekly_pct": 0.8,
                "silver": 32.5, "silver_weekly_pct": 1.2,
                "us_30y_yield": 4.65, "us_30y_yield_week_start": 4.58
            }
        }'

Key notes:
  - equity/fx/commodities keys all lowercase with underscores
  - Weekly % changes: "{key}_weekly_pct" (e.g. sp500_weekly_pct)
  - For yield instruments (ten_year_yield, us_30y_yield): use "{key}_week_start"
    instead of "{key}_weekly_pct" for precise bps computation
  - JPY/USD (not USD/JPY) — ask Perplexity for JPY per USD (e.g. 0.00667)
  - Pass null for any asset Perplexity could not find
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_global_data import (
    fetch_from_perplexity_global,
    FIXTURES_DIR,
)


def main():
    parser = argparse.ArgumentParser(
        description="Build global edition fixtures from Perplexity weekly price data"
    )
    parser.add_argument("--date",      required=True,
                        help="Week-end date in YYYY-MM-DD format (typically Friday)")
    parser.add_argument("--prices",    required=True,
                        help='JSON string with "equity", "fx", "commodities" keys')
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite fixtures if they already exist")
    args = parser.parse_args()

    try:
        perplexity_data = json.loads(args.prices)
    except json.JSONDecodeError as e:
        print(f"ERROR: --prices is not valid JSON: {e}")
        sys.exit(1)

    missing = [k for k in ("equity", "fx", "commodities") if k not in perplexity_data]
    if missing:
        print(f"ERROR: --prices JSON is missing required keys: {missing}")
        sys.exit(1)

    # Check for existing fixtures
    paths = {
        "equity":     FIXTURES_DIR / f"global_equity_{args.date}.json",
        "fx":         FIXTURES_DIR / f"global_fx_{args.date}.json",
        "commodities": FIXTURES_DIR / f"global_commodity_{args.date}.json",
    }
    existing = [k for k, p in paths.items() if p.exists()]
    if existing and not args.overwrite:
        print(f"Fixtures already exist for {args.date}: {existing}")
        print("Use --overwrite to replace them.")
        sys.exit(0)

    print(f"Building global Perplexity fixtures for week ending {args.date}...")
    equity_fixture, fx_fixture, commodity_fixture = fetch_from_perplexity_global(
        args.date, perplexity_data
    )

    paths["equity"].write_text(json.dumps(equity_fixture, indent=2))
    paths["fx"].write_text(json.dumps(fx_fixture, indent=2))
    paths["commodities"].write_text(json.dumps(commodity_fixture, indent=2))

    # Summary
    print(f"\nSaved:")
    print(f"  {paths['equity'].name}      — {len(equity_fixture)} indices")
    print(f"  {paths['fx'].name}          — {len(fx_fixture)} FX pairs")
    print(f"  {paths['commodities'].name} — {len(commodity_fixture)} commodities")

    # Warn about missing assets
    from fetch_global_data import (
        _GLOBAL_EQUITY_KEY_MAP, _GLOBAL_FX_KEY_MAP, _GLOBAL_COMMODITY_KEY_MAP
    )
    eq_data = perplexity_data.get("equity", {})
    fx_data = perplexity_data.get("fx", {})
    co_data = perplexity_data.get("commodities", {})

    missing_eq = [v[0] for k, v in _GLOBAL_EQUITY_KEY_MAP.items() if eq_data.get(k) is None]
    missing_fx = [v[0] for k, v in _GLOBAL_FX_KEY_MAP.items()     if fx_data.get(k) is None]
    missing_co = [v[0] for k, v in _GLOBAL_COMMODITY_KEY_MAP.items() if co_data.get(k) is None]

    if missing_eq:
        print(f"\n  WARNING: Missing equity assets: {missing_eq}")
    if missing_fx:
        print(f"  WARNING: Missing FX pairs: {missing_fx}")
    if missing_co:
        print(f"  WARNING: Missing commodities: {missing_co}")


if __name__ == "__main__":
    main()
