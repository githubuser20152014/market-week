#!/usr/bin/env python3
"""Generate the Framework Foundry Weekly — International Edition newsletter."""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from data.fetch_intl_data import fetch_intl_index_data, fetch_intl_fx_data, fetch_intl_econ_calendar
from data.intl_process_data import process_intl_index_data, process_fx_data, build_intl_template_context
from data.chart import generate_price_chart
from data.pdf_export import generate_pdf

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"


def _load_week_daybreak_data(date_str):
    """Load and aggregate daybreak fixture data for the newsletter week."""
    target = date.fromisoformat(date_str)
    monday = target - timedelta(days=target.weekday())

    fixtures_dir = BASE_DIR / "fixtures"
    news_items  = []
    week_events = []

    for offset in range(5):  # Mon–Fri
        day = monday + timedelta(days=offset)
        if day > target:
            break
        fixture_path = fixtures_dir / f"daybreak_{day.isoformat()}.json"
        if not fixture_path.exists():
            continue
        try:
            data = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        for item in data.get("market_news", []):
            news_items.append({
                "headline": item.get("headline", ""),
                "summary":  item.get("summary", ""),
            })

        for ev in data.get("econ_calendar", {}).get("yesterday", []):
            week_events.append(ev)

    return {"news_items": news_items, "week_events": week_events}


def render_newsletter(context):
    """Render the international Jinja2 template with the given context."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("intl_newsletter_template.md")
    return template.render(context)


def main():
    parser = argparse.ArgumentParser(
        description="Generate the Framework Foundry Weekly International Edition newsletter."
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Newsletter date (YYYY-MM-DD). Default: today.",
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
        "--pdf",
        action="store_true",
        help="Also generate a PDF version of the newsletter.",
    )
    args = parser.parse_args()

    use_mock = not args.live
    date_str = args.date

    # Fetch
    raw_indices = fetch_intl_index_data(date_str, use_mock=use_mock)
    raw_fx = fetch_intl_fx_data(date_str, use_mock=use_mock)
    econ = fetch_intl_econ_calendar(date_str, use_mock=use_mock)

    # Persist live data as fixtures so build_combined_site.py uses the same prices
    if args.live:
        fixtures_dir = BASE_DIR / "fixtures"
        fixtures_dir.mkdir(exist_ok=True)
        (fixtures_dir / f"intl_indices_{date_str}.json").write_text(
            json.dumps(raw_indices, indent=2), encoding="utf-8"
        )
        (fixtures_dir / f"intl_fx_{date_str}.json").write_text(
            json.dumps(raw_fx, indent=2), encoding="utf-8"
        )
        print(f"Fixtures saved to {fixtures_dir}/intl_indices_{date_str}.json + intl_fx_{date_str}.json")

    # Load aggregated daybreak fixture data for the week (read-only, never fails)
    daybreak_context = _load_week_daybreak_data(date_str)

    # Process
    index_data = process_intl_index_data(raw_indices)
    fx_data = process_fx_data(raw_fx)
    context = build_intl_template_context(index_data, fx_data, econ, date_str, daybreak_context=daybreak_context)

    # Generate chart (indices only — keeps the chart readable)
    OUTPUT_DIR.mkdir(exist_ok=True)
    intl_chart_path = generate_price_chart(
        raw_indices, date_str, OUTPUT_DIR,
        title="Framework Foundry Weekly - International Edition -- Performance (% Change from Monday Open)",
        prefix="intl_chart",
    )
    context["chart_path"] = intl_chart_path.name

    # Render
    newsletter = render_newsletter(context)

    # Output
    if args.preview:
        print(newsletter)
        print(f"\nChart saved to {intl_chart_path}")
    else:
        out_path = OUTPUT_DIR / f"intl_newsletter_{date_str}.md"
        out_path.write_text(newsletter, encoding="utf-8")
        print(f"Newsletter saved to {out_path}")
        print(f"Chart saved to {intl_chart_path}")

    # PDF export
    if args.pdf:
        intl_pdf_path = generate_pdf(
            context, intl_chart_path, OUTPUT_DIR, date_str,
            title="Framework Foundry Weekly - International Edition",
            filename=f"intl_newsletter_{date_str}.pdf",
        )
        print(f"PDF saved to {intl_pdf_path}")


if __name__ == "__main__":
    main()
