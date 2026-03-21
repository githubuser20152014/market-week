#!/usr/bin/env python3
"""Render the Global Investor Edition as a standalone vertical HTML page."""

# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """\
  :root {
    --navy:      #0f1f3d;
    --accent:    #4a7fb5;
    --accent-lt: #7aabda;
    --gold:      #c9a84c;
    --white:     #ffffff;
    --off-white: #f5f4f0;
    --text:      #1a1a2e;
    --border:    #ddd8cc;
    --muted:     #6b7280;
    --green:     #2a7d4f;
    --red:       #b91c1c;
    --amber:     #d97706;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #dde3ea;
    font-family: 'Source Serif 4', Georgia, serif;
    color: var(--text);
    padding: 32px 16px;
  }

  .page {
    max-width: 820px;
    margin: 0 auto;
    background: var(--white);
    box-shadow: 0 8px 48px rgba(0,0,0,0.18);
  }

  /* HEADER */
  .header { background: var(--navy); position: relative; overflow: hidden; }
  .header::before {
    content: ''; position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
    background-size: 28px 28px;
  }
  .header-inner {
    position: relative; display: flex; align-items: center;
    justify-content: space-between; padding: 28px 40px 24px; gap: 24px;
  }
  .logo-icon { flex-shrink: 0; width: 64px; height: 64px; }
  .logo-text { flex: 1; }
  .logo-name-framework {
    font-family: 'Cormorant Garamond', serif; font-size: 30px; font-weight: 600;
    letter-spacing: 4px; color: var(--white); display: block; line-height: 1;
  }
  .logo-name-foundry {
    font-family: 'Raleway', sans-serif; font-size: 14px; font-weight: 300;
    letter-spacing: 12px; color: var(--accent); display: block; margin-top: 5px; line-height: 1;
  }
  .logo-rule { height: 1px; background: rgba(255,255,255,0.15); margin: 8px 0 6px; }
  .logo-tagline {
    font-family: 'Raleway', sans-serif; font-size: 8.5px; font-weight: 300;
    letter-spacing: 3.5px; color: rgba(255,255,255,0.4); text-transform: uppercase;
  }
  .header-meta { text-align: right; flex-shrink: 0; }
  .header-meta .issue-label {
    font-family: 'Raleway', sans-serif; font-size: 9px; letter-spacing: 3px;
    color: rgba(255,255,255,0.35); text-transform: uppercase; display: block;
  }
  .header-meta .issue-date {
    font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 300;
    color: var(--white); display: block; margin-top: 3px; line-height: 1.1;
  }
  .header-meta .issue-edition {
    font-family: 'Raleway', sans-serif; font-size: 9px; letter-spacing: 2px;
    color: var(--gold); display: block; margin-top: 4px;
  }
  .header-accent {
    height: 3px;
    background: linear-gradient(90deg, var(--gold) 0%, var(--accent-lt) 60%, transparent 100%);
  }

  /* REGION BANNER */
  .region-banner {
    background: var(--accent); padding: 7px 40px;
    display: flex; align-items: center; gap: 10px;
  }
  .region-banner span {
    font-family: 'Raleway', sans-serif; font-size: 9px; font-weight: 500;
    letter-spacing: 3px; color: rgba(255,255,255,0.9); text-transform: uppercase;
  }
  .region-dots { display: flex; gap: 6px; margin-left: auto; }
  .region-dot { font-size: 14px; line-height: 1; }

  /* CONTENT */
  .content { padding: 36px 40px; }
  .section-block { margin-bottom: 40px; }
  .section-title {
    font-family: 'Cormorant Garamond', serif; font-size: 19px; font-weight: 600;
    color: var(--navy); letter-spacing: 0.5px; padding-bottom: 8px;
    border-bottom: 2px solid var(--accent); margin-bottom: 18px; display: inline-block;
  }

  /* SECTION DIVIDER */
  .section-rule {
    border: none; border-top: 1px solid var(--border); margin: 0 0 40px;
  }

  /* BIG THEME */
  .big-theme-title {
    font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 600;
    color: var(--navy); line-height: 1.3; margin-bottom: 18px;
  }

  /* PROSE */
  .brief-text {
    font-size: 14.5px; line-height: 1.8; color: #2c2c3e; font-weight: 300;
  }
  .brief-text + .brief-text { margin-top: 12px; }

  /* MACRO REGIME */
  .regime-table {
    width: 100%; border-collapse: collapse;
    font-family: 'Raleway', sans-serif; font-size: 12.5px;
  }
  .regime-table thead tr { background: var(--navy); color: var(--white); }
  .regime-table thead th {
    padding: 10px 14px; text-align: left; font-weight: 500;
    letter-spacing: 1px; font-size: 10px; text-transform: uppercase;
  }
  .regime-table tbody tr { border-bottom: 1px solid var(--border); }
  .regime-table tbody tr:nth-child(even) { background: var(--off-white); }
  .regime-table tbody td { padding: 10px 14px; }
  .signal-green  { color: var(--green); font-weight: 700; }
  .signal-yellow { color: var(--amber); font-weight: 700; }
  .signal-red    { color: var(--red);   font-weight: 700; }

  /* DATA TABLES */
  .data-table {
    width: 100%; border-collapse: collapse;
    font-family: 'Raleway', sans-serif; font-size: 12.5px;
  }
  .data-table thead tr { background: var(--navy); color: var(--white); }
  .data-table thead th {
    padding: 9px 14px; text-align: left; font-weight: 500;
    letter-spacing: 1px; font-size: 10px; text-transform: uppercase;
  }
  .data-table tbody tr { border-bottom: 1px solid var(--border); }
  .data-table tbody tr:nth-child(even) { background: var(--off-white); }
  .data-table tbody td { padding: 9px 14px; }
  .data-table + .data-table { margin-top: 24px; }
  .pct { font-weight: 600; }
  .pct.positive { color: var(--green); }
  .pct.negative { color: var(--red); }

  .table-label {
    font-family: 'Raleway', sans-serif; font-size: 9px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase; color: var(--muted);
    margin: 20px 0 6px;
  }
  .table-label:first-child { margin-top: 0; }

  /* POSITIONING */
  .positioning-list { list-style: none; padding: 0; }
  .positioning-list li {
    font-size: 14px; line-height: 1.7; color: #2c2c3e; font-weight: 300;
    padding: 10px 14px 10px 28px; position: relative;
    border-left: 3px solid var(--accent); background: var(--off-white);
    margin-bottom: 8px;
  }
  .positioning-list li::before {
    content: '\\2192'; position: absolute; left: 10px; color: var(--accent); font-weight: 600;
  }

  /* UPCOMING EVENTS */
  .imp-high   { color: var(--red);   font-weight: 700; font-size: 11px; }
  .imp-medium { color: var(--amber); font-weight: 600; font-size: 11px; }
  .imp-low    { color: var(--muted); font-weight: 400; font-size: 11px; }

  /* SUBSCRIBE */
  .subscribe-section { background: var(--navy); padding: 36px 40px; text-align: center; }
  .subscribe-section h2 {
    font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 600;
    color: var(--white); margin: 0 0 6px; letter-spacing: 0.5px;
  }
  .subscribe-section p {
    font-family: 'Raleway', sans-serif; font-size: 11px; color: rgba(255,255,255,0.55);
    letter-spacing: 1px; text-transform: uppercase; margin: 0 0 20px;
  }
  .subscribe-form { display: flex; justify-content: center; max-width: 440px; margin: 0 auto; }
  .subscribe-form input[type="email"] {
    flex: 1; padding: 10px 16px; font-family: 'Raleway', sans-serif; font-size: 12px;
    border: 1px solid rgba(255,255,255,0.2); border-right: none;
    border-radius: 2px 0 0 2px; background: rgba(255,255,255,0.08);
    color: var(--white); outline: none;
  }
  .subscribe-form input[type="email"]::placeholder { color: rgba(255,255,255,0.35); }
  .subscribe-form button {
    padding: 10px 20px; font-family: 'Raleway', sans-serif; font-size: 10px;
    font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    background: var(--accent); color: var(--white); border: none;
    border-radius: 0 2px 2px 0; cursor: pointer; transition: background 0.2s; white-space: nowrap;
  }
  .subscribe-form button:hover { background: var(--accent-lt); }

  /* SHARE BAR */
  .share-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 40px; border-top: 1px solid var(--border); background: var(--off-white);
  }
  .share-label {
    font-family: 'Raleway', sans-serif; font-size: 10px; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase; color: var(--muted);
  }
  .share-buttons { display: flex; gap: 10px; }
  .share-btn {
    display: flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; border-radius: 50%; background: var(--navy);
    color: white; text-decoration: none; transition: background 0.2s;
  }
  .share-btn:hover { background: var(--accent); }
  .share-btn svg { width: 16px; height: 16px; fill: white; }

  /* FOOTER */
  .footer {
    background: var(--navy); padding: 16px 40px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .footer-logo {
    font-family: 'Cormorant Garamond', serif; font-size: 13px; font-weight: 400;
    letter-spacing: 2px; color: rgba(255,255,255,0.5);
  }
  .footer-logo span { color: var(--accent); }
  .footer-disclaimer {
    font-family: 'Raleway', sans-serif; font-size: 8.5px;
    color: rgba(255,255,255,0.3); letter-spacing: 0.5px;
    text-align: right; max-width: 380px; line-height: 1.6;
  }

  @media (max-width: 600px) {
    .header-inner { padding: 20px 20px 16px; flex-wrap: wrap; }
    .content { padding: 24px 20px; }
    .footer { padding: 14px 20px; flex-direction: column; gap: 10px; }
    .share-bar { padding: 16px 20px; }
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

def _pct_str(val, is_yield=False, bps=None):
    if is_yield:
        return f"{bps:+.0f} bps" if bps is not None else "—"
    return f"{val:+.2f}%" if val is not None else "—"


def _pct_class(val, is_yield=False, bps=None):
    num = bps if is_yield else val
    if num is None:
        return "pct"
    return "pct positive" if num >= 0 else "pct negative"


def _signal_cls(signal):
    return {"green": "signal-green", "yellow": "signal-yellow", "red": "signal-red"}.get(
        (signal or "").lower(), ""
    )


def _signal_dot(signal):
    labels = {"green": "&#9679;&nbsp;GREEN", "yellow": "&#9679;&nbsp;YELLOW", "red": "&#9679;&nbsp;RED"}
    return labels.get((signal or "").lower(), signal or "—")


def _md_inline(text):
    """Convert **bold** and *italic* markdown to HTML inline elements."""
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         text)
    return text


def _paras(text):
    html = ""
    for para in (text or "").split("\n\n"):
        para = para.strip()
        if para:
            html += f'<p class="brief-text">{_md_inline(para)}</p>\n'
    return html


def _positioning_html(text):
    items = ""
    for line in (text or "").splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            items += f"<li>{_md_inline(line[2:].strip())}</li>\n"
        elif line:
            items += f"<li>{line}</li>\n"
    return f'<ul class="positioning-list">\n{items}</ul>' if items else "<p>—</p>"


def _equity_table(indices, label):
    if not indices:
        return ""
    rows = ""
    for idx in indices:
        is_yield = idx.get("is_yield", False)
        bps   = idx.get("yield_change_bps")
        pct_s = _pct_str(idx.get("weekly_pct"), is_yield, bps)
        pct_c = _pct_class(idx.get("weekly_pct"), is_yield, bps)
        close = idx.get("close")
        wl, wh = idx.get("week_low"), idx.get("week_high")
        close_s = f"{close:,.2f}" if close is not None else "—"
        range_s = f"{wl:,.2f} – {wh:,.2f}" if (wl is not None and wh is not None) else "—"
        rows += f"""
            <tr>
              <td>{idx['name']}</td>
              <td>{close_s}</td>
              <td class="{pct_c}">{pct_s}</td>
              <td>{range_s}</td>
            </tr>"""
    return f"""
      <div class="table-label">{label}</div>
      <table class="data-table">
        <thead><tr><th>Index</th><th>Close</th><th>Weekly %</th><th>Week Range</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>"""


def _fx_table(fx_list):
    if not fx_list:
        return ""
    rows = ""
    for fx in fx_list:
        pct   = fx.get("weekly_pct")
        rate  = fx.get("rate")
        pct_s = _pct_str(pct)
        pct_c = _pct_class(pct)
        rate_s = f"{rate:.4f}" if rate is not None else "—"
        rows += f"""
            <tr>
              <td>{fx['name']}</td>
              <td>{rate_s}</td>
              <td class="{pct_c}">{pct_s}</td>
            </tr>"""
    return f"""
      <div class="table-label">Currencies (vs. USD)</div>
      <table class="data-table">
        <thead><tr><th>Pair</th><th>Rate</th><th>Weekly %</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>"""


def _commodity_table(commodities):
    if not commodities:
        return ""
    rows = ""
    for c in commodities:
        is_yield = c.get("is_yield", False)
        bps   = c.get("yield_change_bps")
        pct_s = _pct_str(c.get("weekly_pct"), is_yield, bps)
        pct_c = _pct_class(c.get("weekly_pct"), is_yield, bps)
        close = c.get("close")
        close_s = f"{close:,.2f}" if close is not None else "—"
        rows += f"""
            <tr>
              <td>{c['name']}</td>
              <td>{close_s}</td>
              <td class="{pct_c}">{pct_s}</td>
            </tr>"""
    return f"""
      <div class="table-label">Commodities &amp; Metals</div>
      <table class="data-table">
        <thead><tr><th>Asset</th><th>Close</th><th>Weekly %</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>"""


def _upcoming_rows(events):
    rows = ""
    for ev in events:
        imp = ev.get("importance", 1)
        if imp >= 3:
            cls, label = "imp-high", "High"
        elif imp == 2:
            cls, label = "imp-medium", "Medium"
        else:
            cls, label = "imp-low", "Low"
        rows += f"""
            <tr>
              <td>{ev.get('date', '')}</td>
              <td>{ev.get('event', '')}</td>
              <td class="{cls}">{label}</td>
            </tr>"""
    return rows


# ── Main render ───────────────────────────────────────────────────────────────

def render_html(ctx):
    """Render the Global Investor Edition as a vertical HTML page."""
    date_str     = ctx.get("date", "")
    display_date = ctx.get("date_display", date_str)

    # ── Macro regime table ────────────────────────────────────────────────────
    regime = ctx.get("macro_regime", {})
    regime_rows = ""
    for key, label in [
        ("growth",         "Growth"),
        ("inflation",      "Inflation"),
        ("rate_direction", "Rate Direction"),
        ("risk_appetite",  "Risk Appetite"),
    ]:
        r   = regime.get(key, {})
        sig = r.get("signal", "")
        note = r.get("note", "")
        regime_rows += f"""
            <tr>
              <td>{label}</td>
              <td class="{_signal_cls(sig)}">{_signal_dot(sig)}</td>
              <td>{note}</td>
            </tr>"""

    # ── Appendix tables ───────────────────────────────────────────────────────
    us_table     = _equity_table(ctx.get("us_indices", []),   "US Equities")
    fi_table     = _equity_table(ctx.get("fixed_income", []), "Fixed Income &amp; USD")
    eu_table     = _equity_table(ctx.get("eu_indices", []),   "European Equities")
    apac_table   = _equity_table(ctx.get("apac_indices", []), "Asia-Pacific Equities")
    fx_table     = _fx_table(ctx.get("fx", []))
    com_table    = _commodity_table(ctx.get("commodities", []))

    # ── Upcoming events ───────────────────────────────────────────────────────
    upcoming_rows = _upcoming_rows(ctx.get("upcoming_events", []))
    upcoming_table = f"""
      <table class="data-table">
        <thead><tr><th>Date</th><th>Event</th><th>Importance</th></tr></thead>
        <tbody>{upcoming_rows}</tbody>
      </table>""" if upcoming_rows else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Framework Foundry &mdash; Global Investor Edition &middot; {date_str}</title>
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
{_LOGO_SVG}
      <div class="logo-text">
        <span class="logo-name-framework">FRAMEWORK</span>
        <span class="logo-name-foundry">FOUNDRY</span>
        <div class="logo-rule"></div>
        <span class="logo-tagline">Global Investor Edition &nbsp;&middot;&nbsp; Research for the serious investor</span>
      </div>
      <div class="header-meta">
        <span class="issue-label">Week Ending</span>
        <span class="issue-date">{display_date}</span>
        <span class="issue-edition">&#127758; Global Edition</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

  <!-- REGION BANNER -->
  <div class="region-banner">
    <span>Coverage: US &middot; Europe &middot; Asia-Pacific &middot; FX &middot; Commodities &middot; Macro</span>
    <div class="region-dots">
      <span class="region-dot">&#127482;&#127480;</span>
      <span class="region-dot">&#127466;&#127482;</span>
      <span class="region-dot">&#127471;&#127477;</span>
    </div>
  </div>

  <div class="content">

    <!-- BIG THEME -->
    <div class="section-block">
      <div class="big-theme-title">{ctx.get('big_theme_title', '')}</div>
      {_paras(ctx.get('big_theme_body', ''))}
    </div>

    <hr class="section-rule"/>

    <!-- MACRO REGIME -->
    <div class="section-block">
      <div class="section-title">Macro Regime Snapshot</div>
      <table class="regime-table">
        <thead><tr><th>Variable</th><th>Signal</th><th>Note</th></tr></thead>
        <tbody>{regime_rows}</tbody>
      </table>
    </div>

    <hr class="section-rule"/>

    <!-- EQUITY MARKETS -->
    <div class="section-block">
      <div class="section-title">Equity Markets</div>
      {_paras(ctx.get('equity_narrative', ''))}
    </div>

    <!-- CURRENCY MARKETS -->
    <div class="section-block">
      <div class="section-title">Currency Markets</div>
      {_paras(ctx.get('fx_narrative', ''))}
    </div>

    <!-- COMMODITIES -->
    <div class="section-block">
      <div class="section-title">Commodities &amp; Metals</div>
      {_paras(ctx.get('commodities_narrative', ''))}
    </div>

    <hr class="section-rule"/>

    <!-- THIS WEEK'S EVENTS -->
    <div class="section-block">
      <div class="section-title">This Week&rsquo;s Economic Events</div>
      {_paras(ctx.get('events_commentary', ''))}
    </div>

    <!-- NEXT WEEK -->
    <div class="section-block">
      <div class="section-title">Next Week: What to Watch</div>
      {_paras(ctx.get('next_week_commentary', ''))}
      {upcoming_table}
    </div>

    <!-- POSITIONING -->
    <div class="section-block">
      <div class="section-title">Global Investor Positioning</div>
      {_positioning_html(ctx.get('positioning', ''))}
    </div>

    <hr class="section-rule"/>

    <!-- DATA APPENDIX -->
    <div class="section-block">
      <div class="section-title">Data Appendix</div>
      {us_table}
      {fi_table}
      {eu_table}
      {apac_table}
      {fx_table}
      {com_table}
    </div>

  </div><!-- /content -->

  <!-- SUBSCRIBE -->
  <div class="subscribe-section">
    <h2>Stay in the loop</h2>
    <p>Free weekly global market intelligence, every weekend.</p>
    <form class="subscribe-form" action="https://formspree.io/f/mwpvyoal" method="POST">
      <input type="email" name="email" placeholder="your@email.com" required />
      <button type="submit">Subscribe</button>
    </form>
  </div>

  <!-- SHARE BAR -->
  <div class="share-bar">
    <span class="share-label">Share this edition</span>
    <div class="share-buttons">
      <a class="share-btn" href="#" target="_blank" rel="noopener"
         onclick="this.href='https://twitter.com/intent/tweet?text='+encodeURIComponent('Global markets this week via Framework Foundry \u2014 '+window.location.href);return true;"
         title="Share on X / Twitter">
        <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a class="share-btn" href="#" target="_blank" rel="noopener"
         onclick="this.href='https://www.linkedin.com/sharing/share-offsite/?url='+encodeURIComponent(window.location.href);return true;"
         title="Share on LinkedIn">
        <svg viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
      </a>
    </div>
  </div>

  <!-- FOOTER -->
  <footer class="footer">
    <div class="footer-logo">FRAMEWORK <span>FOUNDRY</span> &nbsp;&middot;&nbsp; <span style="color:rgba(255,255,255,0.35);font-size:10px;letter-spacing:1px;">GLOBAL EDITION</span></div>
    <div class="footer-disclaimer">
      Disclaimer: For informational purposes only. Not investment advice.<br/>
      Past performance is not indicative of future results.
    </div>
  </footer>

</div><!-- /page -->
</body>
</html>"""
