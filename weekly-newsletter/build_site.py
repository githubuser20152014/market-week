#!/usr/bin/env python3
"""Build a static HTML site from the newsletter for Vercel deployment."""

import argparse
from datetime import date, datetime
from pathlib import Path

from data.fetch_data import fetch_index_data, fetch_econ_calendar
from data.process_data import process_index_data, build_template_context

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

CARD_GROUPS = {
    "Large Cap":    ["S&P 500", "Dow Jones", "Nasdaq"],
    "Broad Market": ["Russell 2000", "Gold"],
    "Fixed Income": ["10Y Treasury"],
}

CARD_ICONS = {
    "Large Cap":    "📈",
    "Broad Market": "📊",
    "Fixed Income": "🏦",
}

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
  }

  .page {
    max-width: 780px;
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

  .header-meta { text-align: right; flex-shrink: 0; }

  .header-meta .issue-label {
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    letter-spacing: 3px;
    color: rgba(255,255,255,0.35);
    text-transform: uppercase;
    display: block;
  }

  .header-meta .issue-date {
    font-family: 'Cormorant Garamond', serif;
    font-size: 22px;
    font-weight: 300;
    color: var(--white);
    display: block;
    margin-top: 3px;
    line-height: 1.1;
  }

  .header-meta .issue-week {
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    letter-spacing: 2px;
    color: var(--accent);
    display: block;
    margin-top: 4px;
  }

  .header-accent {
    height: 3px;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent-lt) 50%, transparent 100%);
  }

  /* REGION BANNER */
  .region-banner {
    background: var(--accent);
    padding: 7px 40px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .region-banner span {
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 3px;
    color: rgba(255,255,255,0.9);
    text-transform: uppercase;
  }

  .region-dots { display: flex; gap: 6px; margin-left: auto; }
  .region-dot { font-size: 14px; line-height: 1; }

  /* CONTENT */
  .content { padding: 36px 40px; }

  .section-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 19px;
    font-weight: 600;
    color: var(--navy);
    letter-spacing: 0.5px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent);
    margin-bottom: 18px;
    display: inline-block;
  }

  .section-block { margin-bottom: 36px; }

  .brief-text {
    font-size: 14.5px;
    line-height: 1.8;
    color: #2c2c3e;
    font-weight: 300;
  }

  .brief-text + .brief-text { margin-top: 12px; }

  /* INDEX CARDS */
  .index-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 14px;
    margin-bottom: 20px;
  }

  .index-card {
    border-top: 3px solid var(--accent);
    padding: 14px;
    background: var(--off-white);
  }

  .index-card h4 {
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 8px;
  }

  .index-card .idx-row {
    font-family: 'Cormorant Garamond', serif;
    font-size: 13px;
    font-weight: 400;
    color: var(--navy);
    margin-bottom: 2px;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }

  .pct-pos { color: var(--green); font-size: 11px; font-family: 'Raleway', sans-serif; font-weight: 600; }
  .pct-neg { color: var(--red);   font-size: 11px; font-family: 'Raleway', sans-serif; font-weight: 600; }

  /* MARKET SNAPSHOT TABLE */
  .snapshot-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Raleway', sans-serif;
    font-size: 13px;
  }

  .snapshot-table thead tr { background: var(--navy); color: var(--white); }
  .snapshot-table thead th {
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
    letter-spacing: 1px;
    font-size: 10px;
    text-transform: uppercase;
  }

  .snapshot-table tbody tr { border-bottom: 1px solid var(--border); }
  .snapshot-table tbody tr:nth-child(even) { background: var(--off-white); }
  .snapshot-table tbody td { padding: 10px 14px; }

  .pct { font-weight: 600; }
  .pct.positive { color: var(--green); }
  .pct.negative { color: var(--red); }

  .snapshot-footer {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    font-family: 'Raleway', sans-serif;
    font-size: 11px;
    font-weight: 600;
  }

  .snapshot-footer .best  { color: var(--green); }
  .snapshot-footer .worst { color: var(--red); }

  /* ECONOMIC EVENTS */
  .events-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Raleway', sans-serif;
    font-size: 12.5px;
  }

  .events-table thead tr { background: var(--navy); color: var(--white); }
  .events-table thead th {
    padding: 9px 12px;
    text-align: left;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .events-table tbody td {
    padding: 9px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }

  .events-table tbody tr:nth-child(even) { background: var(--off-white); }

  .tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .tag.above  { background: #d4edda; color: #155724; }
  .tag.below  { background: #f8d7da; color: #721c24; }
  .tag.inline { background: #e8e8e8; color: #555; }

  /* ANALYSIS CARDS */
  .analysis-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-top: 18px;
  }

  .analysis-card {
    border-left: 3px solid var(--accent);
    padding: 12px 14px;
    background: var(--off-white);
  }

  .analysis-card h4 {
    font-family: 'Raleway', sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--navy);
    margin-bottom: 6px;
  }

  .analysis-card p {
    font-size: 12.5px;
    line-height: 1.65;
    color: #3a3a4a;
    font-weight: 300;
  }

  /* UPCOMING TABLE */
  .upcoming-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Raleway', sans-serif;
    font-size: 12.5px;
  }

  .upcoming-table thead tr { background: var(--navy); color: var(--white); }
  .upcoming-table thead th {
    padding: 9px 12px;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    text-align: left;
  }

  .upcoming-table tbody td {
    padding: 9px 12px;
    border-bottom: 1px solid var(--border);
  }

  .upcoming-table tbody tr:nth-child(even) { background: var(--off-white); }

  .imp-high   { color: var(--red);   font-weight: 700; font-size: 11px; }
  .imp-medium { color: #d97706;      font-weight: 600; font-size: 11px; }
  .imp-low    { color: var(--muted); font-weight: 400; font-size: 11px; }

  /* POSITIONING TIPS */
  .tips-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Raleway', sans-serif;
    font-size: 12.5px;
  }

  .tips-table thead tr { background: var(--navy); color: var(--white); }
  .tips-table thead th {
    padding: 9px 14px;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    text-align: left;
  }

  .tips-table tbody td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    line-height: 1.55;
    vertical-align: top;
  }

  .tips-table tbody tr:nth-child(even) { background: var(--off-white); }
  .tips-table .signal-col { color: var(--navy); font-weight: 500; width: 45%; }
  .tips-table .action-col { color: #2c2c3e; font-weight: 300; }

  /* FOOTER */
  .footer {
    background: var(--navy);
    padding: 16px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
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
    .index-grid { grid-template-columns: 1fr; }
    .analysis-grid { grid-template-columns: 1fr; }
    .footer { padding: 14px 20px; flex-direction: column; gap: 10px; }
  }
"""


def build(date_str, use_mock=True):
    PUBLIC_DIR.mkdir(exist_ok=True)

    # Fetch and process data
    raw_indices = fetch_index_data(date_str, use_mock=use_mock)
    econ = fetch_econ_calendar(date_str, use_mock=use_mock)
    index_data = process_index_data(raw_indices)
    context = build_template_context(index_data, econ, date_str)

    # Build HTML
    html = render_html(context)
    (PUBLIC_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"Site built in {PUBLIC_DIR}")


def render_html(ctx):
    """Render the newsletter as a standalone HTML page (v2 design)."""

    # ── Helpers ───────────────────────────────────────────────────────────────
    index_lookup = {idx["name"]: idx for idx in ctx["indices"]}

    def fmt_perf(idx):
        if not idx:
            return ""
        if idx.get("is_yield"):
            bps = idx.get("yield_change_bps", 0)
            return f"{bps:+.0f} bps"
        return f"{idx.get('weekly_pct', 0):+.2f}%"

    # ── Display date ──────────────────────────────────────────────────────────
    date_str = ctx["date"]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = f"{d.strftime('%b')} {d.day}, {d.year}"
    except ValueError:
        display_date = date_str

    # ── Index cards ───────────────────────────────────────────────────────────
    cards_html = ""
    for group_name, members in CARD_GROUPS.items():
        icon = CARD_ICONS.get(group_name, "📊")
        rows = ""
        for member in members:
            idx = index_lookup.get(member)
            if not idx:
                continue
            if idx.get("is_yield"):
                bps = idx["yield_change_bps"]
                val_str = f"{bps:+.0f} bps"
                cls = "pct-pos" if bps >= 0 else "pct-neg"
            else:
                pct = idx["weekly_pct"]
                val_str = f"{pct:+.2f}%"
                cls = "pct-pos" if pct >= 0 else "pct-neg"
            rows += f'<div class="idx-row"><span>{member}</span><span class="{cls}">{val_str}</span></div>\n'
        cards_html += f"""
        <div class="index-card">
          <h4>{icon} {group_name}</h4>
          {rows}
        </div>"""

    # ── Market snapshot rows ──────────────────────────────────────────────────
    index_rows = ""
    for idx in ctx["indices"]:
        if idx.get("is_yield"):
            bps = idx["yield_change_bps"]
            weekly_str = f"{bps:+.0f} bps"
            pct_class = "pct positive" if bps >= 0 else "pct negative"
        else:
            pct = idx["weekly_pct"]
            weekly_str = f"{pct:+.2f}%"
            pct_class = "pct positive" if pct >= 0 else "pct negative"
        index_rows += f"""
            <tr>
              <td>{idx['name']}</td>
              <td>{idx['close']:,.2f}</td>
              <td class="{pct_class}">{weekly_str}</td>
              <td>{idx['week_low']:,.2f} \u2013 {idx['week_high']:,.2f}</td>
            </tr>"""

    # ── Economic events rows ──────────────────────────────────────────────────
    econ_rows = ""
    for ev in ctx["past_events"]:
        surprise = ev.get("surprise", "")
        if surprise == "above":
            tag = '<span class="tag above">Above</span>'
        elif surprise == "below":
            tag = '<span class="tag below">Below</span>'
        else:
            tag = '<span class="tag inline">Inline</span>'
        econ_rows += f"""
            <tr>
              <td>{ev['date']}</td>
              <td>{ev['event']}</td>
              <td>{ev['actual']}{ev.get('unit', '')}</td>
              <td>{ev['expected']}{ev.get('unit', '')}</td>
              <td>{ev['previous']}{ev.get('unit', '')}</td>
              <td>{tag}</td>
            </tr>"""

    # ── Analysis cards ────────────────────────────────────────────────────────
    analysis_cards = ""
    for ev in ctx["past_events"]:
        impact = ev.get("impact", "")
        if not impact:
            continue
        event_name = ev["event"]
        event_lower = event_name.lower()
        if "core cpi" in event_lower:
            emoji = "\u27a1\ufe0f"
        elif "cpi" in event_lower:
            emoji = "\U0001f525"
        elif "jobless" in event_lower:
            emoji = "\U0001f4bc"
        elif "retail" in event_lower:
            emoji = "\U0001f6d2"
        else:
            emoji = "\U0001f4ca"
        analysis_cards += f"""
        <div class="analysis-card">
          <h4>{emoji} {event_name}</h4>
          <p>{impact}</p>
        </div>"""

    # ── Upcoming rows ─────────────────────────────────────────────────────────
    upcoming_rows = ""
    for ev in ctx["upcoming_events"]:
        imp = ev.get("importance", 1)
        if imp >= 3:
            imp_class, imp_label = "imp-high", "High"
        elif imp == 2:
            imp_class, imp_label = "imp-medium", "Medium"
        else:
            imp_class, imp_label = "imp-low", "Low"
        upcoming_rows += f"""
            <tr>
              <td>{ev['date']}</td>
              <td>{ev['event']}</td>
              <td><span class="{imp_class}">{imp_label}</span></td>
            </tr>"""

    # ── Tips rows ─────────────────────────────────────────────────────────────
    tips_rows = ""
    for tip in ctx["tips"]:
        if " -- " in tip:
            signal, action = tip.split(" -- ", 1)
        else:
            signal, action = tip, ""
        tips_rows += f"""
            <tr>
              <td class="signal-col">{signal}</td>
              <td class="action-col">{action[:1].upper() + action[1:]}</td>
            </tr>"""

    # ── Narrative ─────────────────────────────────────────────────────────────
    narrative_html = ""
    for para in ctx["narrative"].split("\n\n"):
        para = para.strip()
        if para:
            narrative_html += f'<p class="brief-text">{para}</p>\n'

    # ── Best / Worst ──────────────────────────────────────────────────────────
    best = ctx.get("best") or {}
    worst = ctx.get("worst") or {}
    best_str = f"{best.get('name', '')} ({fmt_perf(best)})" if best else ""
    worst_str = f"{worst.get('name', '')} ({fmt_perf(worst)})" if worst else ""

    # ── Full HTML ─────────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Framework Foundry \u2014 US Edition \u00b7 {date_str}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet"/>
  <style>
{_CSS}
  </style>
</head>
<body>
<div class="page">

  <!-- HEADER -->
  <header class="header">
    <div class="header-inner">
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
      </svg>
      <div class="logo-text">
        <span class="logo-name-framework">FRAMEWORK</span>
        <span class="logo-name-foundry">FOUNDRY</span>
        <div class="logo-rule"></div>
        <span class="logo-tagline">US Edition &nbsp;\u00b7&nbsp; Research for the serious investor</span>
      </div>
      <div class="header-meta">
        <span class="issue-label">Week Ending</span>
        <span class="issue-date">{display_date}</span>
        <span class="issue-week">US Edition</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

  <!-- REGION BANNER -->
  <div class="region-banner">
    <span>Coverage: Equities \u00b7 Fixed Income \u00b7 Commodities \u00b7 Macro \u00b7 Positioning</span>
    <div class="region-dots">
      <span class="region-dot">\U0001f1fa\U0001f1f8</span>
    </div>
  </div>

  <div class="content">

    <!-- THE WEEK IN BRIEF -->
    <div class="section-block">
      <div class="section-title">The Week in Brief</div>
      {narrative_html}
    </div>

    <!-- INDEX SNAPSHOT CARDS -->
    <div class="section-block">
      <div class="section-title">Index Snapshot</div>
      <div class="index-grid">{cards_html}
      </div>
    </div>

    <!-- MARKET SNAPSHOT TABLE -->
    <div class="section-block">
      <div class="section-title">Market Snapshot</div>
      <table class="snapshot-table">
        <thead>
          <tr>
            <th>Index</th>
            <th>Close</th>
            <th>Weekly %</th>
            <th>Week Range</th>
          </tr>
        </thead>
        <tbody>
          {index_rows}
        </tbody>
      </table>
      <div class="snapshot-footer">
        <span class="best">\u25b2 Best: {best_str}</span>
        <span class="worst">\u25bc Worst: {worst_str}</span>
      </div>
    </div>

    <!-- ECONOMIC EVENTS -->
    <div class="section-block">
      <div class="section-title">Last Week\u2019s Economic Events</div>
      <table class="events-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Event</th>
            <th>Actual</th>
            <th>Expected</th>
            <th>Previous</th>
            <th>Surprise</th>
          </tr>
        </thead>
        <tbody>
          {econ_rows}
        </tbody>
      </table>
      <div class="analysis-grid">
        {analysis_cards}
      </div>
    </div>

    <!-- UPCOMING WEEK -->
    <div class="section-block">
      <div class="section-title">Upcoming Week</div>
      <table class="upcoming-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Event</th>
            <th>Importance</th>
          </tr>
        </thead>
        <tbody>
          {upcoming_rows}
        </tbody>
      </table>
    </div>

    <!-- POSITIONING TIPS -->
    <div class="section-block">
      <div class="section-title">Positioning Tips</div>
      <table class="tips-table">
        <thead>
          <tr>
            <th>Signal</th>
            <th>Suggested Action</th>
          </tr>
        </thead>
        <tbody>
          {tips_rows}
        </tbody>
      </table>
    </div>

  </div><!-- /content -->

  <!-- FOOTER -->
  <footer class="footer">
    <div class="footer-logo">FRAMEWORK <span>FOUNDRY</span> &nbsp;\u00b7&nbsp; <span style="color:rgba(255,255,255,0.35); font-size:10px; letter-spacing:1px;">US EDITION</span></div>
    <div class="footer-disclaimer">
      Disclaimer: For informational purposes only. Not investment advice.<br/>
      Past performance is not indicative of future results.
    </div>
  </footer>

</div><!-- /page -->
</body>
</html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a static HTML site from the newsletter."
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Newsletter date (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch live index data via yfinance (default: use mock fixtures).",
    )
    args = parser.parse_args()
    build(args.date, use_mock=not args.live)
