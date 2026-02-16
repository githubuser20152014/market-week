#!/usr/bin/env python3
"""Build a static HTML site from the newsletter for Vercel deployment."""

import argparse
from datetime import date
from pathlib import Path

from data.fetch_data import fetch_index_data, fetch_econ_calendar
from data.process_data import process_index_data, build_template_context
from data.chart import generate_price_chart

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"


def build(date_str, use_mock=True):
    PUBLIC_DIR.mkdir(exist_ok=True)

    # Fetch and process data
    raw_indices = fetch_index_data(date_str, use_mock=use_mock)
    econ = fetch_econ_calendar(date_str, use_mock=use_mock)
    index_data = process_index_data(raw_indices)
    context = build_template_context(index_data, econ, date_str)

    # Generate chart into public/
    chart_path = generate_price_chart(raw_indices, date_str, PUBLIC_DIR)

    # Build HTML
    html = render_html(context, chart_path.name)
    (PUBLIC_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"Site built in {PUBLIC_DIR}")


def render_html(ctx, chart_filename):
    """Render the newsletter as a standalone HTML page."""

    # Build index rows
    index_rows = ""
    for idx in ctx["indices"]:
        color = "#22891e" if idx["weekly_pct"] >= 0 else "#b41e1e"
        index_rows += f"""
            <tr>
                <td>{idx['name']}</td>
                <td class="num">{idx['close']:,.2f}</td>
                <td class="num" style="color:{color}">{idx['weekly_pct']:+.2f}%</td>
                <td class="num">{idx['week_low']:,.2f} - {idx['week_high']:,.2f}</td>
            </tr>"""

    # Build econ events rows
    econ_rows = ""
    for ev in ctx["past_events"]:
        econ_rows += f"""
            <tr>
                <td>{ev['date']}</td>
                <td>{ev['event']}</td>
                <td class="num">{ev['actual']}{ev.get('unit','')}</td>
                <td class="num">{ev['expected']}{ev.get('unit','')}</td>
                <td class="num">{ev['previous']}{ev.get('unit','')}</td>
                <td>{ev.get('surprise','')}</td>
            </tr>"""

    # Build impact notes
    impact_notes = ""
    for ev in ctx["past_events"]:
        impact = ev.get("impact", "")
        if impact:
            impact_notes += f"""
            <div class="impact-note">
                <strong>{ev['event']}:</strong>
                <span>{impact}</span>
            </div>"""

    # Build upcoming rows
    upcoming_rows = ""
    for ev in ctx["upcoming_events"]:
        imp = ev.get("importance", 1)
        label = "High" if imp >= 3 else ("Medium" if imp == 2 else "Low")
        badge_class = "badge-high" if imp >= 3 else ("badge-med" if imp == 2 else "badge-low")
        upcoming_rows += f"""
            <tr>
                <td>{ev['date']}</td>
                <td>{ev['event']}</td>
                <td class="center"><span class="badge {badge_class}">{label}</span></td>
            </tr>"""

    # Build tips rows
    tips_rows = ""
    for tip in ctx["tips"]:
        if " -- " in tip:
            signal, action = tip.split(" -- ", 1)
        else:
            signal, action = tip, ""
        tips_rows += f"""
            <tr>
                <td class="signal">{signal}</td>
                <td>{action}</td>
            </tr>"""

    # Format narrative paragraphs
    narrative_html = ""
    for para in ctx["narrative"].split("\n\n"):
        narrative_html += f"<p>{para.strip()}</p>\n"

    best = ctx.get("best", {})
    worst = ctx.get("worst", {})

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Framework Foundry Weekly - {ctx['date']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #1e1e1e;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #142850, #1a3a6b);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .header .byline {{
            font-size: 1.15rem;
            opacity: 0.9;
            margin-top: 4px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 0.95rem;
            opacity: 0.75;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 30px 20px;
        }}
        .section {{
            background: white;
            border-radius: 10px;
            padding: 28px 30px;
            margin-bottom: 24px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }}
        .section h2 {{
            font-size: 1.3rem;
            color: #142850;
            margin-bottom: 4px;
            padding-bottom: 8px;
            border-bottom: 3px solid #3264b4;
            display: inline-block;
        }}
        .section h2 + * {{ margin-top: 16px; }}
        .narrative p {{
            margin-bottom: 14px;
            font-size: 0.95rem;
            color: #333;
        }}
        .chart-img {{
            width: 100%;
            border-radius: 6px;
            margin: 16px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            font-size: 0.9rem;
        }}
        thead th {{
            background: #142850;
            color: white;
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
        }}
        thead th.num, td.num {{ text-align: right; }}
        thead th.center, td.center {{ text-align: center; }}
        tbody tr:nth-child(even) {{ background: #f5f7fa; }}
        tbody td {{
            padding: 9px 12px;
            border-bottom: 1px solid #eee;
        }}
        .callout {{
            display: flex;
            justify-content: space-between;
            margin-top: 12px;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        .callout .best {{ color: #22891e; }}
        .callout .worst {{ color: #b41e1e; }}
        .impact-note {{
            background: #f0f4fa;
            border-left: 3px solid #3264b4;
            padding: 10px 14px;
            margin: 8px 0;
            font-size: 0.85rem;
            border-radius: 0 6px 6px 0;
        }}
        .impact-note strong {{
            color: #142850;
            display: block;
            margin-bottom: 2px;
        }}
        .impact-note span {{ color: #555; }}
        .badge {{
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.78rem;
            font-weight: 600;
        }}
        .badge-high {{ background: #fee2e2; color: #b41e1e; }}
        .badge-med {{ background: #fef3c7; color: #92400e; }}
        .badge-low {{ background: #e0e7ff; color: #3730a3; }}
        .signal {{ font-weight: 600; color: #142850; }}
        .disclaimer {{
            text-align: center;
            font-size: 0.78rem;
            color: #888;
            padding: 20px;
            margin-top: 10px;
        }}
        @media (max-width: 600px) {{
            .header h1 {{ font-size: 1.5rem; }}
            .section {{ padding: 18px 16px; }}
            table {{ font-size: 0.8rem; }}
            thead th, tbody td {{ padding: 7px 6px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Framework Foundry Weekly</h1>
        <div class="byline">Research for the serious investor</div>
        <div class="subtitle">Week ending {ctx['date']}</div>
    </div>

    <div class="container">
        <div class="section">
            <h2>The Week in Brief</h2>
            <div class="narrative">
                {narrative_html}
            </div>
        </div>

        <div class="section">
            <h2>Market Snapshot</h2>
            <img src="{chart_filename}" alt="Weekly Performance Chart" class="chart-img">
            <table>
                <thead>
                    <tr>
                        <th>Index</th>
                        <th class="num">Close</th>
                        <th class="num">Weekly %</th>
                        <th class="num">Week Range</th>
                    </tr>
                </thead>
                <tbody>
                    {index_rows}
                </tbody>
            </table>
            <div class="callout">
                <span class="best">Best: {best.get('name','')} ({best.get('weekly_pct',0):+.2f}%)</span>
                <span class="worst">Worst: {worst.get('name','')} ({worst.get('weekly_pct',0):+.2f}%)</span>
            </div>
        </div>

        <div class="section">
            <h2>Last Week's Economic Events</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Event</th>
                        <th class="num">Actual</th>
                        <th class="num">Expected</th>
                        <th class="num">Previous</th>
                        <th>Surprise</th>
                    </tr>
                </thead>
                <tbody>
                    {econ_rows}
                </tbody>
            </table>
            <div style="margin-top: 16px;">
                {impact_notes}
            </div>
        </div>

        <div class="section">
            <h2>Upcoming Week</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Event</th>
                        <th class="center">Importance</th>
                    </tr>
                </thead>
                <tbody>
                    {upcoming_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Positioning Tips</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width:40%">Signal</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {tips_rows}
                </tbody>
            </table>
        </div>
    </div>

    <div class="disclaimer">
        Disclaimer: This newsletter is for informational purposes only and does not constitute investment advice.
        Past performance is not indicative of future results. Always do your own research before making investment decisions.
        <br><br>Generated by Framework Foundry Weekly
    </div>
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
