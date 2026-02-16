#!/usr/bin/env python3
"""Generate the Framework Foundry Weekly newsletter."""

import argparse
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from data.fetch_data import fetch_index_data, fetch_econ_calendar
from data.process_data import process_index_data, build_template_context
from data.chart import generate_price_chart

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"


def render_newsletter(context):
    """Render the Jinja2 template with the given context."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("newsletter_template.md")
    return template.render(context)


def main():
    parser = argparse.ArgumentParser(
        description="Generate the Framework Foundry Weekly newsletter."
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
    args = parser.parse_args()

    use_mock = not args.live
    date_str = args.date

    # Fetch
    raw_indices = fetch_index_data(date_str, use_mock=use_mock)
    econ = fetch_econ_calendar(date_str, use_mock=use_mock)

    # Process
    index_data = process_index_data(raw_indices)
    context = build_template_context(index_data, econ, date_str)

    # Generate chart
    OUTPUT_DIR.mkdir(exist_ok=True)
    chart_path = generate_price_chart(raw_indices, date_str, OUTPUT_DIR)
    context["chart_path"] = chart_path.name

    # Render
    newsletter = render_newsletter(context)

    # Output
    if args.preview:
        print(newsletter)
        print(f"\nChart saved to {chart_path}")
    else:
        out_path = OUTPUT_DIR / f"newsletter_{date_str}.md"
        out_path.write_text(newsletter, encoding="utf-8")
        print(f"Newsletter saved to {out_path}")
        print(f"Chart saved to {chart_path}")


if __name__ == "__main__":
    main()
