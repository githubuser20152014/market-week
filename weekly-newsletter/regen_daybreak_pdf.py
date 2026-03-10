#!/usr/bin/env python3
"""
regen_daybreak_pdf.py — Regenerate the daybreak PDF from the already-built site HTML.

Called by publish_daybreak.sh after build_combined_site.py so the PDF always
reflects the verified site HTML (which matches the approved .md), not the
fixture-derived HTML that was rendered at initial generation time.

Usage:
    python regen_daybreak_pdf.py 2026-03-10
"""

import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def main() -> None:
    date_str  = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    html_path = SCRIPT_DIR / 'site' / 'daily' / date_str / 'index.html'
    pdf_out   = SCRIPT_DIR / 'output'                    / f'market_day_break_{date_str}.pdf'
    downloads = SCRIPT_DIR / 'site' / 'downloads'        / f'market_day_break_{date_str}.pdf'

    if not html_path.exists():
        print(f"ERROR: {html_path} not found — run build_combined_site.py first.")
        sys.exit(1)

    from data.pdf_export import _PDF_OVERRIDES
    from playwright.sync_api import sync_playwright

    html_str  = html_path.read_text(encoding='utf-8')
    html_str  = html_str.replace('</head>', _PDF_OVERRIDES + '</head>', 1)

    with tempfile.NamedTemporaryFile(suffix='.html', delete=False,
                                    mode='w', encoding='utf-8') as tmp:
        tmp.write(html_str)
        tmp_path = Path(tmp.name)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page    = browser.new_page()
            page.goto(tmp_path.as_uri(), wait_until='networkidle')
            page.pdf(
                path=str(pdf_out),
                format='A4',
                print_background=True,
                margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            )
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    downloads.parent.mkdir(exist_ok=True)
    shutil.copy2(pdf_out, downloads)

    print(f"PDF regenerated -> {pdf_out}")
    print(f"PDF copied      -> {downloads}")


if __name__ == '__main__':
    main()
