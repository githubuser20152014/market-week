"""Export the newsletter as a PDF by rendering the HTML edition via Playwright."""

import base64
import sys
import tempfile
from pathlib import Path

# Resolve the weekly-newsletter root so we can import build_site / intl_build_site
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# CSS injected before PDF conversion: hide web-only chrome, optimise for print
_PDF_OVERRIDES = """
<style>
  .nav-strip, .back-link, nav { display: none !important; }
  .page { box-shadow: none !important; margin: 0 !important; }
  body { background: #fff !important; }
  a { text-decoration: none !important; color: inherit !important; }
  @page { margin: 0; }
</style>
"""


def _chart_img_tag(chart_path):
    """Embed the chart PNG as a base64 data-URI <img> tag."""
    if not chart_path:
        return ""
    p = Path(chart_path)
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (
        '<div style="margin:1.5rem 0;">'
        f'<img src="data:image/png;base64,{b64}" '
        'style="width:100%;max-width:100%;display:block;" /></div>'
    )


def generate_pdf(context, chart_path, output_dir, date_str,
                 title="Framework Foundry Weekly"):
    """Render the newsletter HTML and convert to PDF via Playwright/Chromium.

    Args:
        context:    Template context dict from build_template_context.
        chart_path: Path to chart PNG (embedded as base64 data-URI).
        output_dir: Directory to save the PDF.
        date_str:   Newsletter date string (YYYY-MM-DD).
        title:      Document title (kept for API compatibility).

    Returns:
        Path to the saved PDF.
    """
    from playwright.sync_api import sync_playwright

    # Choose renderer based on edition
    if context.get("fx_rates"):
        from intl_build_site import render_html
    else:
        from build_site import render_html

    html_str = render_html(context)

    # Inject PDF CSS overrides
    html_str = html_str.replace("</head>", _PDF_OVERRIDES + "</head>", 1)

    # Inject chart image after "Week in Brief" section
    chart_tag = _chart_img_tag(chart_path)
    if chart_tag:
        marker = "<!-- INDEX SNAPSHOT"
        if marker in html_str:
            html_str = html_str.replace(marker, chart_tag + "\n\n    " + marker, 1)

    # Write HTML to a temp file so Playwright can load it with file:// (resolves fonts)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                    mode="w", encoding="utf-8") as tmp:
        tmp.write(html_str)
        tmp_path = Path(tmp.name)

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    pdf_path = output_dir / f"newsletter_{date_str}.pdf"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(tmp_path.as_uri(), wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    return pdf_path
