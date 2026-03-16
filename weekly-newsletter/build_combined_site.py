#!/usr/bin/env python3
"""Build the unified static site for Cloudflare Pages deployment.

Run from weekly-newsletter/:
    python build_combined_site.py           # mock data
    python build_combined_site.py --live    # live API data
"""

import argparse
import csv
import json as _json
import markdown
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

  /* SUB-PANELS (within Markets / Market IQ) */
  .sub-panel { display: none; }
  .sub-panel.active { display: block; }

  /* IQ SUB-NAV (inside Market IQ panel) */
  .iq-sub-nav {
    background: var(--off-white);
    border-bottom: 1px solid var(--border);
    padding: 0 40px;
    display: flex;
    gap: 0;
    margin: 0 -40px 28px;
  }

  .iq-sub-tab {
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

  .iq-sub-tab:hover { color: var(--navy); }
  .iq-sub-tab.active { color: var(--accent); border-bottom-color: var(--accent); }

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

  /* IQ GRID FLIP CARDS */
  .iq-card-fullname {
    font-family: 'Source Serif 4', serif;
    font-size: 11px; font-weight: 300; font-style: italic;
    color: var(--accent-lt); margin-top: 4px;
  }

  .iq-card-formula {
    border-left: 3px solid var(--gold);
    padding: 8px 12px; margin-top: 10px;
    font-family: 'Source Serif 4', serif;
    font-size: 11px; line-height: 1.6;
    color: #3a3a4a; font-weight: 300; font-style: italic;
  }

  .iq-grid-flip {
    perspective: 1400px; cursor: pointer;
    border: 1px solid transparent; /* keeps grid cell size stable before JS sets height */
  }

  .iq-grid-flip-inner {
    position: relative; width: 100%;
    transform-style: preserve-3d;
    transition: transform 0.7s cubic-bezier(0.4, 0.2, 0.2, 1);
  }

  .iq-grid-flip.flipped .iq-grid-flip-inner { transform: rotateY(180deg); }

  .iq-grid-flip-front, .iq-grid-flip-back {
    position: absolute; inset: 0;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    display: flex; flex-direction: column;
    background: var(--off-white);
    border: 1px solid var(--border);
  }

  .iq-grid-flip-front { border-top: 4px solid var(--accent); }
  .iq-grid-flip-back  { transform: rotateY(180deg); border-top: 4px solid var(--gold); }

  .iq-grid-flip-front-body { padding: 12px 16px; flex: 1; }

  .iq-grid-flip-front-footer {
    padding: 10px 16px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
  }

  .iq-grid-flip-back-body {
    padding: 14px 16px; flex: 1;
    display: flex; flex-direction: column; gap: 10px;
    overflow: hidden;
  }

  /* Tighter overrides for back inside grid cells */
  .iq-grid-back-header { padding: 12px 16px !important; }
  .iq-grid-back-header .flip-back-title { font-size: 14px; }
  .iq-grid-back-header .flip-back-value { font-size: 22px; }
  .iq-grid-flip-back .stat-tile { padding: 10px 12px; }
  .iq-stat-value { font-size: 20px !important; }
  .iq-grid-flip-back .stat-tile-sub { margin-top: 4px; }
  .iq-grid-flip-back .insight-callout { padding: 10px 12px; }
  .iq-grid-flip-back .insight-callout-text { font-size: 11.5px; line-height: 1.6; }
  .iq-grid-back-footer { padding: 10px 16px !important; }
  .iq-grid-flip-back .mini-bar-chart { height: 52px; gap: 6px; }

  /* Chart label + container inside grid back */
  .iq-chart-label {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 600;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 6px;
  }

  .iq-chart-container {
    background: var(--navy);
    padding: 10px 12px 8px; border-radius: 1px;
  }

  /* Rate timeline (FFR card) */
  .rate-timeline {
    display: flex; align-items: center; gap: 0;
    height: 52px; padding: 0 4px;
  }

  .rate-node {
    display: flex; flex-direction: column;
    align-items: center; flex: 1; position: relative;
  }

  .rate-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent-lt); margin-bottom: 4px; position: relative; z-index: 1;
  }

  .rate-dot.current { background: var(--gold); width: 11px; height: 11px; }

  .rate-connector {
    position: absolute; top: 3px; left: 50%;
    width: 100%; height: 2px;
    background: rgba(255,255,255,0.2); z-index: 0;
  }

  .rate-node:last-child .rate-connector { display: none; }

  .rate-value {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 700;
    color: var(--accent-lt); text-align: center;
  }

  .rate-node.current-node .rate-value { color: var(--gold); }

  .rate-period {
    font-family: 'Raleway', sans-serif;
    font-size: 7px; font-weight: 600;
    letter-spacing: 0.5px; text-transform: uppercase;
    color: rgba(255,255,255,0.4); text-align: center; margin-top: 3px;
  }

  .rate-node.current-node .rate-period { color: rgba(255,255,255,0.65); }

  /* IQ SEARCH BAR */
  .iq-search-row { margin-bottom: 20px; }
  .iq-search-wrapper { position: relative; display: flex; align-items: center; }
  .iq-search-icon {
    position: absolute; left: 13px;
    width: 15px; height: 15px;
    color: var(--muted); pointer-events: none; flex-shrink: 0;
  }
  .iq-search-input {
    width: 100%; box-sizing: border-box;
    font-family: 'Raleway', sans-serif;
    font-size: 12px; font-weight: 400; letter-spacing: 0.5px;
    padding: 11px 40px 11px 38px;
    border: 1px solid var(--border);
    background: var(--white); color: var(--text);
    outline: none; transition: border-color 0.2s;
  }
  .iq-search-input:focus { border-color: var(--accent); }
  .iq-search-input::placeholder { color: var(--muted); font-weight: 300; }
  .iq-search-clear {
    position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
    background: none; border: none; color: var(--muted);
    font-size: 20px; cursor: pointer; line-height: 1; padding: 0 2px; display: none;
  }
  .iq-search-clear.visible { display: block; }
  .iq-no-results {
    display: none;
    font-family: 'Source Serif 4', serif;
    font-size: 14px; font-weight: 300; font-style: italic;
    color: var(--muted); padding: 32px 0; text-align: center;
  }
  .iq-no-results.visible { display: block; }

  /* IQ ALPHA NAV */
  .iq-alpha-row {
    display: flex; flex-wrap: wrap; gap: 4px;
    margin-bottom: 28px; padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }
  .iq-alpha-btn {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
    padding: 5px 8px; border: 1px solid var(--border);
    background: var(--white); color: var(--muted); cursor: default;
  }
  .iq-alpha-btn.has-cards { color: var(--text); cursor: pointer; }
  .iq-alpha-btn.has-cards:hover,
  .iq-alpha-btn.alpha-active {
    background: var(--navy); color: var(--white); border-color: var(--navy);
  }

  /* FEATURED FLIP CARD */
  .featured-card-label {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--accent); margin-bottom: 14px;
  }

  .flip-card {
    perspective: 1400px;
    cursor: pointer;
    width: 100%;
    margin-bottom: 32px;
  }

  .flip-card-inner {
    position: relative;
    width: 100%; height: 620px;
    transform-style: preserve-3d;
    transition: transform 0.7s cubic-bezier(0.4, 0.2, 0.2, 1);
  }

  .flip-card.flipped .flip-card-inner { transform: rotateY(180deg); }

  .flip-card-front, .flip-card-back {
    position: absolute; inset: 0;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    display: flex; flex-direction: column;
  }

  .flip-card-front {
    border: 1px solid var(--border);
    border-top: 4px solid var(--accent);
    background: var(--off-white);
  }

  .flip-card-back {
    transform: rotateY(180deg);
    border: 1px solid var(--border);
    border-top: 4px solid var(--gold);
    background: var(--off-white);
  }

  .flip-front-header {
    background: var(--navy); padding: 32px 36px 28px;
    position: relative; overflow: hidden;
  }

  .flip-front-header::before {
    content: ''; position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
    background-size: 24px 24px;
  }

  .flip-front-header-inner { position: relative; }

  .flip-front-eyebrow {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 600;
    letter-spacing: 2.5px; text-transform: uppercase;
    color: var(--gold); margin-bottom: 8px;
  }

  .flip-front-term {
    font-family: 'Cormorant Garamond', serif;
    font-size: 56px; font-weight: 600;
    color: var(--white); line-height: 1; letter-spacing: 1px;
  }

  .flip-front-fullname {
    font-family: 'Source Serif 4', serif;
    font-size: 14px; font-weight: 300; font-style: italic;
    color: var(--accent-lt); margin-top: 10px;
  }

  .flip-front-body {
    padding: 0 36px; flex: 1; overflow: visible;
    display: flex; flex-direction: column; justify-content: center;
  }

  .flip-front-what-label {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 16px;
  }

  .flip-front-def {
    font-family: 'Source Serif 4', serif;
    font-size: 17px; line-height: 1.8;
    color: var(--text); font-weight: 300; margin-bottom: 32px;
  }

  .flip-front-formula {
    border-left: 3px solid var(--gold);
    padding-left: 20px; margin-bottom: 24px;
    font-family: 'Source Serif 4', serif;
    font-size: 14px; line-height: 1.7;
    color: #3a3a4a; font-weight: 300; font-style: italic;
  }

  .flip-front-context {
    font-family: 'Source Serif 4', serif;
    font-size: 14px; line-height: 1.7;
    color: #3a3a4a; font-weight: 300; margin: 0;
  }

  .flip-front-footer {
    padding: 20px 36px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
  }

  .flip-hint {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 500;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--accent);
  }

  /* BACK */
  .flip-back-header {
    background: var(--navy-mid); padding: 22px 36px;
    position: relative; overflow: hidden;
  }

  .flip-back-header::before {
    content: ''; position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
    background-size: 24px 24px;
  }

  .flip-back-header-inner {
    position: relative;
    display: flex; justify-content: space-between; align-items: center;
  }

  .flip-back-source-label {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 600;
    letter-spacing: 2.5px; text-transform: uppercase;
    color: var(--gold); margin-bottom: 4px;
  }

  .flip-back-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 20px; font-weight: 600; color: var(--white);
  }

  .flip-back-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 32px; font-weight: 300; line-height: 1;
  }

  .flip-back-value-period {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 600;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: rgba(255,255,255,0.4); margin-top: 2px;
    text-align: right;
  }

  .flip-back-body {
    padding: 24px 36px; flex: 1;
    display: flex; flex-direction: column; gap: 20px;
    overflow: visible;
  }

  /* Mini bar chart */
  .mini-bar-chart-wrap {
    background: var(--navy);
    padding: 20px 24px 16px; border-radius: 1px;
  }

  .mini-bar-chart {
    display: flex; align-items: flex-end;
    gap: 10px; height: 88px;
  }

  .mini-bar-col {
    display: flex; flex-direction: column;
    align-items: center; flex: 1;
  }

  .mini-bar-value-label {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 700;
    letter-spacing: 0.5px; margin-bottom: 3px;
  }

  .mini-bar {
    width: 100%; min-height: 4px;
    border-radius: 1px 1px 0 0;
  }

  .mini-bar-period-label {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
    margin-top: 5px;
  }

  /* Stat tiles */
  .stat-tile-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
  }

  .stat-tile {
    border: 1px solid var(--border);
    background: var(--white); padding: 18px 20px;
  }

  .stat-tile-label {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 600;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 10px;
  }

  .stat-tile-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 32px; font-weight: 600; line-height: 1;
  }

  .stat-tile-sub {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 500;
    color: var(--muted); margin-top: 8px;
  }

  /* Insight callout */
  .insight-callout {
    border: 1px solid var(--border);
    border-left: 3px solid var(--gold);
    background: var(--white);
    padding: 18px 20px;
  }

  .insight-callout-label {
    font-family: 'Raleway', sans-serif;
    font-size: 8px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--gold); margin-bottom: 12px;
  }

  .insight-callout-text {
    font-family: 'Source Serif 4', serif;
    font-size: 14px; line-height: 1.75;
    color: #3a3a4a; font-weight: 300; margin: 0;
  }

  .flip-back-footer {
    padding: 18px 36px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
  }

  .flip-back-source {
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--muted);
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

  /* FEEDBACK */
  .feedback-section {
    background: var(--navy); padding: 48px 24px;
    border-top: 1px solid rgba(255,255,255,0.08);
  }
  .feedback-inner {
    max-width: 560px; margin: 0 auto;
  }
  .feedback-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 18px; font-weight: 600; color: var(--white);
    letter-spacing: 0.5px; margin-bottom: 20px;
  }
  .feedback-form { display: flex; flex-direction: column; gap: 12px; }
  .feedback-row  { display: flex; gap: 12px; }
  .feedback-row input { flex: 1; }
  .feedback-form input,
  .feedback-form textarea {
    width: 100%; padding: 10px 14px; border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.08); color: var(--white);
    font-family: 'Raleway', sans-serif; font-size: 13px;
    box-sizing: border-box;
  }
  .feedback-form input::placeholder,
  .feedback-form textarea::placeholder { color: rgba(255,255,255,0.4); }
  .feedback-form textarea { resize: vertical; min-height: 90px; }
  .feedback-form button {
    align-self: flex-start; padding: 10px 28px;
    background: var(--accent); color: var(--white);
    border: none; border-radius: 4px; cursor: pointer;
    font-family: 'Raleway', sans-serif; font-size: 12px;
    font-weight: 600; letter-spacing: 1px; text-transform: uppercase;
  }
  .feedback-form button:hover { background: var(--accent-lt); }

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


