#!/usr/bin/env python3
"""Build a static HTML page for the The Morning Brief daily edition."""

import re as _re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Reuse the shared CSS from build_site.py and extend it
from build_site import _CSS as _BASE_CSS

_DAYBREAK_CSS = _BASE_CSS + """
  /* DAYBREAK-SPECIFIC STYLES */

  /* Session badge for partial (early) European markets */
  .session-partial {
    display: inline-block;
    background: #c9a84c22;
    color: #c9a84c;
    border: 1px solid #c9a84c55;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
    font-family: 'Raleway', sans-serif;
  }

  .session-closed {
    display: inline-block;
    background: rgba(107,114,128,0.12);
    color: var(--muted);
    border: 1px solid rgba(107,114,128,0.3);
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.5px;
    font-family: 'Raleway', sans-serif;
  }

  /* Time column in today's watch list */
  .time-col {
    font-family: 'Raleway', sans-serif;
    color: var(--muted);
    white-space: nowrap;
    font-size: 12px;
  }

  /* Futures table row tinting */
  .futures-row-pos { background: rgba(42,125,79,0.07) !important; }
  .futures-row-neg { background: rgba(185,28,28,0.07) !important; }

  /* Sub-section labels within a section */
  .sub-section-label {
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin: 16px 0 8px;
  }

  .sub-section-label:first-child { margin-top: 0; }

  /* News table */
  .news-table td.idx-col    { width: 2rem; color: #888; text-align: center; }
  .news-table td.source-col { width: 7rem; color: #555; font-size: 0.85rem; }
  .news-table a             { color: #1a5276; text-decoration: none; }
  .news-table a:hover       { text-decoration: underline; }
"""


