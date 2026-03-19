#!/usr/bin/env python3
"""Generate the Framework Foundry The Morning Brief daily edition.

Typical 6 AM EST run:
    python generate_market_day_break.py --live --pdf

Backfill:
    python generate_market_day_break.py --date 2026-03-03 --live --pdf

Preview (no file saved):
    python generate_market_day_break.py --preview
"""

import argparse
import json
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from data.fetch_daybreak_data import fetch_daybreak_data
from data.daybreak_process_data import (
    build_daybreak_context,
    generate_linkedin_post,
    generate_x_post,
    generate_substack_post,
    _generate_post_title,
)
from data.pdf_export import generate_pdf

BASE_DIR     = Path(__file__).resolve().parent
OUTPUT_DIR   = BASE_DIR / "output"
FIXTURES_DIR = BASE_DIR / "fixtures"
TEMPLATES_DIR = BASE_DIR / "templates"


def main():
    parser = argparse.ArgumentParser(
        description="Generate the Framework Foundry The Morning Brief daily edition."
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Brief date (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print to stdout instead of saving.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch live data via yfinance + Finnhub (default: nearest fixture).",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also generate a PDF version.",
    )
    parser.add_argument(
        "--md-only",
        action="store_true",
        help="Save the Markdown only — skip LinkedIn, X, Substack, and PDF.",
    )
    parser.add_argument(
        "--no-rewrite-md",
        action="store_true",
        help="Skip writing the .md file (use existing approved MD) — generate social posts and PDF only.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Cross-check prices against FRED + Stooq before generating.",
    )
    args = parser.parse_args()

    use_mock = not args.live
    date_str = args.date

    # ── Fetch ─────────────────────────────────────────────────────────────────
    raw = fetch_daybreak_data(date_str, use_mock=use_mock)

    # ── Price verification ─────────────────────────────────────────────────────
    if args.verify or (args.live and not getattr(args, "no_verify", False)):
        from data.verify_prices import verify_prices_daybreak
        verify_prices_daybreak(raw, date_str)

    # ── Persist live data as fixture ──────────────────────────────────────────
    if args.live:
        FIXTURES_DIR.mkdir(exist_ok=True)
        fixture_path = FIXTURES_DIR / f"daybreak_{date_str}.json"
        fixture_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        print(f"Fixture saved -> {fixture_path}")

    # ── Process ───────────────────────────────────────────────────────────────
    context = build_daybreak_context(raw)

    # ── Render (Markdown via Jinja2) ──────────────────────────────────────────
    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.preview:
        # Render the HTML to stdout for quick inspection
        import sys
        from daybreak_build_site import render_html
        html = render_html(context)
        sys.stdout.buffer.write(html.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        return

    # Save Markdown
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    # Use daybreak template if it exists, otherwise render HTML only
    md_path = OUTPUT_DIR / f"market_day_break_{date_str}.md"
    if args.no_rewrite_md:
        print(f"Skipping MD write — using existing approved {md_path.name}")
    else:
        try:
            template = env.get_template("daybreak_template.md")
            md = template.render(context)
            md_path.write_text(md, encoding="utf-8")
            print(f"Newsletter saved -> {md_path}")
        except Exception:
            # Fallback: save minimal Markdown
            md_path.write_text(
                f"# The Morning Brief - {date_str}\n\n{context['narrative']}\n",
                encoding="utf-8"
            )
            print(f"Newsletter saved (minimal) -> {md_path}")

    if args.md_only:
        print("MD-only mode — skipping social posts and PDF.")
        return

    # ── Email subject (sidecar file read by send_email.py) ────────────────────
    title_path = OUTPUT_DIR / f"title_{date_str}.txt"
    title_path.write_text(_generate_post_title(context), encoding="utf-8")

    # ── LinkedIn post ─────────────────────────────────────────────────────────
    import warnings
    with warnings.catch_warnings(record=True) as _w:
        warnings.simplefilter("always")
        linkedin_post = generate_linkedin_post(context)
    linkedin_path = OUTPUT_DIR / f"linkedin_{date_str}.txt"
    linkedin_path.write_text(linkedin_post, encoding="utf-8")
    char_count = len(linkedin_post)
    limit_note = f" *** OVER LIMIT by {char_count - 3000} chars ***" if char_count > 3000 else ""
    print(f"LinkedIn post saved -> {linkedin_path}  ({char_count}/3,000 chars{limit_note})")

    # ── X (Twitter) thread ────────────────────────────────────────────────────
    with warnings.catch_warnings(record=True) as _wx:
        warnings.simplefilter("always")
        x_post = generate_x_post(context)
    x_path = OUTPUT_DIR / f"x_{date_str}.txt"
    x_path.write_text(x_post, encoding="utf-8")
    for w in _wx:
        print(f"  [warn] {w.message}")
    print(f"X thread saved -> {x_path}  ({len(x_post)} chars total)")

    # ── Substack draft ────────────────────────────────────────────────────────
    substack_post = generate_substack_post(context)
    substack_path = OUTPUT_DIR / f"substack_{date_str}.html"
    substack_path.write_text(substack_post, encoding="utf-8")
    print(f"Substack draft saved -> {substack_path}")

    # ── PDF export ────────────────────────────────────────────────────────────
    if args.pdf:
        pdf_filename = f"market_day_break_{date_str}.pdf"
        pdf_path = generate_pdf(
            context,
            chart_path=None,
            output_dir=OUTPUT_DIR,
            date_str=date_str,
            title="Framework Foundry - The Morning Brief",
            filename=pdf_filename,
        )
        print(f"PDF saved -> {pdf_path}")


if __name__ == "__main__":
    main()
