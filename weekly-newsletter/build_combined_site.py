#!/usr/bin/env python3
"""Build the unified static site for Cloudflare Pages deployment.

Run from weekly-newsletter/:
    python build_combined_site.py           # mock data
    python build_combined_site.py --live    # live API data
"""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from build_site import render_html as render_us_html
from intl_build_site import render_html as render_intl_html
from data.fetch_data import fetch_index_data, fetch_econ_calendar
from data.process_data import process_index_data, build_template_context
from data.fetch_intl_data import fetch_intl_index_data, fetch_intl_fx_data, fetch_intl_econ_calendar
from data.intl_process_data import process_intl_index_data, process_fx_data, build_intl_template_context

OUTPUT_DIR = BASE_DIR / "output"
SITE_DIR = BASE_DIR / "site"

# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """\
  :root {
    --navy:      #0f1f3d;
    --accent:    #4a7fb5;
    --accent-lt: #7aabda;
    --white:     #ffffff;
    --off-white: #f5f4f0;
    --text:      #1a1a2e;
    --border:    #ddd8cc;
    --muted:     #6b7280;
    --green:     #2a7d4f;
    --red:       #b91c1c;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #dde3ea;
    font-family: 'Source Serif 4', Georgia, serif;
    color: var(--text);
    padding: 32px 16px;
    min-height: 100vh;
  }

  .page {
    max-width: 860px;
    margin: 0 auto;
    background: var(--white);
    box-shadow: 0 8px 48px rgba(0,0,0,0.18);
  }

  /* HEADER */
  .header {
    background: var(--navy);
    position: relative;
    overflow: hidden;
  }

  .header::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
    background-size: 28px 28px;
  }

  .header-inner {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 28px 40px 24px;
    gap: 24px;
  }

  .logo-icon { flex-shrink: 0; width: 64px; height: 64px; }
  .logo-text { flex: 1; }

  .logo-name-framework {
    font-family: 'Cormorant Garamond', serif;
    font-size: 30px;
    font-weight: 600;
    letter-spacing: 4px;
    color: var(--white);
    display: block;
    line-height: 1;
  }

  .logo-name-foundry {
    font-family: 'Raleway', sans-serif;
    font-size: 14px;
    font-weight: 300;
    letter-spacing: 12px;
    color: var(--accent);
    display: block;
    margin-top: 5px;
    line-height: 1;
  }

  .logo-rule {
    height: 1px;
    background: rgba(255,255,255,0.15);
    margin: 8px 0 6px;
  }

  .logo-tagline {
    font-family: 'Raleway', sans-serif;
    font-size: 8.5px;
    font-weight: 300;
    letter-spacing: 3.5px;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
  }

  .header-accent {
    height: 3px;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent-lt) 50%, transparent 100%);
  }

  /* NAV STRIP */
  .nav-strip {
    background: var(--accent);
    padding: 7px 40px;
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 3px;
    color: rgba(255,255,255,0.9);
    text-transform: uppercase;
  }

  /* CONTENT */
  .content { padding: 40px; }

  .section-label {
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
  }

  /* HERO CARDS */
  .hero-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 48px;
  }

  .hero-card {
    border: 1px solid var(--border);
    border-top: 4px solid var(--accent);
    background: var(--off-white);
    padding: 24px;
  }

  .hero-card-edition {
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 6px;
  }

  .hero-card-date {
    font-family: 'Cormorant Garamond', serif;
    font-size: 22px;
    font-weight: 300;
    color: var(--navy);
    margin-bottom: 16px;
  }

  .hero-idx-row {
    display: flex;
    justify-content: space-between;
    font-family: 'Raleway', sans-serif;
    font-size: 12px;
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
    color: var(--navy);
  }

  .hero-idx-row:last-child { border-bottom: none; }

  .pct-pos { color: var(--green); font-weight: 600; }
  .pct-neg { color: var(--red);   font-weight: 600; }

  .hero-cta {
    display: inline-block;
    background: var(--navy);
    color: var(--white);
    font-family: 'Raleway', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 10px 20px;
    text-decoration: none;
    margin-top: 18px;
  }

  .hero-cta:hover { background: var(--accent); }

  .hero-card.no-issue {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    color: var(--muted);
    font-family: 'Raleway', sans-serif;
    font-size: 12px;
    letter-spacing: 1px;
  }

  /* ARCHIVE TABLE */
  .archive-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Raleway', sans-serif;
    font-size: 13px;
  }

  .archive-table thead tr { background: var(--navy); color: var(--white); }
  .archive-table thead th {
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
    letter-spacing: 1px;
    font-size: 10px;
    text-transform: uppercase;
  }

  .archive-table tbody tr { border-bottom: 1px solid var(--border); }
  .archive-table tbody tr:nth-child(even) { background: var(--off-white); }
  .archive-table tbody td { padding: 10px 14px; vertical-align: middle; }

  .archive-link {
    display: inline-block;
    font-family: 'Raleway', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--accent);
    text-decoration: none;
    border: 1px solid var(--accent);
    padding: 3px 10px;
    margin-right: 6px;
    white-space: nowrap;
  }

  .archive-link:hover { background: var(--accent); color: var(--white); }
  .archive-link.pdf { color: var(--muted); border-color: var(--muted); }
  .archive-link.pdf:hover { background: var(--muted); color: var(--white); }

  /* FOOTER */
  .footer {
    background: var(--navy);
    padding: 16px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 0;
  }

  .footer-logo {
    font-family: 'Cormorant Garamond', serif;
    font-size: 13px;
    font-weight: 400;
    letter-spacing: 2px;
    color: rgba(255,255,255,0.5);
  }

  .footer-logo span { color: var(--accent); }

  .footer-disclaimer {
    font-family: 'Raleway', sans-serif;
    font-size: 8.5px;
    color: rgba(255,255,255,0.3);
    letter-spacing: 0.5px;
    text-align: right;
    max-width: 380px;
    line-height: 1.6;
  }

  @media (max-width: 600px) {
    .header-inner { padding: 20px 20px 16px; flex-wrap: wrap; }
    .content { padding: 24px 20px; }
    .hero-grid { grid-template-columns: 1fr; }
    .footer { padding: 14px 20px; flex-direction: column; gap: 10px; }
  }