def render_html(ctx: dict) -> str:
    """Render the The Morning Brief daily edition as a standalone HTML page."""

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _pct_str(pct, is_yield=False, bps=None):
        if is_yield:
            if bps is None:
                return "--"
            return f"{bps:+.0f} bps"
        if pct is None:
            return "--"
        return f"{pct:+.2f}%"

    def _pct_class(val):
        if val is None:
            return "pct"
        return "pct positive" if val >= 0 else "pct negative"

    # ── Display date ──────────────────────────────────────────────────────────
    date_str = ctx["date"]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = f"{d.strftime('%b')} {d.day}, {d.year}"
    except ValueError:
        display_date = date_str

    # ── Narrative ─────────────────────────────────────────────────────────────
    narrative_html = ""
    for para in ctx["narrative"].split("\n\n"):
        para = para.strip()
        if para:
            para = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", para)
            para = _re.sub(r"\*(.+?)\*",     r"<em>\1</em>",         para)
            para = _re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', para)
            narrative_html += f'<p class="brief-text">{para}</p>\n'

    # ── Plain-English Summary ─────────────────────────────────────────────────
    plain_html = ""
    raw_plain = ctx.get("plain_summary", "")
    for block in raw_plain.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("- "):
            items = [line[2:].strip() for line in block.splitlines() if line.startswith("- ")]
            def _fmt(item):
                item = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
                item = _re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', item)
                return item
            items_html = "".join(f'<li>{_fmt(item)}</li>' for item in items)
            plain_html += f'<ul class="plain-list">{items_html}</ul>\n'
        else:
            para = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", block)
            plain_html += f'<p class="plain-text">{para}</p>\n'

    # ── Market-Moving Headlines ───────────────────────────────────────────────
    news_html = ""
    if ctx.get("market_news"):
        news_rows = ""
        for i, item in enumerate(ctx["market_news"], 1):
            url       = item.get("url", "#")
            headline  = item.get("headline", "")
            source    = item.get("source", "")
            summary   = item.get("summary", "")
            title_attr = summary.replace('"', "&quot;") if summary else ""
            news_rows += (
                f'<tr><td class="idx-col">{i}</td>'
                f'<td><a href="{url}" target="_blank" title="{title_attr}">{headline}</a></td>'
                f'<td class="source-col">{source}</td></tr>\n'
            )
        news_html = (
            '<div class="section-block">\n'
            '  <div class="section-title">Market-Moving Headlines</div>\n'
            '  <table class="snapshot-table news-table">\n'
            '    <thead><tr><th>#</th><th>Headline</th><th>Source</th></tr></thead>\n'
            f'    <tbody>\n{news_rows}    </tbody>\n'
            '  </table>\n'
            '</div>\n'
        )

    # ── US Market Close Table ─────────────────────────────────────────────────
    us_rows = ""
    for idx in ctx["us_indices"]:
        if not idx.get("table", True):
            continue
        if idx.get("is_yield"):
            close_str = f"{idx['close']:.2f}%" if idx["close"] is not None else "--"
            perf_str  = _pct_str(None, is_yield=True, bps=idx.get("yield_change_bps"))
            pct_cls   = _pct_class(idx.get("yield_change_bps"))
        else:
            close_str = f"{idx['close']:,.2f}" if idx["close"] is not None else "--"
            perf_str  = _pct_str(idx["daily_pct"])
            pct_cls   = _pct_class(idx["daily_pct"])
        us_rows += f"""
            <tr>
              <td>{idx['name']}</td>
              <td>{close_str}</td>
              <td class="{pct_cls}">{perf_str}</td>
            </tr>"""

    # Best / Worst footer
    us_best  = ctx.get("us_best")
    us_worst = ctx.get("us_worst")
    best_str  = f"{us_best['name']} ({_pct_str(us_best['daily_pct'])})"  if us_best  else ""
    worst_str = f"{us_worst['name']} ({_pct_str(us_worst['daily_pct'])})" if us_worst else ""

    # ── Overnight Markets ─────────────────────────────────────────────────────
    apac_rows   = ""
    europe_rows = ""
    for idx in ctx["intl_indices"]:
        close_str = f"{idx['close']:,.2f}" if idx["close"] is not None else "--"
        perf_str  = _pct_str(idx["daily_pct"])
        pct_cls   = _pct_class(idx["daily_pct"])
        status    = idx.get("status", "closed")
        if status == "partial":
            badge = '<span class="session-partial">Early Session</span>'
        else:
            badge = '<span class="session-closed">Closed</span>'
        row = f"""
            <tr>
              <td>{idx['name']}</td>
              <td>{close_str}</td>
              <td class="{pct_cls}">{perf_str}</td>
              <td>{badge}</td>
            </tr>"""
        if idx["region"] == "Asia-Pacific":
            apac_rows += row
        else:
            europe_rows += row

    intl_rows_html = ""
    if apac_rows:
        intl_rows_html += """
        <div class="sub-section-label">Asia-Pacific (Closed)</div>
        <table class="snapshot-table" style="margin-bottom:16px;">
          <thead>
            <tr><th>Index</th><th>Close</th><th>Daily %</th><th>Session</th></tr>
          </thead>
          <tbody>""" + apac_rows + """
          </tbody>
        </table>"""
    if europe_rows:
        intl_rows_html += """
        <div class="sub-section-label">Europe</div>
        <table class="snapshot-table">
          <thead>
            <tr><th>Index</th><th>Close/Price</th><th>Daily %</th><th>Session</th></tr>
          </thead>
          <tbody>""" + europe_rows + """
          </tbody>
        </table>"""

    # ── FX & Safe Havens ──────────────────────────────────────────────────────
    fx_rows = ""
    for fx in ctx["fx_rates"]:
        rate_str = f"{fx['rate']:.4f}" if fx["rate"] is not None else "--"
        perf_str = _pct_str(fx["daily_pct"])
        pct_cls  = _pct_class(fx["daily_pct"])
        fx_rows += f"""
            <tr>
              <td>{fx['name']}</td>
              <td>{rate_str}</td>
              <td class="{pct_cls}">{perf_str}</td>
            </tr>"""

    # ── Pre-Market Futures ─────────────────────────────────────────────────────
    futures_rows = ""
    for fut in ctx["futures"]:
        price_str = f"{fut['price']:,.2f}" if fut["price"] is not None else "--"
        perf_str  = _pct_str(fut["daily_pct"])
        pct_cls   = _pct_class(fut["daily_pct"])
        pct_val   = fut["daily_pct"]
        row_cls   = "futures-row-pos" if (pct_val is not None and pct_val >= 0) \
                    else ("futures-row-neg" if pct_val is not None else "")
        futures_rows += f"""
            <tr class="{row_cls}">
              <td>{fut['name']}</td>
              <td>{price_str}</td>
              <td class="{pct_cls}">{perf_str}</td>
            </tr>"""

    # ── Yesterday's Events ────────────────────────────────────────────────────
    yesterday_rows = ""
    for ev in ctx.get("yesterday_events", []):
        surprise = ev.get("surprise", "neutral")
        if surprise == "above":
            tag = '<span class="tag above">Above</span>'
        elif surprise == "below":
            tag = '<span class="tag below">Below</span>'
        else:
            tag = '<span class="tag inline">Inline</span>'
        actual   = f"{ev.get('actual', '--')}{ev.get('unit', '')}"
        expected = f"{ev.get('expected', '--')}{ev.get('unit', '')}"
        yesterday_rows += f"""
            <tr>
              <td>{ev.get('event', '')}</td>
              <td>{actual}</td>
              <td>{expected}</td>
              <td>{ev.get('previous', '--')}</td>
              <td>{tag}</td>
            </tr>"""

    if not yesterday_rows:
        yesterday_rows = '<tr><td colspan="5" style="color:var(--muted);font-style:italic;">No major events recorded.</td></tr>'

    # ── Today's Watch List ────────────────────────────────────────────────────
    today_rows = ""
    for ev in ctx.get("today_events", []):
        imp = ev.get("importance", 1)
        if imp >= 3:
            imp_class, imp_label = "imp-high", "High"
        elif imp == 2:
            imp_class, imp_label = "imp-medium", "Medium"
        else:
            imp_class, imp_label = "imp-low", "Low"
        time_est = ev.get("time_est", "--") or "--"
        expected = f"{ev.get('expected', '--')}{ev.get('unit', '')}"
        today_rows += f"""
            <tr>
              <td class="time-col">{time_est}</td>
              <td>{ev.get('event', '')}</td>
              <td><span class="{imp_class}">{imp_label}</span></td>
              <td>{expected}</td>
            </tr>"""

    if not today_rows:
        today_rows = '<tr><td colspan="4" style="color:var(--muted);font-style:italic;">No high-importance events scheduled today.</td></tr>'

    # ── Positioning Tips ──────────────────────────────────────────────────────
    tips_rows = ""
    for tip in ctx["tips"]:
        # Split on " -- " or " — " (em dash) so either separator works
        sep = " -- " if " -- " in tip else (" \u2014 " if " \u2014 " in tip else None)
        if sep:
            signal, action = tip.split(sep, 1)
        else:
            signal, action = tip, ""
        def _md_links(text):
            return _re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)
        signal = _md_links(signal)
        action = _md_links(action)
        tips_rows += f"""
            <tr>
              <td class="signal-col">{signal}</td>
              <td class="action-col">{action[:1].upper() + action[1:] if action else ''}</td>
            </tr>"""

    # ── Full HTML ─────────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Framework Foundry \u2014 The Morning Brief \u00b7 {date_str}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet"/>
  <style>
{_DAYBREAK_CSS}
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
        <span class="logo-tagline">{ctx['tagline']}</span>
      </div>
      <div class="header-meta">
        <span class="issue-label">The Morning Brief</span>
        <span class="issue-date">{display_date}</span>
        <span class="issue-week">Daily Edition</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

  <!-- REGION BANNER -->
  <div class="region-banner">
    <span>{ctx['region_banner']}</span>
    <div class="region-dots">
      <span class="region-dot">\U0001f310</span>
    </div>
  </div>

  <div class="content">

    <!-- THE BRIEF -->
    <div class="section-block">
      <div class="section-title">The Brief</div>
      {narrative_html}
      {plain_html}
    </div>

    {news_html}

    <!-- POSITIONING NOTES -->
    <div class="section-block">
      <div class="section-title">Positioning Notes</div>
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

  <!-- RAW DATA LINK -->
  <div style="text-align:center;padding:12px 40px 0;font-family:'Raleway',sans-serif;font-size:11px;letter-spacing:1px;color:var(--muted);">
    Want the raw numbers?
    <a href="data/index.html" style="color:var(--accent);text-decoration:none;margin-left:4px;">View full market data &rarr;</a>
  </div>

  </div><!-- /content -->

  <!-- SUBSCRIBE -->
  <div class="subscribe-section">
    <h2>Stay in the loop</h2>
    <p>Free daily market intelligence, every morning.</p>
    <form class="subscribe-form" action="https://formspree.io/f/mwpvyoal" method="POST">
      <input type="email" name="email" placeholder="your@email.com" required />
      <button type="submit">Subscribe</button>
    </form>
  </div>

  <!-- SHARE BAR -->
  <div class="share-bar">
    <span class="share-label">Share this edition</span>
    <div class="share-buttons">
      <a class="share-btn twitter" href="#" target="_blank" rel="noopener"
         onclick="this.href='https://twitter.com/intent/tweet?text='+encodeURIComponent('The Morning Brief via Framework Foundry \u2014  '+window.location.href);return true;"
         title="Share on X / Twitter">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a class="share-btn linkedin" href="#" target="_blank" rel="noopener"
         onclick="this.href='https://www.linkedin.com/sharing/share-offsite/?url='+encodeURIComponent(window.location.href);return true;"
         title="Share on LinkedIn">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
      </a>
      <a class="share-btn facebook" href="#" target="_blank" rel="noopener"
         onclick="this.href='https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(window.location.href);return true;"
         title="Share on Facebook">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      </a>
    </div>
  </div>

  <!-- FOOTER -->
  <footer class="footer">
    <div class="footer-logo">FRAMEWORK <span>FOUNDRY</span> &nbsp;\u00b7&nbsp; <span style="color:rgba(255,255,255,0.35); font-size:10px; letter-spacing:1px;">DAILY EDITION</span></div>
    <div class="footer-disclaimer">
      Disclaimer: For informational purposes only. Not investment advice.<br/>
      Past performance is not indicative of future results.
    </div>
  </footer>