# ── Market IQ live data (FRED) ────────────────────────────────────────────────

def _iq_fred_key():
    """Load FRED API key from env or config file."""
    key = __import__("os").environ.get("FRED_API_KEY", "")
    if not key:
        env_path = BASE_DIR / "config" / "api_keys.env"
        try:
            for line in env_path.read_text().splitlines():
                if line.strip().startswith("FRED_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip()
                    break
        except Exception:
            pass
    return key


def _fred_obs(series_id, units="lin", limit=6, frequency=None, agg_method=None):
    """Fetch FRED observations. Returns list of (date_str, float) newest-first."""
    try:
        import requests
    except ImportError:
        return []
    key = _iq_fred_key()
    if not key:
        return []
    params = {"series_id": series_id, "api_key": key, "file_type": "json",
              "sort_order": "desc", "limit": limit, "units": units}
    if frequency:
        params["frequency"] = frequency
    if agg_method:
        params["aggregation_method"] = agg_method
    try:
        r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                         params=params, timeout=10)
        r.raise_for_status()
        out = []
        for o in r.json().get("observations", []):
            if o["value"] not in (".", ""):
                try:
                    out.append((o["date"], float(o["value"])))
                except ValueError:
                    pass
        return out
    except Exception as e:
        print(f"  FRED {series_id}: {e}")
        return []


def _iq_mlabel(date_str):
    """'2026-01-01' → \"Jan '26\"."""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%b '%y")
    except ValueError:
        return date_str


def _iq_qlabel(date_str):
    """'2025-10-01' → \"Q4 '25\"."""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        q = (dt.month - 1) // 3 + 1
        return f"Q{q} '{dt.strftime('%y')}"
    except ValueError:
        return date_str


def _yf_monthly(ticker_sym, limit=5):
    """Fetch last N monthly closes via yfinance. Returns [(date_str, float), ...] newest-first."""
    try:
        import yfinance as yf
        from datetime import timedelta
        end = datetime.today()
        start = end - timedelta(days=limit * 40)
        df = yf.download(ticker_sym, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"), interval="1mo",
                         progress=False, auto_adjust=True)
        if df.empty:
            return []
        close_col = df["Close"]
        # yfinance >=0.2 may return DataFrame with ticker as column
        if hasattr(close_col, "squeeze"):
            close_col = close_col.squeeze()
        closes = close_col.dropna()
        result = []
        for idx, v in closes.items():
            date_str = str(idx)[:10]
            val = float(v) if not hasattr(v, '__len__') else float(v.iloc[0])
            result.append((date_str[:7] + "-01", val))
        return list(reversed(result[-limit:]))
    except Exception as e:
        print(f"  yfinance {ticker_sym}: {e}")
        return []


