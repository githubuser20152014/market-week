#!/usr/bin/env python3
"""Generate the Framework Foundry Weekly — Global Investor Edition."""

import argparse
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# Load API keys from config/api_keys.env if present
_ENV_FILE = Path(__file__).resolve().parent / "config" / "api_keys.env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)

from data.fetch_global_data import (
    fetch_global_equity_data,
    fetch_global_fx_data,
    fetch_global_commodity_data,
)
from data.process_global_data import (
    process_global_equity_data,
    process_global_fx_data,
    process_global_commodity_data,
    build_global_template_context,
)
from data.fetch_data import fetch_econ_calendar
from data.chart import generate_price_chart
from data.pdf_export import generate_pdf

BASE_DIR     = Path(__file__).resolve().parent
OUTPUT_DIR   = BASE_DIR / "output"
FIXTURES_DIR = BASE_DIR / "fixtures"
TEMPLATES_DIR = BASE_DIR / "templates"


def render_newsletter(context):
    """Render the Jinja2 global template with the given context."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("global_newsletter_template.md")
    return template.render(context)


def main():
    parser = argparse.ArgumentParser(
        description="Generate the Framework Foundry Weekly — Global Investor Edition."
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Data/fixture date (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--pub-date",
        default=None,
        help="Publication display date (YYYY-MM-DD). Overrides --date for header and filename.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print newsletter to stdout instead of saving.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch live data via yfinance (default: use mock fixtures).",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip price verification even in --live mode.",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also generate a PDF version of the newsletter.",
    )
    parser.add_argument(
        "--digest-dir",
        default=os.environ.get("DIGEST_DIR"),
        help="Path to news-digest directory for causal context (ContentRepo/07-Reading/news-digest). Also set via DIGEST_DIR env var.",
    )
    args = parser.parse_args()

    use_mock = not args.live
    date_str = args.date
    pub_date_str = args.pub_date if args.pub_date else date_str

    # ── Fetch ──────────────────────────────────────────────────────────────────
    print(f"Fetching global equity data ({date_str}) …")
    raw_equity = fetch_global_equity_data(date_str, use_mock=use_mock)

    print("Fetching global FX data …")
    raw_fx = fetch_global_fx_data(date_str, use_mock=use_mock)

    print("Fetching global commodity data …")
    raw_commodity = fetch_global_commodity_data(date_str, use_mock=use_mock)

    print("Fetching economic calendar …")
    econ = fetch_econ_calendar(date_str, use_mock=use_mock)

    # ── Save fixtures ──────────────────────────────────────────────────────────
    if args.live:
        FIXTURES_DIR.mkdir(exist_ok=True)
        for name, data in [
            ("global_equity",    raw_equity),
            ("global_fx",        raw_fx),
            ("global_commodity", raw_commodity),
        ]:
            path = FIXTURES_DIR / f"{name}_{date_str}.json"
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Fixture saved: {path.name}")

    # ── Process ────────────────────────────────────────────────────────────────
    print("Processing data …")
    equity_data    = process_global_equity_data(raw_equity)
    fx_data        = process_global_fx_data(raw_fx)
    commodity_data = process_global_commodity_data(raw_commodity)

    print("Generating narrative (Claude API) …")
    context = build_global_template_context(
        equity_data, fx_data, commodity_data, econ, pub_date_str,
        digest_dir=args.digest_dir,
        data_date=date_str,
    )

    # ── Chart ──────────────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(exist_ok=True)
    # Build a combined equity raw dict for charting (US indices only, keyed as
    # fetch_data.py expects: name → {symbol, data})
    chart_raw = {
        name: {"symbol": info["symbol"], "data": info["data"]}
        for name, info in raw_equity.items()
        if info.get("region") == "US" and "VIX" not in name
    }
    chart_path = generate_price_chart(
        chart_raw, pub_date_str, OUTPUT_DIR, prefix="global_chart"
    )
    context["chart_path"] = chart_path.name

    # ── Render ─────────────────────────────────────────────────────────────────
    newsletter = render_newsletter(context)

    # ── Output ─────────────────────────────────────────────────────────────────
    if args.preview:
        print(newsletter)
        print(f"\nChart saved to {chart_path}")
    else:
        out_path = OUTPUT_DIR / f"global_newsletter_{pub_date_str}.md"
        out_path.write_text(newsletter, encoding="utf-8")
        print(f"Newsletter saved to {out_path}")
        print(f"Chart saved to {chart_path}")

    # ── PDF ────────────────────────────────────────────────────────────────────
    if args.pdf:
        pdf_ctx = dict(context)
        pdf_ctx.setdefault("indices", equity_data.get("us_indices", []))
        pdf_path = generate_pdf(
            pdf_ctx, chart_path, OUTPUT_DIR, pub_date_str,
            filename=f"global_newsletter_{pub_date_str}.pdf",
        )
        print(f"PDF saved to {pdf_path}")


if __name__ == "__main__":
    main()