</div><!-- /page -->
</body>
</html>"""


def render_data_html(ctx: dict) -> str:
    """Render the raw market data page for a daybreak edition.

    Lives at site/daily/{date}/data/index.html.
    Contains all six data tables removed from the main brief.
    """
    def _pct_str(pct, is_yield=False, bps=None):
        if is_yield:
            return "--" if bps is None else f"{bps:+.0f} bps"
        return "--" if pct is None else f"{pct:+.2f}%"

    def _pct_class(val):
        if val is None:
            return "pct"
        return "pct positive" if val >= 0 else "pct negative"

    date_str = ctx["date"]
    try:
        from datetime import datetime
        d = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = f"{d.strftime('%b')} {d.day}, {d.year}"
    except ValueError:
        display_date = date_str

    # ── US Market Close ───────────────────────────────────────────────────────
    us_rows = ""
    for idx in ctx["us_indices"]:
        if not idx.get("table", True):
            continue
        if idx.get("is_yield"):
            close_str = f"{idx['close']:.2f}%" if idx["close"] is not None else "--"
            perf_str  = _pct_str(None, is_yield=True, bps=idx.get("yield_change_bps"))
            pct_cls   = _pct_class(idx.get("yield_change_bps"))
        else:
            close_str = f"{idx['close']:,.2f}" if idx["close"] is not None else "--"
            perf_str  = _pct_str(idx["daily_pct"])
            pct_cls   = _pct_class(idx["daily_pct"])
        us_rows += f"<tr><td>{idx['name']}</td><td>{close_str}</td><td class='{pct_cls}'>{perf_str}</td></tr>"

    us_best  = ctx.get("us_best")
    us_worst = ctx.get("us_worst")
    best_str  = f"{us_best['name']} ({_pct_str(us_best['daily_pct'])})"  if us_best  else ""
    worst_str = f"{us_worst['name']} ({_pct_str(us_worst['daily_pct'])})" if us_worst else ""

    # ── Overnight Markets ─────────────────────────────────────────────────────
    apac_rows = europe_rows = ""
    for idx in ctx["intl_indices"]:
        close_str = f"{idx['close']:,.2f}" if idx["close"] is not None else "--"
        perf_str  = _pct_str(idx["daily_pct"])
        pct_cls   = _pct_class(idx["daily_pct"])
        status    = idx.get("status", "closed")
        badge = '<span class="session-partial">Early Session</span>' if status == "partial" \
                else '<span class="session-closed">Closed</span>'
        row = f"<tr><td>{idx['name']}</td><td>{close_str}</td><td class='{pct_cls}'>{perf_str}</td><td>{badge}</td></tr>"
        if idx["region"] == "Asia-Pacific":
            apac_rows += row
        else:
            europe_rows += row

    intl_html = ""
    if apac_rows:
        intl_html += f"""<div class="sub-section-label">Asia-Pacific (Closed)</div>
        <table class="snapshot-table" style="margin-bottom:16px;">
          <thead><tr><th>Index</th><th>Close</th><th>Daily %</th><th>Session</th></tr></thead>
          <tbody>{apac_rows}</tbody></table>"""
    if europe_rows:
        intl_html += f"""<div class="sub-section-label">Europe</div>
        <table class="snapshot-table">
          <thead><tr><th>Index</th><th>Close/Price</th><th>Daily %</th><th>Session</th></tr></thead>
          <tbody>{europe_rows}</tbody></table>"""

    # ── FX & Safe Havens ──────────────────────────────────────────────────────
    fx_rows = ""
    for fx in ctx["fx_rates"]:
        rate_str = f"{fx['rate']:.4f}" if fx["rate"] is not None else "--"
        perf_str = _pct_str(fx["daily_pct"])
        pct_cls  = _pct_class(fx["daily_pct"])
        fx_rows += f"<tr><td>{fx['name']}</td><td>{rate_str}</td><td class='{pct_cls}'>{perf_str}</td></tr>"

    # ── Pre-Market Futures ─────────────────────────────────────────────────────
    futures_rows = ""
    for fut in ctx["futures"]:
        price_str = f"{fut['price']:,.2f}" if fut["price"] is not None else "--"
        perf_str  = _pct_str(fut["daily_pct"])
        pct_cls   = _pct_class(fut["daily_pct"])
        pct_val   = fut["daily_pct"]
        row_cls   = "futures-row-pos" if (pct_val is not None and pct_val >= 0) \
                    else ("futures-row-neg" if pct_val is not None else "")
        futures_rows += f"<tr class='{row_cls}'><td>{fut['name']}</td><td>{price_str}</td><td class='{pct_cls}'>{perf_str}</td></tr>"

    # ── Yesterday's Events ────────────────────────────────────────────────────
    yesterday_rows = ""
    for ev in ctx.get("yesterday_events", []):
        surprise = ev.get("surprise", "neutral")
        tag = {'above': '<span class="tag above">Above</span>',
               'below': '<span class="tag below">Below</span>'}.get(
               surprise, '<span class="tag inline">Inline</span>')
        actual   = f"{ev.get('actual', '--')}{ev.get('unit', '')}"
        expected = f"{ev.get('expected', '--')}{ev.get('unit', '')}"
        yesterday_rows += (f"<tr><td>{ev.get('event', '')}</td><td>{actual}</td>"
                           f"<td>{expected}</td><td>{ev.get('previous', '--')}</td>"
                           f"<td>{tag}</td></tr>")
    if not yesterday_rows:
        yesterday_rows = '<tr><td colspan="5" style="color:var(--muted);font-style:italic;">No major events recorded.</td></tr>'

    # ── Today's Watch List ────────────────────────────────────────────────────
    today_rows = ""
    for ev in ctx.get("today_events", []):
        imp = ev.get("importance", 1)
        if imp >= 3:
            imp_class, imp_label = "imp-high", "High"
        elif imp == 2:
            imp_class, imp_label = "imp-medium", "Medium"
        else:
            imp_class, imp_label = "imp-low", "Low"
        time_est = ev.get("time_est", "--") or "--"
        expected = f"{ev.get('expected', '--')}{ev.get('unit', '')}"
        today_rows += (f"<tr><td class='time-col'>{time_est}</td><td>{ev.get('event', '')}</td>"
                       f"<td><span class='{imp_class}'>{imp_label}</span></td>"
                       f"<td>{expected}</td></tr>")
    if not today_rows:
        today_rows = '<tr><td colspan="4" style="color:var(--muted);font-style:italic;">No high-importance events scheduled today.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Framework Foundry \u2014 Market Data \u00b7 {date_str}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet"/>
  <style>
{_DAYBREAK_CSS}
  </style>
</head>
<body>
<div class="page">

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
        <span class="logo-tagline">Raw Market Data \u00b7 {display_date}</span>
      </div>
      <div class="header-meta">
        <span class="issue-label">The Morning Brief</span>
        <span class="issue-date">{display_date}</span>
        <span class="issue-week">Data Edition</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

  <div class="region-banner">
    <span>US Close \u00b7 Asia-Pacific \u00b7 Europe \u00b7 FX \u00b7 Futures \u00b7 Economic Calendar</span>
    <div class="region-dots"><span class="region-dot">\U0001f4ca</span></div>
  </div>

  <div class="content">

    <div style="padding:12px 0 20px;font-family:'Raleway',sans-serif;font-size:11px;letter-spacing:1px;color:var(--muted);">
      <a href="../index.html" style="color:var(--accent);text-decoration:none;">&larr; Back to The Brief</a>
    </div>

    <div class="section-block">
      <div class="section-title">US Market Close</div>
      <table class="snapshot-table">
        <thead><tr><th>Index</th><th>Close</th><th>Daily %</th></tr></thead>
        <tbody>{us_rows}</tbody>
      </table>
      <div class="snapshot-footer">
        <span class="best">\u25b2 Best: {best_str}</span>
        <span class="worst">\u25bc Worst: {worst_str}</span>
      </div>
    </div>

    <div class="section-block">
      <div class="section-title">Overnight Markets</div>
      {intl_html if intl_html else '<p class="brief-text" style="color:var(--muted);">No overnight data available.</p>'}
    </div>

    <div class="section-block">
      <div class="section-title">Currencies &amp; Safe Havens</div>
      <table class="snapshot-table">
        <thead><tr><th>Pair</th><th>Rate</th><th>Daily %</th></tr></thead>
        <tbody>{fx_rows if fx_rows else '<tr><td colspan="3" style="color:var(--muted);font-style:italic;">No FX data.</td></tr>'}</tbody>
      </table>
    </div>

    <div class="section-block">
      <div class="section-title">Pre-Market Futures</div>
      <table class="snapshot-table">
        <thead><tr><th>Contract</th><th>Price</th><th>Daily %</th></tr></thead>
        <tbody>{futures_rows if futures_rows else '<tr><td colspan="3" style="color:var(--muted);font-style:italic;">No futures data.</td></tr>'}</tbody>
      </table>
    </div>

    <div class="section-block">
      <div class="section-title">What Moved Markets Yesterday</div>
      <table class="events-table">
        <thead><tr><th>Event</th><th>Actual</th><th>Expected</th><th>Previous</th><th>Surprise</th></tr></thead>
        <tbody>{yesterday_rows}</tbody>
      </table>
    </div>

    <div class="section-block">
      <div class="section-title">Today\u2019s Watch List</div>
      <table class="upcoming-table">
        <thead><tr><th>Time (EST)</th><th>Event</th><th>Importance</th><th>Expected</th></tr></thead>
        <tbody>{today_rows}</tbody>
      </table>
    </div>

  </div><!-- /content -->

  <footer class="footer">
    <div class="footer-logo">FRAMEWORK <span>FOUNDRY</span> &nbsp;\u00b7&nbsp; <span style="color:rgba(255,255,255,0.35);font-size:10px;letter-spacing:1px;">RAW DATA</span></div>
    <div class="footer-disclaimer">
      For informational purposes only. Not investment advice.
    </div>
  </footer>

</div><!-- /page -->
</body>
</html>"""