"""

_LOGO_SVG = """\
      <svg class="logo-icon" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
        <circle cx="40" cy="40" r="34" fill="none" stroke="white" stroke-width="1.4" opacity="0.85"/>
        <line x1="10" y1="30" x2="70" y2="30" stroke="white" stroke-width="0.7" opacity="0.3"/>
        <line x1="8"  y1="40" x2="72" y2="40" stroke="white" stroke-width="0.7" opacity="0.3"/>
        <line x1="10" y1="50" x2="70" y2="50" stroke="white" stroke-width="0.7" opacity="0.3"/>
        <line x1="30" y1="8"  x2="30" y2="72" stroke="white" stroke-width="0.7" opacity="0.3"/>
        <line x1="40" y1="6"  x2="40" y2="74" stroke="white" stroke-width="0.7" opacity="0.3"/>
        <line x1="50" y1="8"  x2="50" y2="72" stroke="white" stroke-width="0.7" opacity="0.3"/>
        <line x1="18" y1="62" x2="62" y2="18" stroke="#c9a84c" stroke-width="2.2" stroke-linecap="round"/>
        <circle cx="40" cy="40" r="3" fill="#c9a84c"/>
      </svg>"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_date(date_str):
    """Format YYYY-MM-DD → 'Feb 21, 2026'."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{d.strftime('%b')} {d.day}, {d.year}"
    except ValueError:
        return date_str


def find_us_dates():
    """Sorted (newest first) list of US newsletter dates in output/."""
    dates = []
    for f in OUTPUT_DIR.glob("newsletter_*.md"):
        m = re.match(r"newsletter_(\d{4}-\d{2}-\d{2})\.md$", f.name)
        if m:
            dates.append(m.group(1))
    return sorted(dates, reverse=True)


def find_intl_dates():
    """Sorted (newest first) list of Intl newsletter dates in output/."""
    dates = []
    for f in OUTPUT_DIR.glob("intl_newsletter_*.md"):
        m = re.match(r"intl_newsletter_(\d{4}-\d{2}-\d{2})\.md$", f.name)
        if m:
            dates.append(m.group(1))
    return sorted(dates, reverse=True)


def find_pdf_src(date_str, edition="us"):
    """Return Path to the PDF in output/ for this date/edition, or None."""
    if edition == "us":
        candidates = [
            OUTPUT_DIR / f"newsletter_us_{date_str}.pdf",
            OUTPUT_DIR / f"newsletter_{date_str}.pdf",
        ]
    else:
        candidates = [
            OUTPUT_DIR / f"intl_newsletter_{date_str}.pdf",
            OUTPUT_DIR / f"intl_newsletter_us_{date_str}.pdf",
        ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ── Hero card renderers ───────────────────────────────────────────────────────

_US_PREVIEW_INDICES = ["S&P 500", "Dow Jones", "Nasdaq"]
_INTL_PREVIEW_INDICES = ["Nikkei 225", "FTSE 100", "Euro Stoxx 50"]


def _render_us_hero(date_str, ctx):
    display = fmt_date(date_str)
    index_lookup = {idx["name"]: idx for idx in ctx["indices"]}
    rows = ""
    for name in _US_PREVIEW_INDICES:
        idx = index_lookup.get(name)
        if not idx:
            continue
        if idx.get("is_yield"):
            bps = idx.get("yield_change_bps", 0)
            val = f"{bps:+.0f} bps"
        else:
            pct = idx.get("weekly_pct", 0)
            val = f"{pct:+.2f}%"
        cls = "pct-pos" if (idx.get("yield_change_bps", idx.get("weekly_pct", 0)) >= 0) else "pct-neg"
        rows += f'<div class="hero-idx-row"><span>{name}</span><span class="{cls}">{val}</span></div>\n'
    return f"""
    <div class="hero-card">
      <div class="hero-card-edition">&#127482;&#127480; US Edition</div>
      <div class="hero-card-date">{display}</div>
      <div class="hero-indices">{rows}</div>
      <a class="hero-cta" href="us/{date_str}/">Read Issue &rarr;</a>
    </div>"""


def _render_intl_hero(date_str, ctx):
    display = fmt_date(date_str)
    index_lookup = {idx["name"]: idx for idx in ctx["indices"]}
    rows = ""
    for name in _INTL_PREVIEW_INDICES:
        idx = index_lookup.get(name)
        if not idx:
            # try first available
            continue
        pct = idx.get("weekly_pct", 0)
        cls = "pct-pos" if pct >= 0 else "pct-neg"
        rows += f'<div class="hero-idx-row"><span>{name}</span><span class="{cls}">{pct:+.2f}%</span></div>\n'
    # Fallback: show first 3 available indices if preferred ones missing
    if not rows:
        for idx in ctx["indices"][:3]:
            pct = idx.get("weekly_pct", 0)
            cls = "pct-pos" if pct >= 0 else "pct-neg"
            rows += f'<div class="hero-idx-row"><span>{idx["name"]}</span><span class="{cls}">{pct:+.2f}%</span></div>\n'
    return f"""
    <div class="hero-card">
      <div class="hero-card-edition">&#127758; International Edition</div>
      <div class="hero-card-date">{display}</div>
      <div class="hero-indices">{rows}</div>
      <a class="hero-cta" href="intl/{date_str}/">Read Issue &rarr;</a>
    </div>"""


# ── Landing page ──────────────────────────────────────────────────────────────

def render_landing(us_dates, intl_dates, us_ctxs, intl_ctxs, pdf_map):
    """Render site/index.html."""

    # Hero cards (latest of each edition)
    latest_us = us_dates[0] if us_dates else None
    latest_intl = intl_dates[0] if intl_dates else None

    us_hero = _render_us_hero(latest_us, us_ctxs[latest_us]) if latest_us else \
        '<div class="hero-card no-issue">No US issue yet</div>'
    intl_hero = _render_intl_hero(latest_intl, intl_ctxs[latest_intl]) if latest_intl else \
        '<div class="hero-card no-issue">No International issue yet</div>'

    # Archive: all unique dates sorted newest-first
    all_dates = sorted(set(us_dates) | set(intl_dates), reverse=True)
    archive_rows = ""
    for d in all_dates:
        display = fmt_date(d)
        # US column
        if d in us_dates:
            us_html_link = f'<a class="archive-link" href="us/{d}/">Read</a>'
            us_pdf_name = pdf_map.get(("us", d))
            us_pdf_link = f'<a class="archive-link pdf" href="downloads/{us_pdf_name}">PDF</a>' \
                if us_pdf_name else ""
        else:
            us_html_link = "&mdash;"
            us_pdf_link = ""
        # Intl column
        if d in intl_dates:
            intl_html_link = f'<a class="archive-link" href="intl/{d}/">Read</a>'
            intl_pdf_name = pdf_map.get(("intl", d))
            intl_pdf_link = f'<a class="archive-link pdf" href="downloads/{intl_pdf_name}">PDF</a>' \
                if intl_pdf_name else ""
        else:
            intl_html_link = "&mdash;"
            intl_pdf_link = ""

        archive_rows += f"""
          <tr>
            <td>{display}</td>
            <td>{us_html_link}{us_pdf_link}</td>
            <td>{intl_html_link}{intl_pdf_link}</td>
          </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Framework Foundry &mdash; Weekly Economic Intelligence</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet"/>
  <style>
{_CSS}
  </style>