def fetch_live_iq_data():
    """Pull live FRED data for all Market IQ cards.

    Returns a dict keyed by card term with field overrides.
    Results are cached in fixtures/market_iq_YYYY-MM-DD.json so subsequent
    builds on the same day skip the API calls.
    """
    today = datetime.today().strftime("%Y-%m-%d")
    fixture_path = BASE_DIR / "fixtures" / f"market_iq_{today}.json"
    if fixture_path.exists():
        try:
            return _json.loads(fixture_path.read_text())
        except Exception:
            pass

    data = {}
    print("Fetching live Market IQ data from FRED...")

    # CPI — CPIAUCNS YoY (NSA), CPILFESL core YoY
    cpi = _fred_obs("CPIAUCNS", units="pc1", limit=5)
    core_cpi = _fred_obs("CPILFESL", units="pc1", limit=2)
    if cpi:
        cur_d, cur_v = cpi[0]
        core_v = core_cpi[0][1] if core_cpi else None
        pts = list(reversed(cpi[:4]))
        data["CPI"] = {
            "current_value": f"{cur_v:.1f}%",
            "current_value_period": f"YoY \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 2.5 else "green",
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1)} for d, v in pts]),
            "stat1_value": f"{core_v:.1f}%" if core_v is not None else "\u2014",
            "trend": "up" if cur_v > 3.0 else ("flat" if cur_v >= 2.0 else "down"),
            "trend_label": "\u2191 Elevated" if cur_v > 3.0 else ("\u2192 Moderating" if cur_v >= 2.0 else "\u2193 Near Target"),
            "source": f"U.S. Bureau of Labor Statistics \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Fed Funds Rate — DFEDTARU/DFEDTARL (monthly end-of-period)
    ffr_u = _fred_obs("DFEDTARU", units="lin", limit=5, frequency="m", agg_method="eop")
    ffr_l = _fred_obs("DFEDTARL", units="lin", limit=5, frequency="m", agg_method="eop")
    if ffr_u and ffr_l:
        cur_d, upper_v = ffr_u[0]
        lower_v = ffr_l[0][1]
        u_map = {d: v for d, v in ffr_u[:4]}
        l_map = {d: v for d, v in ffr_l[:4]}
        common = sorted(set(u_map) & set(l_map))  # oldest → newest
        timeline = [{"rate": f"{l_map[d]:.2f}\u2013{u_map[d]:.2f}%", "label": _iq_mlabel(d)}
                    for d in common]
        data["Fed Funds Rate"] = {
            "current_value": f"{lower_v:.2f}\u2013{upper_v:.2f}%",
            "current_value_period": f"Target \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "gray",
            "chart_data": _json.dumps(timeline),
            "trend": "flat",
            "trend_label": "\u2192 Hold",
            "source": f"Federal Reserve \u00b7 {_iq_mlabel(cur_d)} FOMC",
        }

    # NFP — PAYEMS level → MoM diff; UNRATE; avg hourly earnings YoY
    payems = _fred_obs("PAYEMS", units="lin", limit=6)
    unrate = _fred_obs("UNRATE", units="lin", limit=2)
    ahe = _fred_obs("CES0500000003", units="pc1", limit=2)
    if payems and len(payems) >= 2:
        diffs = [(payems[i][0], payems[i][1] - payems[i + 1][1]) for i in range(len(payems) - 1)]
        cur_d, cur_v = diffs[0]
        pts = list(reversed(diffs[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["Non-Farm Payrolls"] = {
            "current_value": f"{pfx}{int(cur_v)}K",
            "current_value_period": _iq_mlabel(cur_d),
            "current_value_color": "green" if cur_v > 200 else ("red" if cur_v < 75 else "gray"),
            "chart_data": _json.dumps([
                {"label": _iq_mlabel(d), "value": round(v), "displayValue": f"{int(v)}K"} for d, v in pts
            ]),
            "stat1_value": f"{unrate[0][1]:.1f}%" if unrate else "\u2014",
            "stat2_value": f"+{ahe[0][1]:.1f}%" if ahe else "\u2014",
            "trend": "up" if cur_v > 200 else ("down" if cur_v < 100 else "flat"),
            "trend_label": "\u2191 Strong" if cur_v > 200 else ("\u2193 Softening" if cur_v < 100 else "\u2192 Steady"),
            "source": f"U.S. Bureau of Labor Statistics \u00b7 {_iq_mlabel(cur_d)}",
        }

    # PCE — PCEPILFE core YoY, PCEPI headline YoY
    core_pce = _fred_obs("PCEPILFE", units="pc1", limit=5)
    hdl_pce = _fred_obs("PCEPI", units="pc1", limit=2)
    if core_pce:
        cur_d, cur_v = core_pce[0]
        pts = list(reversed(core_pce[:4]))
        hdl_v = hdl_pce[0][1] if hdl_pce else None
        data["PCE"] = {
            "current_value": f"{cur_v:.1f}%",
            "current_value_period": f"Core YoY \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 2.5 else "green",
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1)} for d, v in pts]),
            "stat1_value": f"{hdl_v:.1f}%" if hdl_v is not None else "\u2014",
            "trend": "up" if cur_v > 3.0 else ("flat" if cur_v >= 2.0 else "down"),
            "trend_label": "\u2191 Above Target" if cur_v > 2.5 else ("\u2192 Moderating" if cur_v >= 2.0 else "\u2193 Near Target"),
            "source": f"U.S. Bureau of Economic Analysis \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Yield Curve — GS10 minus GS2 (monthly)
    gs10 = _fred_obs("GS10", units="lin", limit=5)
    gs2 = _fred_obs("GS2", units="lin", limit=5)
    if gs10 and gs2:
        g10 = {d: v for d, v in gs10}
        g2 = {d: v for d, v in gs2}
        common = sorted(set(g10) & set(g2), reverse=True)
        spreads = [(d, round(g10[d] - g2[d], 2)) for d in common[:5]]
        cur_d, cur_v = spreads[0]
        pts = list(reversed(spreads[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["Yield Curve"] = {
            "current_value": f"{pfx}{cur_v:.2f}%",
            "current_value_period": _iq_mlabel(cur_d),
            "current_value_color": "green" if cur_v >= 0 else "red",
            "chart_data": _json.dumps([
                {"label": _iq_mlabel(d), "value": v,
                 "displayValue": f"+{v:.2f}%" if v >= 0 else f"{v:.2f}%"} for d, v in pts
            ]),
            "stat1_value": f"{g10[common[0]]:.2f}%",
            "stat2_value": f"{g2[common[0]]:.2f}%",
            "trend": "flat" if -0.1 <= cur_v <= 0.3 else ("up" if cur_v > 0.3 else "down"),
            "trend_label": "\u2192 Normalizing" if cur_v >= 0 else "\u2193 Inverted",
            "source": f"U.S. Treasury / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # GDP — A191RL1Q225SBEA (quarterly real growth, annualized)
    gdp = _fred_obs("A191RL1Q225SBEA", units="lin", limit=5)
    if gdp:
        cur_d, cur_v = gdp[0]
        pts = list(reversed(gdp[:4]))
        annual_avg = round(sum(v for _, v in gdp[:4]) / min(4, len(gdp)), 1)
        data["GDP"] = {
            "current_value": f"{cur_v:.1f}%",
            "current_value_period": f"{_iq_qlabel(cur_d)} (Annualized)",
            "current_value_color": "red" if cur_v < 2.0 else "green",
            "chart_data": _json.dumps([{"label": _iq_qlabel(d), "value": round(v, 1)} for d, v in pts]),
            "stat1_value": f"{annual_avg:.1f}%",
            "trend": "up" if cur_v > 3.0 else ("down" if cur_v < 1.5 else "flat"),
            "trend_label": "\u2191 Strong" if cur_v > 3.0 else ("\u2193 Slowing" if cur_v < 2.0 else "\u2192 Steady"),
            "source": f"U.S. Bureau of Economic Analysis \u00b7 {_iq_qlabel(cur_d)}",
        }

    # PPI — PPIACO YoY
    ppi = _fred_obs("PPIACO", units="pc1", limit=5)
    if ppi:
        cur_d, cur_v = ppi[0]
        pts = list(reversed(ppi[:4]))
        data["PPI"] = {
            "current_value": f"{cur_v:.1f}%",
            "current_value_period": f"YoY \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 3.0 else ("green" if cur_v < 1.5 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1)} for d, v in pts]),
            "trend": "up" if cur_v > 3.0 else ("down" if cur_v < 1.5 else "flat"),
            "trend_label": "\u2191 Elevated" if cur_v > 3.0 else ("\u2193 Cooling" if cur_v < 1.5 else "\u2192 Moderate"),
            "source": f"U.S. Bureau of Labor Statistics \u00b7 {_iq_mlabel(cur_d)}",
        }

    # VIX — VIXCLS (daily → monthly avg)
    vix = _fred_obs("VIXCLS", units="lin", limit=5, frequency="m", agg_method="avg")
    if vix:
        cur_d, cur_v = vix[0]
        pts = list(reversed(vix[:4]))
        data["VIX"] = {
            "current_value": f"{cur_v:.1f}",
            "current_value_period": f"Monthly Avg \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 25 else ("green" if cur_v < 15 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"{v:.1f}"} for d, v in pts]),
            "trend": "up" if cur_v > 25 else ("down" if cur_v < 15 else "flat"),
            "trend_label": "\u2191 Elevated" if cur_v > 25 else ("\u2193 Low" if cur_v < 15 else "\u2192 Moderate"),
            "source": f"CBOE / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # DXY — DTWEXBGS (Broad USD Index, monthly avg)
    dxy = _fred_obs("DTWEXBGS", units="lin", limit=5, frequency="m", agg_method="avg")
    if dxy:
        cur_d, cur_v = dxy[0]
        pts = list(reversed(dxy[:4]))
        data["DXY"] = {
            "current_value": f"{cur_v:.1f}",
            "current_value_period": f"Broad Index \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "green" if cur_v > 105 else ("red" if cur_v < 95 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"{v:.1f}"} for d, v in pts]),
            "trend": "up" if cur_v > pts[-1][1] * 1.01 else ("down" if cur_v < pts[0][1] * 0.99 else "flat"),
            "trend_label": "\u2191 Strengthening" if cur_v > 105 else ("\u2193 Weakening" if cur_v < 95 else "\u2192 Stable"),
            "source": f"Federal Reserve / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # JOLTS — JTSJOL (job openings, thousands → display as millions)
    jolts = _fred_obs("JTSJOL", units="lin", limit=5)
    if jolts:
        cur_d, cur_v = jolts[0]
        cur_m = cur_v / 1000.0
        pts = list(reversed(jolts[:4]))
        data["JOLTS"] = {
            "current_value": f"{cur_m:.1f}M",
            "current_value_period": _iq_mlabel(cur_d),
            "current_value_color": "green" if cur_m > 8.0 else ("red" if cur_m < 7.0 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v / 1000, 1), "displayValue": f"{v/1000:.1f}M"} for d, v in pts]),
            "trend": "up" if cur_m > 8.5 else ("down" if cur_m < 7.5 else "flat"),
            "trend_label": "\u2191 Hot" if cur_m > 8.5 else ("\u2193 Cooling" if cur_m < 7.5 else "\u2192 Steady"),
            "source": f"U.S. Bureau of Labor Statistics \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Initial Claims — ICSA (weekly, in thousands)
    claims = _fred_obs("ICSA", units="lin", limit=5)
    if claims:
        cur_d, cur_v = claims[0]
        pts = list(reversed(claims[:4]))
        data["Claims"] = {
            "current_value": f"{int(cur_v):,}",
            "current_value_period": f"Week of {cur_d[:10]}",
            "current_value_color": "green" if cur_v < 225 else ("red" if cur_v > 275 else "gray"),
            "chart_data": _json.dumps([{"label": d[:10][5:], "value": int(v), "displayValue": f"{int(v):,}"} for d, v in pts]),
            "trend": "up" if cur_v > 275 else ("down" if cur_v < 200 else "flat"),
            "trend_label": "\u2191 Rising" if cur_v > 275 else ("\u2193 Low" if cur_v < 200 else "\u2192 Stable"),
            "source": f"U.S. Department of Labor \u00b7 {cur_d[:10]}",
        }

    # Retail Sales MoM — RSAFS (pch = month-over-month %)
    retail = _fred_obs("RSAFS", units="pch", limit=5)
    if retail:
        cur_d, cur_v = retail[0]
        pts = list(reversed(retail[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["Retail Sales"] = {
            "current_value": f"{pfx}{cur_v:.1f}%",
            "current_value_period": f"MoM \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "green" if cur_v > 0.5 else ("red" if cur_v < -0.5 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 0.5 else ("down" if cur_v < -0.3 else "flat"),
            "trend_label": "\u2191 Solid" if cur_v > 0.5 else ("\u2193 Weak" if cur_v < -0.3 else "\u2192 Mixed"),
            "source": f"U.S. Census Bureau \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Housing Starts — HOUST (thousands, annual rate)
    houst = _fred_obs("HOUST", units="lin", limit=5)
    if houst:
        cur_d, cur_v = houst[0]
        cur_m = cur_v / 1000.0
        pts = list(reversed(houst[:4]))
        data["Housing Starts"] = {
            "current_value": f"{cur_m:.2f}M",
            "current_value_period": f"Ann. Rate \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "green" if cur_m > 1.4 else ("red" if cur_m < 1.2 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v / 1000, 2), "displayValue": f"{v/1000:.2f}M"} for d, v in pts]),
            "trend": "up" if cur_m > 1.4 else ("down" if cur_m < 1.2 else "flat"),
            "trend_label": "\u2191 Recovering" if cur_m > 1.4 else ("\u2193 Subdued" if cur_m < 1.2 else "\u2192 Steady"),
            "source": f"U.S. Census Bureau \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Credit Spreads — BAMLH0A0HYM2 (HY OAS, bps → already in bps, monthly avg)
    hy_oas = _fred_obs("BAMLH0A0HYM2", units="lin", limit=5, frequency="m", agg_method="avg")
    if hy_oas:
        cur_d, cur_v = hy_oas[0]
        pts = list(reversed(hy_oas[:4]))
        data["Credit Spreads"] = {
            "current_value": f"{int(cur_v)} bps",
            "current_value_period": f"HY OAS \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 400 else ("green" if cur_v < 300 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": int(v), "displayValue": str(int(v))} for d, v in pts]),
            "trend": "up" if cur_v > 400 else ("down" if cur_v < 300 else "flat"),
            "trend_label": "\u2191 Stressed" if cur_v > 400 else ("\u2193 Tight" if cur_v < 300 else "\u2192 Normal"),
            "source": f"ICE BofA / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Real Rate — DFII10 (10-Year TIPS yield, monthly avg)
    dfii10 = _fred_obs("DFII10", units="lin", limit=5, frequency="m", agg_method="avg")
    if dfii10:
        cur_d, cur_v = dfii10[0]
        data["Real Rate"] = {
            "current_value": f"{cur_v:.2f}%",
            "current_value_period": f"10Y TIPS \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 2.0 else ("green" if cur_v < 0.5 else "gray"),
            "stat1_value": f"{cur_v:.2f}%",
            "trend": "up" if cur_v > 2.0 else ("down" if cur_v < 0.5 else "flat"),
            "trend_label": "\u2191 Restrictive" if cur_v > 2.0 else ("\u2193 Easing" if cur_v < 0.5 else "\u2192 Neutral"),
            "source": f"U.S. Treasury / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Michigan Sentiment — UMCSENT (monthly)
    umcs = _fred_obs("UMCSENT", units="lin", limit=5)
    if umcs:
        cur_d, cur_v = umcs[0]
        pts = list(reversed(umcs[:4]))
        data["Michigan Sentiment"] = {
            "current_value": f"{cur_v:.1f}",
            "current_value_period": _iq_mlabel(cur_d),
            "current_value_color": "green" if cur_v > 75 else ("red" if cur_v < 65 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"{v:.1f}"} for d, v in pts]),
            "trend": "up" if cur_v > 75 else ("down" if cur_v < 65 else "flat"),
            "trend_label": "\u2191 Confident" if cur_v > 75 else ("\u2193 Pessimistic" if cur_v < 65 else "\u2192 Cautious"),
            "source": f"University of Michigan \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Industrial Production MoM — INDPRO (pch)
    indpro = _fred_obs("INDPRO", units="pch", limit=5)
    if indpro:
        cur_d, cur_v = indpro[0]
        pts = list(reversed(indpro[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["Industrial Production"] = {
            "current_value": f"{pfx}{cur_v:.1f}%",
            "current_value_period": f"MoM \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "green" if cur_v > 0.3 else ("red" if cur_v < -0.3 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 0.3 else ("down" if cur_v < -0.3 else "flat"),
            "trend_label": "\u2191 Expanding" if cur_v > 0.3 else ("\u2193 Contracting" if cur_v < -0.3 else "\u2192 Flat"),
            "source": f"Federal Reserve \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Durable Goods Orders MoM — DGORDER (pch)
    dgo = _fred_obs("DGORDER", units="pch", limit=5)
    if dgo:
        cur_d, cur_v = dgo[0]
        pts = list(reversed(dgo[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["Durable Goods"] = {
            "current_value": f"{pfx}{cur_v:.1f}%",
            "current_value_period": f"MoM \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "green" if cur_v > 1.0 else ("red" if cur_v < -1.0 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 1.0 else ("down" if cur_v < -1.0 else "flat"),
            "trend_label": "\u2191 Growing" if cur_v > 1.0 else ("\u2193 Declining" if cur_v < -1.0 else "\u2192 Mixed"),
            "source": f"U.S. Census Bureau \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Breakeven Inflation — T10YIE (10-Year, daily → monthly avg)
    t10yie = _fred_obs("T10YIE", units="lin", limit=5, frequency="m", agg_method="avg")
    if t10yie:
        cur_d, cur_v = t10yie[0]
        pts = list(reversed(t10yie[:4]))
        data["Breakeven Inflation"] = {
            "current_value": f"{cur_v:.2f}%",
            "current_value_period": f"10Y Breakeven \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 2.5 else ("green" if cur_v < 1.8 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 2)} for d, v in pts]),
            "trend": "up" if cur_v > 2.5 else ("down" if cur_v < 1.8 else "flat"),
            "trend_label": "\u2191 Elevated" if cur_v > 2.5 else ("\u2193 Anchored" if cur_v < 1.8 else "\u2192 Stable"),
            "source": f"Federal Reserve / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Import Prices MoM — IR (pch)
    imp = _fred_obs("IR", units="pch", limit=5)
    if imp:
        cur_d, cur_v = imp[0]
        pts = list(reversed(imp[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["Import Prices"] = {
            "current_value": f"{pfx}{cur_v:.1f}%",
            "current_value_period": f"MoM \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 0.5 else ("green" if cur_v < -0.2 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 0.5 else ("down" if cur_v < -0.2 else "flat"),
            "trend_label": "\u2191 Rising" if cur_v > 0.5 else ("\u2193 Falling" if cur_v < -0.2 else "\u2192 Stable"),
            "source": f"U.S. Bureau of Labor Statistics \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Income & Spending — personal spending MoM (PCE level in pch)
    pce_spend = _fred_obs("PCE", units="pch", limit=5)
    if pce_spend:
        cur_d, cur_v = pce_spend[0]
        pts = list(reversed(pce_spend[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["Income & Spending"] = {
            "current_value": f"{pfx}{cur_v:.1f}%",
            "current_value_period": f"Spending MoM \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "green" if cur_v > 0.4 else ("red" if cur_v < 0 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 0.4 else ("down" if cur_v < 0 else "flat"),
            "trend_label": "\u2191 Strong" if cur_v > 0.4 else ("\u2193 Weak" if cur_v < 0 else "\u2192 Moderate"),
            "source": f"U.S. Bureau of Economic Analysis \u00b7 {_iq_mlabel(cur_d)}",
        }

    # U-6 Unemployment — U6RATE (monthly)
    u6 = _fred_obs("U6RATE", units="lin", limit=5)
    if u6:
        cur_d, cur_v = u6[0]
        pts = list(reversed(u6[:4]))
        data["U-6"] = {
            "current_value": f"{cur_v:.1f}%",
            "current_value_period": _iq_mlabel(cur_d),
            "current_value_color": "red" if cur_v > 8.5 else ("green" if cur_v < 7.5 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 8.5 else ("down" if cur_v < 7.0 else "flat"),
            "trend_label": "\u2191 Rising" if cur_v > 8.5 else ("\u2193 Low" if cur_v < 7.0 else "\u2192 Stable"),
            "source": f"U.S. Bureau of Labor Statistics \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Labor Force Participation Rate — CIVPART (monthly)
    lfpr = _fred_obs("CIVPART", units="lin", limit=5)
    if lfpr:
        cur_d, cur_v = lfpr[0]
        pts = list(reversed(lfpr[:4]))
        data["LFPR"] = {
            "current_value": f"{cur_v:.1f}%",
            "current_value_period": _iq_mlabel(cur_d),
            "current_value_color": "green" if cur_v > 63.0 else ("red" if cur_v < 62.0 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 63.3 else ("down" if cur_v < 62.3 else "flat"),
            "trend_label": "\u2191 Rising" if cur_v > 63.3 else ("\u2193 Declining" if cur_v < 62.3 else "\u2192 Stable"),
            "source": f"U.S. Bureau of Labor Statistics \u00b7 {_iq_mlabel(cur_d)}",
        }

    # QT (Fed Balance Sheet) — WALCL (weekly total assets, millions → trillions)
    walcl = _fred_obs("WALCL", units="lin", limit=5, frequency="m", agg_method="eop")
    if walcl:
        cur_d, cur_v = walcl[0]
        cur_t = cur_v / 1_000_000.0
        pts = list(reversed(walcl[:4]))
        data["QT"] = {
            "current_value": f"${cur_t:.2f}T",
            "current_value_period": f"Total Assets \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_t > 8.0 else ("green" if cur_t < 7.0 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v / 1_000_000, 2), "displayValue": f"${v/1_000_000:.2f}T"} for d, v in pts]),
            "trend": "down" if cur_t < pts[0][1] / 1_000_000 else "flat",
            "trend_label": "\u2193 Shrinking" if cur_t < 7.5 else "\u2192 Stable",
            "source": f"Federal Reserve / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # M2 Money Supply YoY — M2SL (pc1)
    m2 = _fred_obs("M2SL", units="pc1", limit=5)
    if m2:
        cur_d, cur_v = m2[0]
        pts = list(reversed(m2[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["M2"] = {
            "current_value": f"{pfx}{cur_v:.1f}%",
            "current_value_period": f"YoY \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 5.0 else ("green" if cur_v < 2.0 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 5.0 else ("down" if cur_v < 0 else "flat"),
            "trend_label": "\u2191 Expanding" if cur_v > 5.0 else ("\u2193 Contracting" if cur_v < 0 else "\u2192 Moderate"),
            "source": f"Federal Reserve / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # SLOOS — DRTSCILM (% banks tightening C&I standards, large firms, quarterly)
    sloos = _fred_obs("DRTSCILM", units="lin", limit=5)
    if sloos:
        cur_d, cur_v = sloos[0]
        pts = list(reversed(sloos[:4]))
        pfx = "+" if cur_v >= 0 else ""
        data["SLOOS"] = {
            "current_value": f"{pfx}{cur_v:.1f}%",
            "current_value_period": f"Net Tightening \u00b7 {_iq_qlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 20 else ("green" if cur_v < 0 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_qlabel(d), "value": round(v, 1), "displayValue": f"{v:.1f}%"} for d, v in pts]),
            "trend": "up" if cur_v > 20 else ("down" if cur_v < 0 else "flat"),
            "trend_label": "\u2191 Tightening" if cur_v > 20 else ("\u2193 Easing" if cur_v < 0 else "\u2192 Neutral"),
            "source": f"Federal Reserve / FRED \u00b7 {_iq_qlabel(cur_d)}",
        }

    # Gold — GC=F via yfinance (monthly close)
    gold = _yf_monthly("GC=F", limit=5)
    if gold:
        cur_d, cur_v = gold[0]
        pts = list(reversed(gold[:4]))
        data["Gold"] = {
            "current_value": f"${cur_v:,.0f}",
            "current_value_period": f"USD/oz \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "green" if cur_v > pts[0][1] else "red",
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": int(v), "displayValue": f"${v:,.0f}"} for d, v in pts]),
            "trend": "up" if cur_v > 4000 else ("down" if cur_v < 2500 else "flat"),
            "trend_label": "\u2191 Rising" if cur_v > 4000 else ("\u2193 Falling" if cur_v < 2500 else "\u2192 Stable"),
            "source": f"COMEX / yfinance \u00b7 {_iq_mlabel(cur_d)}",
        }

    # WTI Crude Oil — DCOILWTICO (daily → monthly avg), fallback to yfinance CL=F
    wti = _fred_obs("DCOILWTICO", units="lin", limit=5, frequency="m", agg_method="avg")
    if not wti:
        wti = _yf_monthly("CL=F", limit=5)
    if wti:
        cur_d, cur_v = wti[0]
        pts = list(reversed(wti[:4]))
        data["WTI"] = {
            "current_value": f"${cur_v:.1f}",
            "current_value_period": f"USD/bbl \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 85 else ("green" if cur_v < 65 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 1), "displayValue": f"${v:.1f}"} for d, v in pts]),
            "trend": "up" if cur_v > 85 else ("down" if cur_v < 65 else "flat"),
            "trend_label": "\u2191 High" if cur_v > 85 else ("\u2193 Low" if cur_v < 65 else "\u2192 Moderate"),
            "source": f"EIA / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Trade Balance — BOPGSTB (millions → billions)
    trade = _fred_obs("BOPGSTB", units="lin", limit=5)
    if trade:
        cur_d, cur_v = trade[0]
        cur_b = cur_v / 1000.0
        pts = list(reversed(trade[:4]))
        data["Trade Balance"] = {
            "current_value": f"${cur_b:,.0f}B",
            "current_value_period": _iq_mlabel(cur_d),
            "current_value_color": "red" if cur_b < -100 else ("green" if cur_b > -50 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v / 1000, 1), "displayValue": f"${v/1000:,.0f}B"} for d, v in pts]),
            "trend": "down" if cur_b < -100 else ("up" if cur_b > -50 else "flat"),
            "trend_label": "\u2193 Widening" if cur_b < -100 else ("\u2191 Narrowing" if cur_b > -50 else "\u2192 Stable"),
            "source": f"U.S. Bureau of Economic Analysis \u00b7 {_iq_mlabel(cur_d)}",
        }

    # USD/CNY — DEXCHUS (CNY per USD, daily → monthly avg)
    usdcny = _fred_obs("DEXCHUS", units="lin", limit=5, frequency="m", agg_method="avg")
    if usdcny:
        cur_d, cur_v = usdcny[0]
        pts = list(reversed(usdcny[:4]))
        data["USD/CNY"] = {
            "current_value": f"{cur_v:.2f}",
            "current_value_period": f"CNY per USD \u00b7 {_iq_mlabel(cur_d)}",
            "current_value_color": "red" if cur_v > 7.3 else ("green" if cur_v < 7.1 else "gray"),
            "chart_data": _json.dumps([{"label": _iq_mlabel(d), "value": round(v, 2), "displayValue": f"{v:.2f}"} for d, v in pts]),
            "trend": "up" if cur_v > 7.3 else ("down" if cur_v < 7.1 else "flat"),
            "trend_label": "\u2191 Weakening CNY" if cur_v > 7.3 else ("\u2193 Strengthening CNY" if cur_v < 7.1 else "\u2192 Stable"),
            "source": f"Federal Reserve / FRED \u00b7 {_iq_mlabel(cur_d)}",
        }

    # Cache to fixture
    if data:
        try:
            (BASE_DIR / "fixtures").mkdir(exist_ok=True)
            fixture_path.write_text(_json.dumps(data, indent=2))
            print(f"  Saved Market IQ fixture: {fixture_path.name}")
        except Exception as e:
            print(f"  Warning: could not save fixture: {e}")

    return data


def load_market_iq_cards(csv_path=None):
    """Load Market IQ flashcard data from CSV, enriched with live FRED data."""
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

    # Merge live FRED data (graceful fallback to CSV values if unavailable)
    try:
        live = fetch_live_iq_data()
        for card in cards:
            overrides = live.get(card.get("term", ""), {})
            if overrides:
                card.update(overrides)
                card["trend_class"] = _TREND_CLASS.get(card.get("trend", "flat"), "trend-flat")
    except Exception as e:
        print(f"Warning: live Market IQ data unavailable — {e}")

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


def parse_fundaa_articles(articles_dir=None):
    """Parse Friday Fundaa articles from content/articles/friday-fundaa-*.md.

    Returns a list of dicts (newest first):
      {title, slug, date, display_date, body_html, excerpt}
    """
    if articles_dir is None:
        articles_dir = BASE_DIR / "content" / "articles"
    articles = []
    try:
        for md_file in sorted(Path(articles_dir).glob("friday-fundaa-*.md")):
            text = md_file.read_text(encoding="utf-8")
            lines = text.splitlines()

            # Title: first non-empty line matching "# Friday Fundaa — …"
            title = ""
            for line in lines:
                m = re.match(r'^#\s+Friday Fundaa\s+[—–-]+\s*(.+)', line)
                if m:
                    title = m.group(1).strip()
                    break

            # Date + slug: italic line "*Topic: Slug | Date: YYYY-MM-DD …*"
            slug = ""
            date_str = ""
            for line in lines:
                m = re.match(r'^\*Topic:\s*([^|]+)\|\s*Date:\s*(\d{4}-\d{2}-\d{2})', line)
                if m:
                    slug = m.group(1).strip().lower().replace(" ", "-")
                    date_str = m.group(2).strip()
                    break

            if not title or not date_str:
                continue

            # Substack body: between "## Substack" and next "## " or EOF
            body_lines = []
            in_substack = False
            for line in lines:
                if re.match(r'^##\s+Substack', line):
                    in_substack = True
                    continue
                if in_substack:
                    if re.match(r'^##\s+', line):
                        break
                    body_lines.append(line)
            body_md = "\n".join(body_lines).strip()
            body_html = markdown.markdown(body_md)

            # Excerpt: first non-empty non-heading paragraph
            excerpt = ""
            for line in body_lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and not stripped.startswith("**Friday Fundaa"):
                    excerpt = stripped[:160]
                    if len(stripped) > 160:
                        excerpt += "…"
                    break

            try:
                d = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = f"{d.strftime('%b')} {d.day}, {d.year}"
            except ValueError:
                display_date = date_str

            articles.append({
                "title": title,
                "slug": slug,
                "date": date_str,
                "display_date": display_date,
                "body_html": body_html,
                "excerpt": excerpt,
            })
    except (FileNotFoundError, OSError):
        pass

    today = datetime.utcnow().strftime("%Y-%m-%d")
    articles = [a for a in articles if a["date"] <= today]
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


_HEADER_LINK_CSS = """\
    .header-home-link {
      position: absolute; inset: 0; z-index: 1;
      display: block; cursor: pointer;
    }
    .header-inner, .header-meta, .header-accent { position: relative; z-index: 2; }
"""

_BREADCRUMB_CSS = """\
    .breadcrumb {
      font-family: 'Raleway', sans-serif;
      font-size: 10px; font-weight: 500; letter-spacing: 1px;
      color: var(--muted); margin-bottom: 28px; padding-top: 4px;
    }
    .breadcrumb a { color: var(--accent); text-decoration: none; }
    .breadcrumb a:hover { text-decoration: underline; }
    .breadcrumb .sep { margin: 0 8px; color: var(--border); }
"""


def _make_breadcrumb_nav(crumbs):
    """Build a <nav class="breadcrumb"> element.

    crumbs: list of (label, url_or_None) — last item is always plain text.
    """
    parts = []
    for i, (label, url) in enumerate(crumbs):
        if url:
            parts.append(f'<a href="{url}">{label}</a>')
        else:
            parts.append(f'<span>{label}</span>')
        if i < len(crumbs) - 1:
            parts.append('<span class="sep">/</span>')
    inner = "\n      ".join(parts)
    return f'    <nav class="breadcrumb">\n      {inner}\n    </nav>'


def inject_breadcrumb(html, crumbs):
    """Post-process rendered HTML: inject breadcrumb CSS + nav into a page.

    Inserts CSS before </style> (first occurrence) and nav as the first
    child of <div class="content">.
    """
    nav = _make_breadcrumb_nav(crumbs)
    html = html.replace("</style>", _BREADCRUMB_CSS + "  </style>", 1)
    html = html.replace('<div class="content">', '<div class="content">\n' + nav, 1)
    return html


def inject_header_link(html, home_url):
    """Post-process rendered HTML: make the header banner link to home.

    Injects an invisible full-bleed anchor overlay inside <header class="header">
    so clicking anywhere on the banner navigates to home_url.
    """
    html = html.replace("</style>", _HEADER_LINK_CSS + "  </style>", 1)
    html = html.replace(
        '<header class="header">',
        f'<header class="header"><a href="{home_url}" class="header-home-link" aria-label="Go to Framework Foundry home"></a>',
        1,
    )
    return html


def render_fundaa_article_page(article):
    """Render a standalone HTML page for a Friday Fundaa article."""
    title = article["title"]
    display_date = article["display_date"]
    body_html = article["body_html"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Friday Fundaa — {title} | Framework Foundry</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;1,8..60,300&display=swap" rel="stylesheet"/>
  <style>
{_CSS}
    /* Article page extras */
    .fundaa-eyebrow {{
      font-family: 'Raleway', sans-serif;
      font-size: 9px; font-weight: 600;
      letter-spacing: 3px; text-transform: uppercase;
      color: var(--accent); margin-bottom: 8px;
    }}
    .fundaa-title {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 32px; font-weight: 600;
      color: var(--navy); line-height: 1.2;
      margin-bottom: 6px;
    }}
    .fundaa-date {{
      font-family: 'Raleway', sans-serif;
      font-size: 11px; color: var(--muted);
      margin-bottom: 28px;
    }}
    .fundaa-body p {{ font-size: 16px; line-height: 1.8; margin-bottom: 18px; font-weight: 300; }}
    .fundaa-body strong {{ font-weight: 600; }}
    .fundaa-body em {{ font-style: italic; }}
    .fundaa-body hr {{ border: none; border-top: 1px solid var(--border); margin: 28px 0; }}
    .fundaa-body ul, .fundaa-body ol {{ padding-left: 24px; margin-bottom: 18px; }}
    .fundaa-body li {{ font-size: 15px; line-height: 1.7; margin-bottom: 6px; }}
    .breadcrumb {{
      font-family: 'Raleway', sans-serif;
      font-size: 10px; font-weight: 500; letter-spacing: 1px;
      color: var(--muted); margin-bottom: 28px;
    }}
    .breadcrumb a {{ color: var(--accent); text-decoration: none; }}
    .breadcrumb a:hover {{ text-decoration: underline; }}
    .breadcrumb .sep {{ margin: 0 8px; color: var(--border); }}
    .header-home-link {{
      position: absolute; inset: 0; z-index: 1;
      display: block; cursor: pointer;
    }}
    .header-inner, .header-meta, .header-accent {{ position: relative; z-index: 2; }}
  </style>
</head>
<body>
<div class="page">

  <header class="header">
    <a href="../../index.html" class="header-home-link" aria-label="Go to Framework Foundry home"></a>
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

  <div class="content">
    <nav class="breadcrumb">
      <a href="../../index.html">Framework Foundry</a>
      <span class="sep">/</span>
      <span>Market IQ</span>
      <span class="sep">/</span>
      <span>Friday Fundaa</span>
      <span class="sep">/</span>
      <span>{title}</span>
    </nav>
    <div class="fundaa-eyebrow">Friday Fundaa</div>
    <div class="fundaa-title">{title}</div>
    <div class="fundaa-date">{display_date}</div>
    <div class="fundaa-body">
      {body_html}
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


def generate_fundaa_pages(articles, site_dir):
    """Write site/fundaa/{date}/index.html for each Friday Fundaa article."""
    fundaa_dir = Path(site_dir) / "fundaa"
    fundaa_dir.mkdir(exist_ok=True)
    for article in articles:
        date_str = article["date"]
        article_dir = fundaa_dir / date_str
        article_dir.mkdir(parents=True, exist_ok=True)
        html = render_fundaa_article_page(article)
        (article_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  -> site/fundaa/{date_str}/index.html")


def _slug(s):
    """Slugify a string for use as a CSS data-category value."""
    import re
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')


def _render_mini_bar_chart(chart_data_json, color_mode="bar"):
    """Render HTML mini bar chart from JSON string.
    color_mode: 'bar' (default, last bar red), 'bar_sign' (green/red by sign), 'bar_inverted' (last bar green).
    """
    try:
        data = _json.loads(chart_data_json)
    except (ValueError, TypeError):
        return ""
    if not data:
        return ""
    max_val = max(abs(d["value"]) for d in data)
    cols = ""
    for i, d in enumerate(data):
        is_last = (i == len(data) - 1)
        pct = (abs(d["value"]) / max_val) * 100 if max_val else 0
        display = d.get("displayValue", f'{d["value"]}%')
        if color_mode == "bar_sign":
            bar_color = ("linear-gradient(180deg,#4ade80,#2a7d4f)" if d["value"] >= 0
                         else "linear-gradient(180deg,#fca5a5,#b91c1c)")
            val_color = ("#4ade80" if d["value"] >= 0 else "#fca5a5") if is_last else "rgba(255,255,255,0.5)"
        elif color_mode == "bar_inverted":
            bar_color = ("linear-gradient(180deg,#4ade80,#2a7d4f)" if is_last
                         else "linear-gradient(180deg,#7aabda,#4a7fb5)")
            val_color = "#4ade80" if is_last else "#7aabda"
        else:
            bar_color = ("linear-gradient(180deg,#b91c1c,#7f1111)" if is_last
                         else "linear-gradient(180deg,#7aabda,#4a7fb5)")
            val_color = "var(--red)" if is_last else "var(--accent-lt)"
        lbl_color = "var(--gold)" if is_last else "rgba(255,255,255,0.45)"
        cols += f"""
      <div class="mini-bar-col">
        <span class="mini-bar-value-label" style="color:{val_color};">{display}</span>
        <div class="mini-bar" style="height:{pct}%;background:{bar_color};"></div>
        <span class="mini-bar-period-label" style="color:{lbl_color};">{d['label']}</span>
      </div>"""
    return f'<div class="mini-bar-chart">{cols}\n    </div>'


def _render_rate_timeline(chart_data_json):
    """Render HTML rate-path timeline from JSON string [{rate, label}, ...]."""
    try:
        data = _json.loads(chart_data_json)
    except (ValueError, TypeError):
        return ""
    if not data:
        return ""
    nodes = ""
    for i, d in enumerate(data):
        is_last = (i == len(data) - 1)
        current_cls = " current-node" if is_last else ""
        dot_cls = " current" if is_last else ""
        nodes += f"""
      <div class="rate-node{current_cls}">
        <div class="rate-connector"></div>
        <div class="rate-dot{dot_cls}"></div>
        <div class="rate-value">{d['rate']}</div>
        <div class="rate-period">{d['label']}</div>
      </div>"""
    return f'<div class="rate-timeline">{nodes}\n    </div>'


def render_featured_flip_card(card):
    """Render front+back HTML for the featured flip card."""
    _color_map = {"red": "var(--red)", "green": "var(--green)"}

    def _color(key):
        return _color_map.get(card.get(key, ""), "var(--text)")

    category    = card.get("category", "")
    term        = card.get("term", "")
    full_name   = card.get("full_name", "")
    formula     = card.get("formula", "")
    definition  = card.get("definition", "")
    context     = card.get("context", "")
    frequency   = card.get("frequency", "")
    trend_class = card.get("trend_class", "trend-flat")
    trend_label = card.get("trend_label", "")

    cur_value  = card.get("current_value", "")
    cur_period = card.get("current_value_period", "")
    chart_html = _render_mini_bar_chart(card.get("chart_data", ""))

    stat1_label = card.get("stat1_label", "")
    stat1_value = card.get("stat1_value", "")
    stat1_sub   = card.get("stat1_sub", "")
    stat2_label = card.get("stat2_label", "")
    stat2_value = card.get("stat2_value", "")
    stat2_sub   = card.get("stat2_sub", "")
    insight     = card.get("insight", "")
    source      = card.get("source", "")

    return f"""<div class="featured-card-label">&#9733; Featured Concept</div>
<div class="flip-card" id="featured-flip">
  <div class="flip-card-inner">

    <!-- FRONT -->
    <div class="flip-card-front">
      <div class="flip-front-header">
        <div class="flip-front-header-inner">
          <div class="flip-front-eyebrow">{category}</div>
          <div class="flip-front-term">{term}</div>
          <div class="flip-front-fullname">{full_name}</div>
        </div>
      </div>
      <div class="flip-front-body">
        <div class="flip-front-what-label">What it is</div>
        <p class="flip-front-def">{definition}</p>
        <div class="flip-front-formula">{formula}</div>
        {f'<p class="flip-front-context">{context}</p>' if context else ""}
      </div>
      <div class="flip-front-footer">
        <span class="iq-card-trend {trend_class}">{trend_label}</span>
        <span class="flip-hint">Flip for latest data &rarr;</span>
      </div>
    </div>

    <!-- BACK -->
    <div class="flip-card-back">
      <div class="flip-back-header">
        <div class="flip-back-header-inner">
          <div>
            <div class="flip-back-source-label">Latest Reading</div>
            <div class="flip-back-title">{term} &mdash; {full_name}</div>
          </div>
          <div style="text-align:right;">
            <div class="flip-back-value" style="color:{_color('current_value_color')};">{cur_value}</div>
            <div class="flip-back-value-period">{cur_period}</div>
          </div>
        </div>
      </div>
      <div class="flip-back-body">
        <div class="mini-bar-chart-wrap">
          {chart_html}
        </div>
        <div class="stat-tile-grid">
          <div class="stat-tile">
            <div class="stat-tile-label">{stat1_label}</div>
            <div class="stat-tile-value" style="color:{_color('stat1_color')};">{stat1_value}</div>
            <div class="stat-tile-sub">{stat1_sub}</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-label">{stat2_label}</div>
            <div class="stat-tile-value" style="color:{_color('stat2_color')};">{stat2_value}</div>
            <div class="stat-tile-sub">{stat2_sub}</div>
          </div>
        </div>
        <div class="insight-callout">
          <div class="insight-callout-label">Analyst Insight</div>
          <p class="insight-callout-text">{insight}</p>
        </div>
      </div>
      <div class="flip-back-footer">
        <span class="flip-back-source">{source}</span>
        <span class="flip-hint">&larr; Flip back</span>
      </div>
    </div>

  </div>
</div>"""


def render_grid_flip_card(card):
    """Render a flip card for the IQ grid (compact, uses .iq-grid-flip structure)."""
    _color_map = {
        "red":   "#b91c1c",
        "green": "#2a7d4f",
        "blue":  "#4a7fb5",
        "gray":  "#6b7280",
    }

    def _c(key):
        return _color_map.get(card.get(key, ""), "var(--text)")

    category     = card.get("category", "")
    term         = card.get("term", "")
    full_name    = card.get("full_name", "")
    formula      = card.get("formula", "")
    definition   = card.get("definition", "")
    frequency    = card.get("frequency", "")
    trend_class  = card.get("trend_class", "trend-flat")
    trend_label  = card.get("trend_label", "")
    cat_slug     = _slug(category)

    cur_value    = card.get("current_value", "")
    cur_period   = card.get("current_value_period", "")
    chart_label  = card.get("chart_label", "")
    chart_type   = card.get("chart_type", "bar")

    if chart_type == "timeline":
        chart_html = _render_rate_timeline(card.get("chart_data", ""))
    else:
        chart_html = _render_mini_bar_chart(card.get("chart_data", ""), chart_type)

    stat1_label = card.get("stat1_label", "")
    stat1_value = card.get("stat1_value", "")
    stat1_sub   = card.get("stat1_sub", "")
    stat2_label = card.get("stat2_label", "")
    stat2_value = card.get("stat2_value", "")
    stat2_sub   = card.get("stat2_sub", "")
    insight     = card.get("insight", "")
    source      = card.get("source", "")
    back_src    = card.get("back_source_label", "Latest Data")
    back_title  = card.get("back_title", f"{term} — Current")

    fullname_html = f'<div class="iq-card-fullname">{full_name}</div>' if full_name else ""
    formula_html  = f'<div class="iq-card-formula">{formula}</div>' if formula else ""

    chart_section = ""
    if chart_html:
        chart_section = f"""
              <div>
                <div class="iq-chart-label">{chart_label}</div>
                <div class="iq-chart-container">{chart_html}</div>
              </div>"""

    return f"""
      <div class="iq-grid-flip" data-category="{cat_slug}" data-term="{term.lower()}" onclick="toggleIQFlip(this)">
        <div class="iq-grid-flip-inner">

          <div class="iq-grid-flip-front">
            <div class="iq-card-top">
              <div class="iq-card-category">{category}</div>
              <div class="iq-card-term">{term}</div>
              {fullname_html}
            </div>
            <div class="iq-grid-flip-front-body">
              <p class="iq-card-def">{definition}</p>
              {formula_html}
            </div>
            <div class="iq-grid-flip-front-footer">
              <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                <span class="iq-card-freq">{frequency}</span>
                <span class="iq-card-trend {trend_class}">{trend_label}</span>
              </div>
              <span class="flip-hint">Flip &rarr;</span>
            </div>
          </div>

          <div class="iq-grid-flip-back">
            <div class="flip-back-header iq-grid-back-header">
              <div class="flip-back-header-inner">
                <div>
                  <div class="flip-back-source-label">{back_src}</div>
                  <div class="flip-back-title">{back_title}</div>
                </div>
                <div style="text-align:right;">
                  <div class="flip-back-value" style="color:{_c('current_value_color')};">{cur_value}</div>
                  <div class="flip-back-value-period">{cur_period}</div>
                </div>
              </div>
            </div>
            <div class="iq-grid-flip-back-body">
              {chart_section}
              <div class="stat-tile-grid">
                <div class="stat-tile">
                  <div class="stat-tile-label">{stat1_label}</div>
                  <div class="stat-tile-value iq-stat-value" style="color:{_c('stat1_color')};">{stat1_value}</div>
                  <div class="stat-tile-sub">{stat1_sub}</div>
                </div>
                <div class="stat-tile">
                  <div class="stat-tile-label">{stat2_label}</div>
                  <div class="stat-tile-value iq-stat-value" style="color:{_c('stat2_color')};">{stat2_value}</div>
                  <div class="stat-tile-sub">{stat2_sub}</div>
                </div>
              </div>
              <div class="insight-callout">
                <div class="insight-callout-label">What This Means For You</div>
                <p class="insight-callout-text">{insight}</p>
              </div>
            </div>
            <div class="flip-back-footer iq-grid-back-footer">
              <span class="flip-back-source">{source}</span>
              <span class="flip-hint">&larr; Flip back</span>
            </div>
          </div>

        </div>
      </div>"""


def render_market_iq_panel(cards, fundaa_articles=None):
    """Render the Market IQ panel HTML with Market IQ / Friday Fundaa sub-tabs."""
    if fundaa_articles is None:
        fundaa_articles = []

    featured = next((c for c in cards if c.get("featured") == "true"), None)
    grid_cards = [c for c in cards if c.get("featured") != "true"]

    # Extract unique categories from grid cards preserving order
    seen = set()
    categories = []
    for c in grid_cards:
        cat = c.get("category", "")
        if cat and cat not in seen:
            seen.add(cat)
            categories.append(cat)

    cat_buttons = f'<button class="iq-cat-btn active" onclick="filterIQCards(this,\'all\')">All</button>\n'
    for cat in categories:
        slug = _slug(cat)
        cat_buttons += f'      <button class="iq-cat-btn" onclick="filterIQCards(this,\'{slug}\')">{cat}</button>\n'

    card_html = ""
    for c in grid_cards:
        if c.get("current_value"):
            card_html += render_grid_flip_card(c)
        else:
            term = c.get("term", "")
            category = c.get("category", "")
            definition = c.get("definition", "")
            frequency = c.get("frequency", "")
            trend_label = c.get("trend_label", "")
            trend_class = c.get("trend_class", "trend-flat")
            cat_slug = _slug(category)
            card_html += f"""
      <div class="iq-card" data-category="{cat_slug}" data-term="{term.lower()}">
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

    featured_html = render_featured_flip_card(featured) if featured else ""

    # Friday Fundaa article list
    fundaa_rows = ""
    for a in fundaa_articles:
        fundaa_rows += f"""
      <a class="article-row" href="fundaa/{a['date']}/index.html">
        <div class="article-tag-col">
          <span class="article-tag guide">Fundaa</span>
        </div>
        <div class="article-content">
          <div class="article-title">{a['title']}</div>
          <div class="article-excerpt">{a['excerpt']}</div>
        </div>
        <div class="article-meta-col">
          <span class="article-date">{a['display_date']}</span>
        </div>
      </a>"""

    if not fundaa_rows:
        fundaa_rows = '<p style="color:var(--muted);font-family:\'Raleway\',sans-serif;font-size:12px;padding:24px 0;">No Friday Fundaa articles yet.</p>'

    return f"""<div id="panel-marketiq" class="section-panel">
  <div class="content">
    <div class="section-label">Market IQ &mdash; Economic Concepts, Plain &amp; Simple</div>

    <div class="iq-sub-nav sub-nav">
      <a class="iq-sub-tab sub-tab active" data-target="iq-sub-flashcards" onclick="showSubNav(this)">Market IQ</a>
      <a class="iq-sub-tab sub-tab" data-target="iq-sub-fundaa" onclick="showSubNav(this)">Friday Fundaa</a>
    </div>

    <div id="iq-sub-flashcards" class="sub-panel active">
      <p class="iq-intro">
        No economics degree required. Each card explains one concept &mdash; what it is, why it matters,
        how often it&rsquo;s published, and what the recent trend means for your money.
      </p>
      {featured_html}
      <div class="iq-search-row">
        <div class="iq-search-wrapper">
          <svg class="iq-search-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
            <circle cx="8.5" cy="8.5" r="5.5"/>
            <line x1="13" y1="13" x2="18" y2="18"/>
          </svg>
          <input type="text" class="iq-search-input" placeholder="Search concepts &mdash; e.g. CPI, yield curve, employment&hellip;" oninput="searchIQCards(this.value)" autocomplete="off" spellcheck="false" />
          <button class="iq-search-clear" onclick="clearIQSearch()" aria-label="Clear search">&times;</button>
        </div>
      </div>
      <div class="iq-no-results" id="iq-no-results">No cards match &ldquo;<span id="iq-no-results-term"></span>&rdquo; &mdash; try a shorter term or browse by category.</div>
      <div class="iq-categories">
        {cat_buttons}
      </div>
      <div class="iq-alpha-row" id="iq-alpha-row"></div>
      <div class="iq-grid">
        {card_html}
      </div>
      <div class="iq-see-all"><a href="#">View all concepts &rarr;</a></div>
    </div>

    <div id="iq-sub-fundaa" class="sub-panel">
      <p class="iq-intro">
        A short weekly moment of &ldquo;huh, didn&rsquo;t know that&rdquo; from the world of markets and money.
        Plain English. No jargon. Just one idea you can actually use.
      </p>
      <div class="article-list">
        {fundaa_rows}
      </div>
    </div>

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
  <div class="content">
    <div class="section-label">Expat Investing &mdash; Resources for Americans Living Abroad</div>
    <p class="investing-intro">
      Navigating PFIC rules, FBAR reporting, tax-efficient investing from outside the US,
      and building wealth across borders. A magazine-style deep dive for the global American investor.
    </p>
    <div class="article-list">
      <a class="article-row" href="/expat/issue-01/index.html">
        <div class="article-tag-col">
          <span class="article-tag guide">Issue 01</span>
        </div>
        <div class="article-content">
          <div class="article-title">The Portugal Issue</div>
          <div class="article-excerpt">D7 Visa · FBAR · Banking · PRIIPs &mdash; Everything you need to know about moving money and building wealth as an American expat in Portugal.</div>
        </div>
        <div class="article-meta-col">
          <span class="article-date">Mar 2026</span>
          <span class="article-read-time">Read Issue &rarr;</span>
        </div>
      </a>
    </div>
  </div>
</div>"""

_JS = """\
<script>
function showSection(id, skipHash) {
  document.querySelectorAll('.section-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.section-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('active');
  var labels = { markets: 0, marketiq: 1, investing: 2, expat: 3 };
  var tabs = document.querySelectorAll('.section-tab');
  if (labels[id] !== undefined) tabs[labels[id]].classList.add('active');
  if (id === 'marketiq') sizeIQGridFlips();
  if (!skipHash) history.replaceState(null, '', '#' + id);
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
document.querySelectorAll('.article-filters .iq-cat-btn')
  .forEach(function(btn) {
    btn.addEventListener('click', function() {
      this.closest('.article-filters')
          .querySelectorAll('.iq-cat-btn')
          .forEach(function(b) { b.classList.remove('active'); });
      this.classList.add('active');
    });
  });
document.querySelectorAll('.flip-card').forEach(function(card) {
  card.addEventListener('click', function() {
    this.classList.toggle('flipped');
  });
});

/* ── MARKET IQ: SEARCH, FILTER, ALPHA NAV ── */
function filterIQCards(btn, category) {
  document.querySelectorAll('.iq-alpha-btn').forEach(function(b) { b.classList.remove('alpha-active'); });
  var si = document.querySelector('.iq-search-input');
  if (si && si.value) { si.value = ''; var sc = document.querySelector('.iq-search-clear'); if (sc) sc.classList.remove('visible'); }
  var nr = document.getElementById('iq-no-results'); if (nr) nr.classList.remove('visible');
  var container = btn.closest('.iq-categories');
  if (container) container.querySelectorAll('.iq-cat-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  document.querySelectorAll('#iq-sub-flashcards .iq-card, #iq-sub-flashcards .iq-grid-flip').forEach(function(card) {
    card.style.display = (category === 'all' || card.dataset.category === category) ? '' : 'none';
  });
}

function buildIQAlphaNav() {
  var hasCards = {};
  document.querySelectorAll('#iq-sub-flashcards .iq-card, #iq-sub-flashcards .iq-grid-flip').forEach(function(card) {
    var ch = (card.dataset.term || '')[0];
    if (ch) hasCards[ch.toUpperCase()] = true;
  });
  var row = document.getElementById('iq-alpha-row');
  if (!row) return;
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach(function(letter) {
    var btn = document.createElement('button');
    btn.className = 'iq-alpha-btn' + (hasCards[letter] ? ' has-cards' : '');
    btn.textContent = letter;
    if (hasCards[letter]) {
      btn.addEventListener('click', function() { filterIQByLetter(btn, letter); });
    }
    row.appendChild(btn);
  });
}

function filterIQByLetter(btn, letter) {
  if (btn.classList.contains('alpha-active')) {
    btn.classList.remove('alpha-active');
    var allBtn = document.querySelector('.iq-categories .iq-cat-btn');
    if (allBtn) filterIQCards(allBtn, 'all');
    return;
  }
  document.querySelectorAll('.iq-alpha-btn').forEach(function(b) { b.classList.remove('alpha-active'); });
  document.querySelectorAll('.iq-categories .iq-cat-btn').forEach(function(b) { b.classList.remove('active'); });
  var si = document.querySelector('.iq-search-input');
  if (si) { si.value = ''; var sc = document.querySelector('.iq-search-clear'); if (sc) sc.classList.remove('visible'); }
  var nr = document.getElementById('iq-no-results'); if (nr) nr.classList.remove('visible');
  btn.classList.add('alpha-active');
  document.querySelectorAll('#iq-sub-flashcards .iq-card, #iq-sub-flashcards .iq-grid-flip').forEach(function(card) {
    var first = (card.dataset.term || '')[0];
    card.style.display = (first && first.toUpperCase() === letter) ? '' : 'none';
  });
}

function searchIQCards(query) {
  var q = query.trim().toLowerCase();
  var sc = document.querySelector('.iq-search-clear');
  var nr = document.getElementById('iq-no-results');
  var nrt = document.getElementById('iq-no-results-term');
  if (sc) sc.classList.toggle('visible', q.length > 0);
  if (!q) {
    if (nr) nr.classList.remove('visible');
    var allBtn = document.querySelector('.iq-categories .iq-cat-btn');
    if (allBtn) filterIQCards(allBtn, 'all');
    return;
  }
  document.querySelectorAll('.iq-categories .iq-cat-btn').forEach(function(b) { b.classList.remove('active'); });
  document.querySelectorAll('.iq-alpha-btn').forEach(function(b) { b.classList.remove('alpha-active'); });
  var matchCount = 0;
  document.querySelectorAll('#iq-sub-flashcards .iq-card, #iq-sub-flashcards .iq-grid-flip').forEach(function(card) {
    var text = [
      card.dataset.category || '',
      card.dataset.term || '',
      (card.querySelector('.iq-card-term') || {textContent:''}).textContent,
      (card.querySelector('.iq-card-def')  || {textContent:''}).textContent,
      (card.querySelector('.iq-card-category') || {textContent:''}).textContent
    ].join(' ').toLowerCase();
    var match = text.indexOf(q) !== -1;
    card.style.display = match ? '' : 'none';
    if (match) matchCount++;
  });
  if (nrt) nrt.textContent = query.trim();
  if (nr) nr.classList.toggle('visible', matchCount === 0);
}

function clearIQSearch() {
  var input = document.querySelector('.iq-search-input');
  if (input) { input.value = ''; searchIQCards(''); input.focus(); }
}

function toggleIQFlip(el) {
  el.classList.toggle('flipped');
}

function sizeIQGridFlips() {
  document.querySelectorAll('.iq-grid-flip').forEach(function(wrapper) {
    var inner = wrapper.querySelector('.iq-grid-flip-inner');
    var front = wrapper.querySelector('.iq-grid-flip-front');
    var back  = wrapper.querySelector('.iq-grid-flip-back');
    if (!inner || !front || !back) return;
    front.style.position = 'relative';
    var frontH = front.scrollHeight;
    front.style.position = '';
    back.style.transform  = 'none';
    back.style.position   = 'relative';
    back.style.visibility = 'hidden';
    var backH = back.scrollHeight;
    back.style.transform  = 'rotateY(180deg)';
    back.style.position   = '';
    back.style.visibility = '';
    inner.style.height = Math.max(frontH, backH) + 'px';
  });
}

document.addEventListener('DOMContentLoaded', function() {
  buildIQAlphaNav();
  var valid = { markets: 1, marketiq: 1, investing: 1, expat: 1 };
  var hash = (location.hash || '').replace('#', '');
  showSection(valid[hash] ? hash : 'markets', true);
});
</script>"""


# ── Landing page ──────────────────────────────────────────────────────────────

def render_landing(us_dates, intl_dates, us_ctxs, intl_ctxs, pdf_map,
                   daybreak_dates=None, daybreak_ctxs=None,
                   market_iq_cards=None, articles=None, fundaa_articles=None):
    """Render site/index.html — 4-tab hub (Markets / Market IQ / Investing / Expat)."""
    if daybreak_dates is None:
        daybreak_dates = []
    if market_iq_cards is None:
        market_iq_cards = []
    if articles is None:
        articles = []
    if fundaa_articles is None:
        fundaa_articles = []

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
    marketiq_panel = render_market_iq_panel(market_iq_cards, fundaa_articles)
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

  <!-- FEEDBACK -->
  <section class="feedback-section">
    <div class="feedback-inner">
      <div class="feedback-title">Leave a comment</div>
      <form class="feedback-form" action="https://formspree.io/f/mwpvyoal" method="POST">
        <input type="hidden" name="_subject" value="Framework Foundry - You have a new comment" />
        <input type="hidden" name="_replyto" value="" />
        <div class="feedback-row">
          <input type="text"  name="name"    placeholder="Your name (optional)" />
          <input type="email" name="email"   placeholder="Your email (optional)" />
        </div>
        <textarea name="message" rows="4" placeholder="Your comment or feedback..." required></textarea>
        <button type="submit">Send</button>
      </form>
    </div>
  </section>

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

  <!-- FEEDBACK -->
  <section class="feedback-section">
    <div class="feedback-inner">
      <div class="feedback-title">Leave a comment</div>
      <form class="feedback-form" action="https://formspree.io/f/mwpvyoal" method="POST">
        <input type="hidden" name="_subject" value="Framework Foundry - You have a new comment" />
        <input type="hidden" name="_replyto" value="" />
        <div class="feedback-row">
          <input type="text"  name="name"    placeholder="Your name (optional)" />
          <input type="email" name="email"   placeholder="Your email (optional)" />
        </div>
        <textarea name="message" rows="4" placeholder="Your comment or feedback..." required></textarea>
        <button type="submit">Send</button>
      </form>
    </div>
  </section>

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
        html = inject_header_link(html, "../../index.html")
        html = inject_breadcrumb(html, [
            ("Framework Foundry", "../../index.html"),
            ("Markets", "../../index.html#markets"),
            (f"Weekly — {fmt_date(date_str)}", None),
        ])
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
        html = inject_header_link(html, "../../index.html")
        html = inject_breadcrumb(html, [
            ("Framework Foundry", "../../index.html"),
            ("Markets", "../../index.html#markets"),
            (f"International — {fmt_date(date_str)}", None),
        ])
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
        html = inject_header_link(html, "../../index.html")
        html = inject_breadcrumb(html, [
            ("Framework Foundry", "../../index.html"),
            ("Markets", "../../index.html#markets"),
            ("Day Break", "../../daily/index.html"),
            (fmt_date(date_str), None),
        ])
        (issue_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  -> site/daily/{date_str}/index.html")

    # Build landing page (4-tab hub)
    market_iq_cards = load_market_iq_cards()
    articles = load_articles()
    fundaa_articles = parse_fundaa_articles()
    generate_fundaa_pages(fundaa_articles, SITE_DIR)
    landing_html = render_landing(
        us_dates, intl_dates, us_ctxs, intl_ctxs, pdf_map,
        daybreak_dates=daybreak_dates, daybreak_ctxs=daybreak_ctxs,
        market_iq_cards=market_iq_cards, articles=articles,
        fundaa_articles=fundaa_articles,
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
