#!/usr/bin/env python3
"""Build the unified static site for Cloudflare Pages deployment.

Run from weekly-newsletter/:
    python build_combined_site.py           # mock data
    python build_combined_site.py --live    # live API data
"""

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from build_site import render_html as render_us_html
from intl_build_site import render_html as render_intl_html
from daybreak_build_site import render_html as render_daybreak_html
from data.fetch_data import fetch_index_data, fetch_econ_calendar
from data.process_data import process_index_data, build_template_context
from data.fetch_intl_data import fetch_intl_index_data, fetch_intl_fx_data, fetch_intl_econ_calendar
from data.intl_process_data import process_intl_index_data, process_fx_data, build_intl_template_context
from data.fetch_daybreak_data import fetch_daybreak_data
from data.daybreak_process_data import build_daybreak_context

OUTPUT_DIR = BASE_DIR / "output"
SITE_DIR = BASE_DIR / "site"

# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """\
  :root {
    --navy:      #0f1f3d;
    --navy-mid:  #1a3260;
    --accent:    #4a7fb5;
    --accent-lt: #7aabda;
    --gold:      #c9a84c;
    --gold-lt:   #e0c97a;
    --white:     #ffffff;
    --off-white: #f5f4f0;
    --text:      #1a1a2e;
    --border:    #ddd8cc;
    --muted:     #6b7280;
    --green:     #2a7d4f;
    --red:       #b91c1c;
    --bg:        #dde3ea;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    font-family: 'Source Serif 4', Georgia, serif;
    color: var(--text);
    padding: 32px 16px;
    min-height: 100vh;
  }

  .page {
    max-width: 900px;
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

  /* SECTION NAV (top-level tabs) */
  .section-nav {
    background: var(--navy);
    padding: 0 40px;
    display: flex;
    border-bottom: 2px solid rgba(255,255,255,0.08);
    gap: 0;
  }

  .section-tab {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 3px; text-transform: uppercase;
    color: rgba(255,255,255,0.45);
    text-decoration: none;
    padding: 13px 22px;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: color 0.15s;
    white-space: nowrap;
    cursor: pointer;
  }

  .section-tab:hover { color: rgba(255,255,255,0.8); }
  .section-tab.active { color: var(--white); border-bottom-color: var(--gold); }
  .section-tab.future { color: rgba(255,255,255,0.2); font-style: italic; }
  .section-tab.future:hover { color: rgba(255,255,255,0.4); }

  /* SUB-NAV (within Markets section) */
  .sub-nav {
    background: var(--off-white);
    border-bottom: 1px solid var(--border);
    padding: 0 40px;
    display: flex;
    gap: 0;
  }

  .sub-tab {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted);
    text-decoration: none;
    padding: 10px 18px;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    cursor: pointer;
    transition: color 0.15s;
  }

  .sub-tab:hover { color: var(--navy); }
  .sub-tab.active { color: var(--accent); border-bottom-color: var(--accent); }

  /* SECTION PANELS */
  .section-panel { display: none; }
  .section-panel.active { display: block; }

  /* SUB-PANELS (within Markets) */
  .sub-panel { display: none; }
  .sub-panel.active { display: block; }

  /* CONTENT */
  .content { padding: 36px 40px; }

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

  .section-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 19px; font-weight: 600;
    color: var(--navy); letter-spacing: 0.5px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent);
    margin-bottom: 18px; display: inline-block;
  }

  /* MARKET IQ */
  .iq-intro {
    font-family: 'Source Serif 4', serif;
    font-size: 15px; line-height: 1.7;
    color: #2c2c3e; font-weight: 300;
    margin-bottom: 32px;
    padding-bottom: 24px; border-bottom: 1px solid var(--border);
  }

  .iq-categories {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 28px;
  }

  .iq-cat-btn {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
    padding: 6px 14px; border: 1px solid var(--border);
    background: var(--white); color: var(--muted);
    cursor: pointer; transition: all 0.15s;
  }

  .iq-cat-btn:hover, .iq-cat-btn.active {
    background: var(--navy); color: var(--white); border-color: var(--navy);
  }

  .iq-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px; margin-bottom: 16px;
  }

  .iq-card {
    border: 1px solid var(--border);
    background: var(--off-white);
    padding: 0; cursor: pointer;
    transition: box-shadow 0.2s, transform 0.15s;
    position: relative; overflow: hidden;
  }

  .iq-card:hover {
    box-shadow: 0 4px 20px rgba(15,31,61,0.12);
    transform: translateY(-2px);
  }

  .iq-card-top { background: var(--navy); padding: 14px 16px 12px; }

  .iq-card-category {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 600;
    letter-spacing: 2.5px; text-transform: uppercase;
    color: var(--gold); margin-bottom: 4px;
  }

  .iq-card-term {
    font-family: 'Cormorant Garamond', serif;
    font-size: 18px; font-weight: 600;
    color: var(--white); line-height: 1.1;
  }

  .iq-card-body { padding: 14px 16px; }

  .iq-card-def {
    font-family: 'Source Serif 4', serif;
    font-size: 12.5px; line-height: 1.6;
    color: #3a3a4a; font-weight: 300;
    margin-bottom: 10px;
  }

  .iq-card-meta {
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid var(--border); padding-top: 10px;
  }

  .iq-card-freq {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--muted);
  }

  .iq-card-trend {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 700;
    letter-spacing: 1px;
    padding: 3px 8px; border-radius: 2px;
  }

  .trend-up   { background: #d4edda; color: #155724; }
  .trend-down { background: #f8d7da; color: #721c24; }
  .trend-flat { background: #e8e8e8; color: #555; }

  .iq-see-all {
    text-align: center; padding: 20px 0 4px;
    font-family: 'Raleway', sans-serif;
    font-size: 10px; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
  }

  .iq-see-all a {
    color: var(--accent); text-decoration: none;
    border-bottom: 1px solid var(--accent); padding-bottom: 2px;
  }

  /* PERSONAL INVESTING */
  .investing-intro {
    font-family: 'Source Serif 4', serif;
    font-size: 15px; line-height: 1.7;
    color: #2c2c3e; font-weight: 300;
    margin-bottom: 32px;
    padding-bottom: 24px; border-bottom: 1px solid var(--border);
  }

  .article-filters {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 28px;
  }

  .article-list { display: flex; flex-direction: column; gap: 0; }

  .article-row {
    display: grid;
    grid-template-columns: 80px 1fr auto;
    gap: 20px; align-items: start;
    padding: 22px 0; border-bottom: 1px solid var(--border);
    text-decoration: none; color: inherit;
    transition: background 0.15s;
  }

  .article-row:hover { background: var(--off-white); margin: 0 -40px; padding: 22px 40px; }
  .article-row:first-child { border-top: 1px solid var(--border); }

  .article-tag-col { padding-top: 3px; }

  .article-tag {
    display: inline-block;
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase;
    padding: 4px 8px; background: var(--navy); color: var(--white);
  }

  .article-tag.etf  { background: var(--accent); }
  .article-tag.guide { background: var(--navy-mid); }
  .article-tag.intl { background: #1a5c3a; }

  .article-content { min-width: 0; }

  .article-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 20px; font-weight: 600;
    color: var(--navy); line-height: 1.2; margin-bottom: 6px;
  }

  .article-excerpt {
    font-family: 'Source Serif 4', serif;
    font-size: 13px; line-height: 1.65;
    color: #5a5a6a; font-weight: 300;
  }

  .article-meta-col { text-align: right; white-space: nowrap; padding-top: 4px; }

  .article-date {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 500;
    letter-spacing: 1px; color: var(--muted); display: block;
  }

  .article-read-time {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; color: var(--muted); margin-top: 4px; display: block;
  }

  /* EXPAT / COMING SOON */
  .coming-soon-panel {
    padding: 60px 40px; text-align: center;
    background: var(--off-white); border-top: 4px solid var(--gold);
  }

  .coming-soon-eyebrow {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--gold); margin-bottom: 16px;
  }

  .coming-soon-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 32px; font-weight: 600;
    color: var(--navy); margin-bottom: 14px;
  }

  .coming-soon-body {
    font-family: 'Source Serif 4', serif;
    font-size: 15px; line-height: 1.7; font-weight: 300;
    color: #4a4a5a; max-width: 460px; margin: 0 auto 28px;
  }

  .notify-form {
    display: flex; justify-content: center; gap: 0;
    max-width: 400px; margin: 0 auto;
  }

  .notify-form input {
    flex: 1; padding: 10px 16px;
    font-family: 'Raleway', sans-serif; font-size: 12px;
    border: 1px solid var(--border); border-right: none;
    background: var(--white); color: var(--text); outline: none;
  }

  .notify-form button {
    padding: 10px 18px;
    font-family: 'Raleway', sans-serif; font-size: 9px;
    font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    background: var(--gold); color: var(--navy);
    border: none; cursor: pointer; transition: background 0.2s;
  }

  .notify-form button:hover { background: var(--gold-lt); }

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

  /* SUBSCRIBE */
  .subscribe-section {
    background: var(--navy);
    padding: 36px 40px;
    text-align: center;
  }

  .subscribe-section h2 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 22px;
    font-weight: 600;
    color: var(--white);
    margin: 0 0 6px;
    letter-spacing: 0.5px;
  }

  .subscribe-section p {
    font-family: 'Raleway', sans-serif;
    font-size: 11px;
    color: rgba(255,255,255,0.55);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 0 0 20px;
  }

  .subscribe-form {
    display: flex;
    justify-content: center;
    gap: 0;
    max-width: 440px;
    margin: 0 auto;
  }

  .subscribe-form input[type="email"] {
    flex: 1;
    padding: 10px 16px;
    font-family: 'Raleway', sans-serif;
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.2);
    border-right: none;
    border-radius: 2px 0 0 2px;
    background: rgba(255,255,255,0.08);
    color: var(--white);
    outline: none;
  }

  .subscribe-form input[type="email"]::placeholder { color: rgba(255,255,255,0.35); }

  .subscribe-form button {
    padding: 10px 20px;
    font-family: 'Raleway', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    background: var(--accent);
    color: var(--white);
    border: none;
    border-radius: 0 2px 2px 0;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .subscribe-form button:hover { background: var(--accent-lt); }

  @media (max-width: 600px) {
    .subscribe-section { padding: 28px 20px; }
    .subscribe-form { flex-direction: column; }
    .subscribe-form input[type="email"] {
      border-right: 1px solid rgba(255,255,255,0.2);
      border-bottom: none;
      border-radius: 2px 2px 0 0;
    }
    .subscribe-form button { border-radius: 0 0 2px 2px; }
  }

  /* SHARE BAR */
  .share-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 40px;
    border-top: 1px solid var(--border);
    background: var(--off-white);
  }

  .share-label {
    font-family: 'Raleway', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
  }

  .share-buttons { display: flex; gap: 10px; }

  .share-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--navy);
    color: white;
    text-decoration: none;
    transition: background 0.2s;
  }

  .share-btn:hover { background: var(--accent); }
  .share-btn svg { width: 16px; height: 16px; fill: white; }

  @media (max-width: 680px) {
    .header-inner { padding: 20px 20px 16px; flex-wrap: wrap; }
    .section-nav  { padding: 0 16px; overflow-x: auto; }
    .sub-nav      { padding: 0 16px; overflow-x: auto; }
    .content      { padding: 24px 20px; }
    .hero-grid    { grid-template-columns: 1fr; }
    .iq-grid      { grid-template-columns: 1fr 1fr; }
    .footer       { padding: 14px 20px; flex-direction: column; gap: 10px; }
    .share-bar    { padding: 14px 20px; }
    .subscribe-section { padding: 28px 20px; }
    .article-row  { grid-template-columns: 70px 1fr; }
    .article-meta-col { display: none; }
    .subscribe-form { flex-direction: column; }
    .subscribe-form input[type="email"] {
      border-right: 1px solid rgba(255,255,255,0.2);
      border-bottom: none;
      border-radius: 2px 2px 0 0;
    }
    .subscribe-form button { border-radius: 0 0 2px 2px; }
  }
  @media (max-width: 460px) {
    .iq-grid { grid-template-columns: 1fr; }
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

_SECTION_NAV = """\
  <nav class="section-nav">
    <a class="section-tab active" onclick="showSection('markets')">Markets</a>
    <a class="section-tab" onclick="showSection('marketiq')">Market IQ</a>
    <a class="section-tab" onclick="showSection('investing')">Investing</a>
    <a class="section-tab future" onclick="showSection('expat')">Expat Investing &#8599;</a>
  </nav>"""

_NAV_TABS_DAILY = """\
  <div class="section-nav" style="display:flex;">
    <a class="section-tab" href="../index.html">Markets</a>
    <a class="section-tab" href="../index.html">Market IQ</a>
    <a class="section-tab" href="../index.html">Investing</a>
    <a class="section-tab future" style="cursor:default;">Expat Investing &#8599;</a>
    <a class="section-tab active" style="border-bottom-color:#c9a84c;color:#c9a84c;" href="index.html">Market Day Break</a>
  </div>"""


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


def find_daybreak_dates():
    """Sorted (newest first) list of Market Day Break dates in output/."""
    dates = []
    for f in OUTPUT_DIR.glob("market_day_break_*.md"):
        m = re.match(r"market_day_break_(\d{4}-\d{2}-\d{2})\.md$", f.name)
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
    elif edition == "intl":
        candidates = [
            OUTPUT_DIR / f"intl_newsletter_{date_str}.pdf",
            OUTPUT_DIR / f"intl_newsletter_us_{date_str}.pdf",
        ]
    else:  # daily
        candidates = [
            OUTPUT_DIR / f"market_day_break_{date_str}.pdf",
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
      <a class="hero-cta" href="us/{date_str}/index.html">Read Issue &rarr;</a>
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
      <a class="hero-cta" href="intl/{date_str}/index.html">Read Issue &rarr;</a>
    </div>"""


_DAYBREAK_PREVIEW_FUTURES = ["S&P Futures", "Nasdaq Futures", "Dow Futures"]


def _render_daybreak_hero(date_str, ctx):
    display = fmt_date(date_str)
    futures_lookup = {f["name"]: f for f in ctx.get("futures", [])}
    rows = ""
    for name in _DAYBREAK_PREVIEW_FUTURES:
        fut = futures_lookup.get(name)
        if not fut:
            continue
        pct  = fut.get("daily_pct")
        val  = f"{pct:+.2f}%" if pct is not None else "--"
        cls  = "pct-pos" if (pct is not None and pct >= 0) else "pct-neg"
        rows += f'<div class="hero-idx-row"><span>{name}</span><span class="{cls}">{val}</span></div>\n'
    return f"""
    <div class="hero-card hero-card--daily" style="border-top-color:#c9a84c;">
      <div class="hero-card-edition" style="color:#c9a84c;">&#127760; Daily Edition</div>
      <div class="hero-card-date">{display}</div>
      <div style="font-family:'Raleway',sans-serif;font-size:9px;letter-spacing:1.5px;color:#6b7280;text-transform:uppercase;margin-bottom:14px;">Data as of 5:00 AM EST</div>
      <div class="hero-indices">{rows}</div>
      <a class="hero-cta" href="daily/{date_str}/index.html">Read Brief &rarr;</a>
    </div>"""


# ── Content loaders ───────────────────────────────────────────────────────────

_TREND_CLASS = {"up": "trend-up", "down": "trend-down", "flat": "trend-flat"}


def load_market_iq_cards(csv_path=None):
    """Load Market IQ flashcard data from CSV. Returns list of dicts."""
    if csv_path is None:
        csv_path = BASE_DIR / "content" / "market_iq.csv"
    cards = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["trend_class"] = _TREND_CLASS.get(row.get("trend", "flat"), "trend-flat")
                cards.append(row)
    except FileNotFoundError:
        pass
    return cards


def load_articles(articles_dir=None):
    """Load article metadata from Markdown frontmatter. Returns list sorted newest first."""
    if articles_dir is None:
        articles_dir = BASE_DIR / "content" / "articles"
    articles = []
    try:
        for md_file in sorted(Path(articles_dir).glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            # Split on YAML frontmatter fences
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            fm_text = parts[1]
            article = {}
            for line in fm_text.splitlines():
                m = re.match(r'^(\w[\w_-]*):\s*(.+)$', line.strip())
                if m:
                    article[m.group(1)] = m.group(2).strip().strip('"')
            if article.get("title"):
                articles.append(article)
    except (FileNotFoundError, OSError):
        pass
    # Sort by date descending
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)
    return articles


def render_market_iq_panel(cards):
    """Render the Market IQ panel HTML."""
    # Extract unique categories preserving order
    seen = set()
    categories = []
    for c in cards:
        cat = c.get("category", "")
        if cat and cat not in seen:
            seen.add(cat)
            categories.append(cat)

    cat_buttons = '<button class="iq-cat-btn active">All</button>\n'
    for cat in categories:
        cat_buttons += f'      <button class="iq-cat-btn">{cat}</button>\n'

    card_html = ""
    for c in cards:
        term = c.get("term", "")
        category = c.get("category", "")
        definition = c.get("definition", "")
        frequency = c.get("frequency", "")
        trend_label = c.get("trend_label", "")
        trend_class = c.get("trend_class", "trend-flat")
        card_html += f"""
      <div class="iq-card">
        <div class="iq-card-top">
          <div class="iq-card-category">{category}</div>
          <div class="iq-card-term">{term}</div>
        </div>
        <div class="iq-card-body">
          <p class="iq-card-def">{definition}</p>
          <div class="iq-card-meta">
            <span class="iq-card-freq">Published: {frequency}</span>
            <span class="iq-card-trend {trend_class}">{trend_label}</span>
          </div>
        </div>
      </div>"""

    return f"""<div id="panel-marketiq" class="section-panel">
  <div class="content">
    <div class="section-label">Market IQ &mdash; Economic Concepts, Plain &amp; Simple</div>
    <p class="iq-intro">
      No economics degree required. Each card explains one concept &mdash; what it is, why it matters,
      how often it&rsquo;s published, and what the recent trend means for your money.
    </p>
    <div class="iq-categories">
      {cat_buttons}
    </div>
    <div class="iq-grid">
      {card_html}
    </div>
    <div class="iq-see-all"><a href="#">View all concepts &rarr;</a></div>
  </div>
</div>"""


def render_investing_panel(articles):
    """Render the Personal Investing panel HTML."""
    article_html = ""
    for a in articles:
        title = a.get("title", "")
        excerpt = a.get("excerpt", "")
        tag = a.get("tag", "")
        tag_class = a.get("tag_class", "")
        date_str = a.get("date", "")
        read_time = a.get("read_time", "")
        # Format date YYYY-MM-DD → "Mar 1, 2026"
        try:
            d = datetime.strptime(str(date_str), "%Y-%m-%d")
            display_date = f"{d.strftime('%b')} {d.day}, {d.year}"
        except ValueError:
            display_date = date_str

        article_html += f"""
      <a class="article-row" href="#">
        <div class="article-tag-col">
          <span class="article-tag {tag_class}">{tag}</span>
        </div>
        <div class="article-content">
          <div class="article-title">{title}</div>
          <div class="article-excerpt">{excerpt}</div>
        </div>
        <div class="article-meta-col">
          <span class="article-date">{display_date}</span>
          <span class="article-read-time">{read_time}</span>
        </div>
      </a>"""

    return f"""<div id="panel-investing" class="section-panel">
  <div class="content">
    <div class="section-label">Personal Investing &mdash; Practical Guides for Long-Term Investors</div>
    <p class="investing-intro">
      Research-backed guides on building a diversified portfolio with low-cost index ETFs.
      No jargon, no stock tips &mdash; just clear frameworks for the patient investor.
    </p>
    <div class="article-filters">
      <button class="iq-cat-btn active">All</button>
      <button class="iq-cat-btn">ETF Basics</button>
      <button class="iq-cat-btn">US Portfolios</button>
      <button class="iq-cat-btn">International</button>
      <button class="iq-cat-btn">Sector ETFs</button>
      <button class="iq-cat-btn">Strategy</button>
    </div>
    <div class="article-list">
      {article_html}
    </div>
  </div>
</div>"""


_EXPAT_PANEL = """\
<div id="panel-expat" class="section-panel">
  <div class="coming-soon-panel">
    <div class="coming-soon-eyebrow">Coming Soon</div>
    <div class="coming-soon-title">Expat Investing</div>
    <p class="coming-soon-body">
      A dedicated resource for Americans living abroad &mdash; navigating PFIC rules, FBAR reporting,
      tax-efficient investing from outside the US, and building wealth across borders.
      Leave your email to be notified when we launch.
    </p>
    <div class="notify-form">
      <input type="email" placeholder="your@email.com"/>
      <button>Notify Me</button>
    </div>
  </div>
</div>"""

_JS = """\
<script>
function showSection(id) {
  document.querySelectorAll('.section-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.section-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('active');
  var labels = { markets: 0, marketiq: 1, investing: 2, expat: 3 };
  var tabs = document.querySelectorAll('.section-tab');
  if (labels[id] !== undefined) tabs[labels[id]].classList.add('active');
}
function showSubNav(el) {
  var nav = el.closest('.sub-nav');
  nav.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  var target = el.getAttribute('data-target');
  if (target) {
    el.closest('.section-panel').querySelectorAll('.sub-panel')
      .forEach(p => p.classList.remove('active'));
    document.getElementById(target).classList.add('active');
  }
}
document.querySelectorAll('.iq-categories .iq-cat-btn, .article-filters .iq-cat-btn')
  .forEach(function(btn) {
    btn.addEventListener('click', function() {
      this.closest('.iq-categories, .article-filters')
          .querySelectorAll('.iq-cat-btn')
          .forEach(function(b) { b.classList.remove('active'); });
      this.classList.add('active');
    });
  });
</script>"""


# ── Landing page ──────────────────────────────────────────────────────────────

def render_landing(us_dates, intl_dates, us_ctxs, intl_ctxs, pdf_map,
                   daybreak_dates=None, daybreak_ctxs=None,
                   market_iq_cards=None, articles=None):
    """Render site/index.html — 4-tab hub (Markets / Market IQ / Investing / Expat)."""
    if daybreak_dates is None:
        daybreak_dates = []
    if market_iq_cards is None:
        market_iq_cards = []
    if articles is None:
        articles = []

    # Hero cards (latest of each weekly edition)
    latest_us   = us_dates[0]   if us_dates   else None
    latest_intl = intl_dates[0] if intl_dates else None

    us_hero = _render_us_hero(latest_us, us_ctxs[latest_us]) if latest_us else \
        '<div class="hero-card no-issue">No US issue yet</div>'
    intl_hero = _render_intl_hero(latest_intl, intl_ctxs[latest_intl]) if latest_intl else \
        '<div class="hero-card no-issue">No International issue yet</div>'

    # Archive: weekly dates only (US + Intl)
    all_dates = sorted(set(us_dates) | set(intl_dates), reverse=True)
    archive_rows = ""
    for d in all_dates:
        display = fmt_date(d)
        if d in us_dates:
            us_html_link = f'<a class="archive-link" href="us/{d}/index.html">Read</a>'
            us_pdf_name  = pdf_map.get(("us", d))
            us_pdf_link  = f'<a class="archive-link pdf" href="downloads/{us_pdf_name}">PDF</a>' \
                if us_pdf_name else ""
        else:
            us_html_link = "&mdash;"
            us_pdf_link  = ""
        if d in intl_dates:
            intl_html_link = f'<a class="archive-link" href="intl/{d}/index.html">Read</a>'
            intl_pdf_name  = pdf_map.get(("intl", d))
            intl_pdf_link  = f'<a class="archive-link pdf" href="downloads/{intl_pdf_name}">PDF</a>' \
                if intl_pdf_name else ""
        else:
            intl_html_link = "&mdash;"
            intl_pdf_link  = ""

        archive_rows += f"""
          <tr>
            <td>{display}</td>
            <td>{us_html_link}{us_pdf_link}</td>
            <td>{intl_html_link}{intl_pdf_link}</td>
          </tr>"""

    # Daybreak sub-panel content
    if daybreak_dates and daybreak_ctxs:
        latest_db = daybreak_dates[0]
        db_hero = _render_daybreak_hero(latest_db, daybreak_ctxs[latest_db])
        # Fix link: from landing, brief is at daily/{date}/index.html
        db_archive_rows = ""
        for d in daybreak_dates:
            display = fmt_date(d)
            html_link = f'<a class="archive-link" href="daily/{d}/index.html">Read</a>'
            pdf_name  = pdf_map.get(("daily", d))
            pdf_link  = f'<a class="archive-link pdf" href="downloads/{pdf_name}">PDF</a>' \
                if pdf_name else ""
            db_archive_rows += f"""
              <tr>
                <td>{display}</td>
                <td>{html_link}{pdf_link}</td>
              </tr>"""
        daybreak_sub = f"""
    <div id="sub-daybreak" class="sub-panel">
      <div class="content">
        <div class="section-label">Latest Brief</div>
        <div class="hero-grid" style="grid-template-columns:1fr;">
          {db_hero}
        </div>
        <div class="section-label">Archive</div>
        <table class="archive-table">
          <thead><tr><th>Date</th><th>Daily Brief</th></tr></thead>
          <tbody>{db_archive_rows}</tbody>
        </table>
      </div>
    </div>"""
    else:
        daybreak_sub = '<div id="sub-daybreak" class="sub-panel"><div class="content"><p style="color:var(--muted);font-family:\'Raleway\',sans-serif;font-size:12px;">No daily briefs yet.</p></div></div>'

    # Market IQ and Investing panels
    marketiq_panel = render_market_iq_panel(market_iq_cards)
    investing_panel = render_investing_panel(articles)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Framework Foundry &mdash; Weekly Economic Intelligence</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;1,8..60,300&display=swap" rel="stylesheet"/>
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
        <span class="logo-tagline">Economic Intelligence &nbsp;&middot;&nbsp; Research for the Serious Investor</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

{_SECTION_NAV}

  <!-- ══ PANEL: MARKETS ══ -->
  <div id="panel-markets" class="section-panel active">

    <div class="sub-nav">
      <a class="sub-tab active" data-target="sub-weekly" onclick="showSubNav(this)">Weekly Editions</a>
      <a class="sub-tab" data-target="sub-daybreak" onclick="showSubNav(this)">Market Day Break</a>
    </div>

    <!-- Sub-panel: Weekly Editions -->
    <div id="sub-weekly" class="sub-panel active">
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
    </div><!-- /sub-weekly -->

    <!-- Sub-panel: Market Day Break -->
    {daybreak_sub}

  </div><!-- /panel-markets -->

  <!-- ══ PANEL: MARKET IQ ══ -->
  {marketiq_panel}

  <!-- ══ PANEL: INVESTING ══ -->
  {investing_panel}

  <!-- ══ PANEL: EXPAT ══ -->
  {_EXPAT_PANEL}

  <!-- SUBSCRIBE -->
  <div class="subscribe-section">
    <h2>Stay in the loop</h2>
    <p>Free market intelligence &mdash; weekly editions &amp; daily briefs.</p>
    <form class="subscribe-form" action="https://formspree.io/f/mwpvyoal" method="POST">
      <input type="email" name="email" placeholder="your@email.com" required />
      <button type="submit">Subscribe</button>
    </form>
  </div>

  <!-- SHARE BAR -->
  <div class="share-bar">
    <span class="share-label">Share Framework Foundry</span>
    <div class="share-buttons">
      <a class="share-btn twitter" href="#" target="_blank" rel="noopener"
         onclick="this.href='https://twitter.com/intent/tweet?text='+encodeURIComponent('Framework Foundry \u2014 free weekly US & international market intelligence:  '+window.location.href);return true;"
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

  <footer class="footer">
    <div class="footer-logo">FRAMEWORK <span>FOUNDRY</span></div>
    <div class="footer-disclaimer">
      For informational purposes only. Not investment advice.<br/>
      Past performance is not indicative of future results.
    </div>
  </footer>

</div><!-- /page -->
{_JS}
</body>
</html>"""


# ── Daily hub page ────────────────────────────────────────────────────────────

def render_daily_hub(daybreak_dates, daybreak_ctxs, pdf_map):
    """Render site/daily/index.html — Market Day Break hub."""
    latest = daybreak_dates[0] if daybreak_dates else None

    if latest:
        daily_hero = _render_daybreak_hero(latest, daybreak_ctxs[latest])
        # Patch the CTA link: from daily hub the brief is at ./{date}/index.html
        daily_hero = daily_hero.replace(
            f'href="daily/{latest}/index.html"',
            f'href="{latest}/index.html"'
        )
    else:
        daily_hero = '<div class="hero-card no-issue" style="border-top-color:#c9a84c;">No Daily Brief yet</div>'

    archive_rows = ""
    for d in daybreak_dates:
        display = fmt_date(d)
        html_link = f'<a class="archive-link" href="{d}/index.html">Read</a>'
        pdf_name  = pdf_map.get(("daily", d))
        pdf_link  = f'<a class="archive-link pdf" href="../downloads/{pdf_name}">PDF</a>' \
            if pdf_name else ""
        archive_rows += f"""
          <tr>
            <td>{display}</td>
            <td>{html_link}{pdf_link}</td>
          </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Framework Foundry &mdash; Market Day Break</title>
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
        <span class="logo-tagline">Market Day Break &nbsp;&middot;&nbsp; Daily intelligence at the open</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

{_NAV_TABS_DAILY}

  <div class="content">

    <div class="section-label">Latest Brief</div>
    <div class="hero-grid" style="grid-template-columns:1fr;">
      {daily_hero}
    </div>

    <div class="section-label">Archive</div>
    <table class="archive-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Daily Brief</th>
        </tr>
      </thead>
      <tbody>
        {archive_rows}
      </tbody>
    </table>

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
    <span class="share-label">Share Framework Foundry</span>
    <div class="share-buttons">
      <a class="share-btn twitter" href="#" target="_blank" rel="noopener"
         onclick="this.href='https://twitter.com/intent/tweet?text='+encodeURIComponent('Framework Foundry \u2014 free daily market intelligence:  '+window.location.href);return true;"
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
    pdf_map = {}  # ("us"|"intl"|"daily", date_str) → filename
    us_dates       = find_us_dates()
    intl_dates     = find_intl_dates()
    daybreak_dates = find_daybreak_dates()

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

    for date_str in daybreak_dates:
        src = find_pdf_src(date_str, "daily")
        if src:
            shutil.copy2(src, downloads_dir / src.name)
            pdf_map[("daily", date_str)] = src.name
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

    # Build Daily (Market Day Break) issue pages
    (SITE_DIR / "daily").mkdir(exist_ok=True)
    daybreak_ctxs = {}
    for date_str in daybreak_dates:
        print(f"Building Daily {date_str} …")
        try:
            raw = fetch_daybreak_data(date_str, use_mock=use_mock)
            ctx = build_daybreak_context(raw)
        except Exception as e:
            print(f"  WARNING: could not build daybreak context for {date_str}: {e}")
            continue
        daybreak_ctxs[date_str] = ctx

        issue_dir = SITE_DIR / "daily" / date_str
        issue_dir.mkdir(parents=True, exist_ok=True)
        html = render_daybreak_html(ctx)
        (issue_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  -> site/daily/{date_str}/index.html")

    # Build landing page (4-tab hub)
    market_iq_cards = load_market_iq_cards()
    articles = load_articles()
    landing_html = render_landing(
        us_dates, intl_dates, us_ctxs, intl_ctxs, pdf_map,
        daybreak_dates=daybreak_dates, daybreak_ctxs=daybreak_ctxs,
        market_iq_cards=market_iq_cards, articles=articles,
    )
    (SITE_DIR / "index.html").write_text(landing_html, encoding="utf-8")
    print(f"  -> site/index.html")

    # Build daily hub page
    daily_hub_html = render_daily_hub(daybreak_dates, daybreak_ctxs, pdf_map)
    (SITE_DIR / "daily" / "index.html").write_text(daily_hub_html, encoding="utf-8")
    print(f"  -> site/daily/index.html")

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