</head>
<body>
<div class="page">

  <header class="header">
    <div class="header-inner">
{_LOGO_SVG}
      <div class="logo-text">
        <span class="logo-name-framework">FRAMEWORK</span>
        <span class="logo-name-foundry">FOUNDRY</span>
        <div class="logo-rule"></div>
        <span class="logo-tagline">Weekly Economic Intelligence &nbsp;&middot;&nbsp; US &amp; International Editions</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

  <div class="nav-strip">Current Issues &nbsp;&middot;&nbsp; Archive &nbsp;&middot;&nbsp; <a href="https://frameworkfoundry.carrd.co" style="color:inherit;text-decoration:underline;">frameworkfoundry.info</a></div>

  <div class="content">

    <div class="section-label">Current Issues</div>
    <div class="hero-grid">
      {us_hero}
      {intl_hero}
    </div>

    <div class="section-label">Archive</div>
    <table class="archive-table">
      <thead>
        <tr>
          <th>Week Ending</th>
          <th>US Edition</th>
          <th>International Edition</th>
        </tr>
      </thead>
      <tbody>
        {archive_rows}
      </tbody>
    </table>

  </div><!-- /content -->

  <footer class="footer">
    <div class="footer-logo">FRAMEWORK <span>FOUNDRY</span></div>
    <div class="footer-disclaimer">
      For informational purposes only. Not investment advice.<br/>
      Past performance is not indicative of future results.
    </div>
  </footer>

