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
import re
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


def _override_from_approved_md(ctx: dict, md_path: Path) -> dict:
    """Read the approved .md file and override narrative fields in ctx.

    Called when --no-rewrite-md is set so that social posts and the email
    subject are generated from the human-approved content, not an empty context.
    """
    if not md_path.exists():
        return ctx

    md = md_path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current, buf = None, []
    for line in md.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf)
            current, buf = line[3:].strip(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf)

    def _paras(text: str) -> str:
        paras, block = [], []
        for line in text.splitlines():
            s = line.strip()
            if not s or s == "---":
                if block:
                    paras.append(" ".join(block))
                    block = []
            else:
                block.append(s)
        if block:
            paras.append(" ".join(block))
        return "\n\n".join(paras)

    if "The Brief" in sections:
        text = _paras(sections["The Brief"])
        if text:
            ctx["narrative"] = text
            ctx["brief_body"] = text

    if "What it means for you" in sections:
        text = _paras(sections["What it means for you"])
        if text:
            ctx["investor_section"] = text

    if "The One Trade" in sections:
        ot = sections["The One Trade"]
        ticker = direction = thesis = confirm = risk = None
        for line in ot.splitlines():
            s = line.strip()
            if not s:
                continue
            m = re.match(r"\*?\*?\[([A-Z0-9]+)\]\([^)]+\)\s*[—–-]+\s*(.+?)\*?\*?$", s)
            if m and ticker is None:
                ticker = m.group(1).strip()
                direction = m.group(2).strip().rstrip("*")
                continue
            if s.startswith("*") and s.endswith("*") and thesis is None:
                thesis = s.strip("*").strip()
                continue
            m2 = re.match(r"\*?\*?Confirms:\*?\*?\s*(.*)", s)
            if m2 and confirm is None:
                confirm = m2.group(1).strip()
                continue
            m3 = re.match(r"\*?\*?Risk:\*?\*?\s*(.*)", s)
            if m3 and risk is None:
                risk = m3.group(1).strip()
        if ticker and direction:
            ctx["one_trade"] = {
                "ticker": ticker, "direction": direction,
                "thesis": thesis or "", "confirm": confirm or "", "risk": risk or "",
            }

    if "Positioning Notes" in sections:
        tips = [re.sub(r"^[-*]\s+", "", l.strip())
                for l in sections["Positioning Notes"].splitlines()
                if re.match(r"^[-*]\s", l.strip())]
        if tips:
            ctx["tips"] = tips

    return ctx

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
    # Skip Claude API when --no-rewrite-md: approved .md is the content source.
    context = build_daybreak_context(raw, use_claude=not args.no_rewrite_md)

    # ── Render (Markdown via Jinja2) ──────────────────────────────────────────
    OUTPUT_DIR.mkdir(exist_ok=True)
    md_path = OUTPUT_DIR / f"market_day_break_{date_str}.md"

    # When not rewriting the MD, load the approved content into context so
    # social posts and email are built from the human-reviewed text, not empty strings.
    if args.no_rewrite_md:
        context = _override_from_approved_md(context, md_path)

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

    # ── Email subject (sidecar file read by send_email.py) ────────────────────
    title_path = OUTPUT_DIR / f"title_{date_str}.txt"
    subject_text = context.get("email_subject") or _generate_post_title(context)
    title_path.write_text(subject_text, encoding="utf-8")
    print(f"Email subject saved -> {title_path}")

    if args.md_only:
        print("MD-only mode — skipping social posts and PDF.")
        return

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
