#!/usr/bin/env python3
"""Build a static HTML site from the international newsletter for Vercel deployment."""

import argparse
from datetime import date
from pathlib import Path

from data.fetch_intl_data import fetch_intl_index_data, fetch_intl_fx_data, fetch_intl_econ_calendar
from data.intl_process_data import process_intl_index_data, process_fx_data, build_intl_template_context
from data.chart import generate_price_chart

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public_intl"
CHART_TITLE = (
    "Framework Foundry Weekly - International Edition"
    " -- Performance (% Change from Monday Open)"
)


def build(date_str, use_mock=True):
    PUBLIC_DIR.mkdir(exist_ok=True)

    # Fetch and process data
    raw_indices = fetch_intl_index_data(date_str, use_mock=use_mock)
    raw_fx = fetch_intl_fx_data(date_str, use_mock=use_mock)
    econ = fetch_intl_econ_calendar(date_str, use_mock=use_mock)

    index_data = process_intl_index_data(raw_indices)
    fx_data = process_fx_data(raw_fx)
    context = build_intl_template_context(index_data, fx_data, econ, date_str)

    # Generate chart into public_intl/
    chart_path_raw = generate_price_chart(raw_indices, date_str, PUBLIC_DIR, title=CHART_TITLE)
    intl_chart_path = PUBLIC_DIR / f"intl_chart_{date_str}.png"
    if chart_path_raw.exists():
        chart_path_raw.replace(intl_chart_path)

    # Build HTML
    html = render_html(context, intl_chart_path.name)
    (PUBLIC_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"International site built in {PUBLIC_DIR}")


def render_html(ctx, chart_filename):
    """Render the international newsletter as a standalone HTML page."""

    # Index rows (with Region column)
    index_rows = ""
    for idx in ctx["indices"]:
        color = "#22891e" if idx["weekly_pct"] >= 0 else "#b41e1e"
        index_rows += f"""
            <tr>
                <td>{idx['name']}</td>
                <td>{idx.get('region', '')}</td>
                <td class="num">{idx['close']:,.2f}</td>
                <td class="num" style="color:{color}">{idx['weekly_pct']:+.2f}%</td>
                <td class="num">{idx['week_low']:,.2f} - {idx['week_high']:,.2f}</td>
            </tr>"""

    # FX rows
    fx_rows = ""
    for fx in ctx.get("fx_rates", []):
        color = "#22891e" if fx["weekly_pct"] >= 0 else "#b41e1e"
        fx_rows += f"""
            <tr>
                <td>{fx['name']}</td>
                <td class="num">{fx['rate']:.4f}</td>
                <td class="num" style="color:{color}">{fx['weekly_pct']:+.2f}%</td>
            </tr>"""

    fx_rates = ctx.get("fx_rates", [])
    fx_best = max(fx_rates, key=lambda x: x["weekly_pct"]) if fx_rates else None
    fx_worst = min(fx_rates, key=lambda x: x["weekly_pct"]) if fx_rates else None

    fx_callout = ""
    if fx_best and fx_worst:
        fx_callout = f"""
        <div class="callout">
            <span class="best">Best: {fx_best['name']} ({fx_best['weekly_pct']:+.2f}%)</span>
            <span class="worst">Worst: {fx_worst['name']} ({fx_worst['weekly_pct']:+.2f}%)</span>
        </div>"""

    # Econ events rows
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

    # Impact notes
    impact_notes = ""
    for ev in ctx["past_events"]:
        impact = ev.get("impact", "")
        if impact:
            impact_notes += f"""
            <div class="impact-note">
                <strong>{ev['event']}:</strong>
                <span>{impact}</span>
            </div>"""

    # Upcoming rows
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

    # Positioning tips rows
    tips_rows = ""
    for tip in ctx["tips"]:
        if ": " in tip:
            signal, action = tip.split(": ", 1)
        else:
            signal, action = tip, ""
        tips_rows += f"""
            <tr>
                <td class="signal">{signal}</td>
                <td>{action}</td>
            </tr>"""

    # Narrative paragraphs
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
    <title>Framework Foundry Weekly - International Edition - {ctx['date']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #1e1e1e;
            line-height: 1.6;
        }}
        .header {{
            background: #142850;
            color: white;
            padding: 36px 20px 32px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.1rem;
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: -0.01em;
        }}
        .header .byline {{
            font-size: 1.1rem;
            font-style: italic;
            opacity: 0.9;
            margin-bottom: 18px;
        }}
        .header .subtitle {{
            font-size: 0.9rem;
            font-weight: 400;
            opacity: 0.8;
        }}
        .container {{
            max-width: 960px;
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
            color: #0f3460;
            margin-bottom: 4px;
            padding-bottom: 8px;
            border-bottom: 3px solid #1a5276;
            display: inline-block;
        }}
        .section h2 + * {{ margin-top: 16px; }}
        .section h3 {{
            font-size: 1.05rem;
            color: #0f3460;
            margin: 20px 0 8px;
        }}
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
            background: #0f3460;
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
            border-left: 3px solid #1a5276;
            padding: 10px 14px;
            margin: 8px 0;
            font-size: 0.85rem;
            border-radius: 0 6px 6px 0;
        }}
        .impact-note strong {{
            color: #0f3460;
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
        .signal {{ font-weight: 600; color: #0f3460; }}
        .disclaimer {{
            text-align: center;
            font-size: 0.78rem;
            color: #888;
            padding: 20px;
            margin-top: 10px;
        }}
        @media (max-width: 600px) {{
            .header h1 {{ font-size: 1.4rem; }}
            .section {{ padding: 18px 16px; }}
            table {{ font-size: 0.8rem; }}
            thead th, tbody td {{ padding: 7px 6px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Framework Foundry Weekly - International Edition</h1>
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
                        <th>Region</th>
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

            <h3>FX Rates</h3>
            <table>
                <thead>
                    <tr>
                        <th>Currency Pair</th>
                        <th class="num">Rate</th>
                        <th class="num">Weekly %</th>
                    </tr>
                </thead>
                <tbody>
                    {fx_rows}
                </tbody>
            </table>
            {fx_callout}
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
        Published by Framework Foundry. Disclaimer: This newsletter is for informational purposes only
        and does not constitute investment advice. Past performance is not indicative of future results.
        Always do your own research before making investment decisions.
        <br><br>Generated by Framework Foundry Weekly &mdash; International Edition
    </div>
</body>
</html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a static HTML site from the international newsletter."
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Newsletter date (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch live data via yfinance (default: use mock fixtures).",
    )
    args = parser.parse_args()
    build(args.date, use_mock=not args.live)