</div><!-- /page -->
</body>
</html>"""


# ── Main build ────────────────────────────────────────────────────────────────

def build(use_mock=True):
    # Create site directory structure
    SITE_DIR.mkdir(exist_ok=True)
    (SITE_DIR / "us").mkdir(exist_ok=True)
    (SITE_DIR / "intl").mkdir(exist_ok=True)
    assets_dir = SITE_DIR / "assets"
    assets_dir.mkdir(exist_ok=True)
    downloads_dir = SITE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    # Copy chart PNGs → site/assets/
    for chart in OUTPUT_DIR.glob("*.png"):
        shutil.copy2(chart, assets_dir / chart.name)
        print(f"  chart  -> assets/{chart.name}")

    # Copy PDFs → site/downloads/ and build map
    pdf_map = {}  # ("us"|"intl", date_str) → filename
    us_dates = find_us_dates()
    intl_dates = find_intl_dates()

    for date_str in us_dates:
        src = find_pdf_src(date_str, "us")
        if src:
            shutil.copy2(src, downloads_dir / src.name)
            pdf_map[("us", date_str)] = src.name
            print(f"  pdf    -> downloads/{src.name}")

    for date_str in intl_dates:
        src = find_pdf_src(date_str, "intl")
        if src:
            shutil.copy2(src, downloads_dir / src.name)
            pdf_map[("intl", date_str)] = src.name
            print(f"  pdf    -> downloads/{src.name}")

    # Build US issue pages
    us_ctxs = {}
    for date_str in us_dates:
        print(f"Building US   {date_str} …")
        raw_indices = fetch_index_data(date_str, use_mock=use_mock)
        econ = fetch_econ_calendar(date_str, use_mock=use_mock)
        index_data = process_index_data(raw_indices)
        ctx = build_template_context(index_data, econ, date_str)
        us_ctxs[date_str] = ctx

        issue_dir = SITE_DIR / "us" / date_str
        issue_dir.mkdir(parents=True, exist_ok=True)
        html = render_us_html(ctx)
        (issue_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  -> site/us/{date_str}/index.html")

    # Build Intl issue pages
    intl_ctxs = {}
    for date_str in intl_dates:
        print(f"Building Intl {date_str} …")
        raw_indices = fetch_intl_index_data(date_str, use_mock=use_mock)
        raw_fx = fetch_intl_fx_data(date_str, use_mock=use_mock)
        econ = fetch_intl_econ_calendar(date_str, use_mock=use_mock)
        index_data = process_intl_index_data(raw_indices)
        fx_data = process_fx_data(raw_fx)
        ctx = build_intl_template_context(index_data, fx_data, econ, date_str)
        intl_ctxs[date_str] = ctx

        issue_dir = SITE_DIR / "intl" / date_str
        issue_dir.mkdir(parents=True, exist_ok=True)
        html = render_intl_html(ctx)
        (issue_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  -> site/intl/{date_str}/index.html")

    # Build landing page
    landing_html = render_landing(us_dates, intl_dates, us_ctxs, intl_ctxs, pdf_map)
    (SITE_DIR / "index.html").write_text(landing_html, encoding="utf-8")
    print(f"  -> site/index.html")

    print(f"\nDone. Site built at {SITE_DIR}")
    print("Open site/index.html in a browser to preview.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build unified static site for Cloudflare Pages.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch live data via yfinance/APIs (default: mock fixtures).",
    )
    args = parser.parse_args()
    build(use_mock=not args.live)
