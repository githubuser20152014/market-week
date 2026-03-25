#!/usr/bin/env python3
"""
build_blueprint_site.py — Build a Blueprint article page for the static site.

Usage:
    python build_blueprint_site.py --date 2026-03-26
    python build_blueprint_site.py --source path/to/article.md

Reads a Blueprint issue from ContentRepo/wednesday-series/Issues/ and writes
a styled HTML page to site/investing-101/{slug}/index.html.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import markdown as md_lib

SCRIPT_DIR   = Path(__file__).resolve().parent
SITE_DIR     = SCRIPT_DIR / "site"
CONTENT_REPO = Path("C:/Users/Akhil/Documents/ContentRepo")
ISSUES_DIR   = CONTENT_REPO / "wednesday-series/Issues"

FORMSPREE_ID = "mwpvyoal"
BASE_URL     = "https://frameworkfoundry.info"


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    meta = {}
    for line in fm_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"')
    return meta, body


def find_article_by_date(date_str: str) -> Path | None:
    for md_file in ISSUES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        if meta.get("date") == date_str:
            return md_file
    return None


def fmt_date(date_str: str) -> str:
    """'2026-03-26' → 'Mar 26, 2026'"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y").replace(" 0", " ")
    except ValueError:
        return date_str


# ── HTML template ─────────────────────────────────────────────────────────────

def render_html(meta: dict, body_html: str) -> str:
    title      = meta.get("title", "The Blueprint")
    issue_num  = meta.get("issue", "")
    date_str   = meta.get("date", "")
    slug       = meta.get("slug", "")
    url        = meta.get("url", f"/investing-101/{slug}/")
    read_time  = meta.get("read_time", "")
    excerpt    = meta.get("excerpt", title)

    date_display = fmt_date(date_str)
    meta_parts   = [date_display] + ([read_time] if read_time else [])
    meta_str     = " &nbsp;&middot;&nbsp; ".join(meta_parts)

    eyebrow = f"The Blueprint &middot; Issue #{issue_num}" if issue_num else "The Blueprint"
    page_url = f"{BASE_URL}{url}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title} | Framework Foundry</title>
  <meta property="og:title" content="{title}"/>
  <meta property="og:description" content="{excerpt}"/>
  <meta property="og:url" content="{page_url}"/>
  <meta property="og:type" content="article"/>
  <meta property="og:site_name" content="Framework Foundry"/>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Raleway:wght@200;300;400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;1,8..60,300&display=swap" rel="stylesheet"/>
  <style>
  :root {{
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
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    font-family: 'Source Serif 4', Georgia, serif;
    color: var(--text);
    padding: 32px 16px;
    min-height: 100vh;
  }}

  .page {{
    max-width: 900px;
    margin: 0 auto;
    background: var(--white);
    box-shadow: 0 8px 48px rgba(0,0,0,0.18);
  }}

  /* HEADER */
  .header {{
    background: var(--navy);
    position: relative;
    overflow: hidden;
  }}

  .header::before {{
    content: '';
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
    background-size: 28px 28px;
  }}

  .header-inner {{
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 28px 40px 24px;
    gap: 24px;
  }}

  .logo-icon {{ flex-shrink: 0; width: 64px; height: 64px; }}
  .logo-text {{ flex: 1; }}

  .logo-name-framework {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 30px; font-weight: 600; letter-spacing: 4px;
    color: var(--white); display: block; line-height: 1;
  }}

  .logo-name-foundry {{
    font-family: 'Raleway', sans-serif;
    font-size: 14px; font-weight: 300; letter-spacing: 12px;
    color: var(--accent); display: block; margin-top: 5px; line-height: 1;
  }}

  .logo-rule {{
    height: 1px; background: rgba(255,255,255,0.15); margin: 8px 0 6px;
  }}

  .logo-tagline {{
    font-family: 'Raleway', sans-serif; font-size: 8.5px; font-weight: 300;
    letter-spacing: 3.5px; color: rgba(255,255,255,0.4); text-transform: uppercase;
  }}

  .header-accent {{
    height: 3px;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent-lt) 50%, transparent 100%);
  }}

  .header-home-link {{
    position: absolute; inset: 0; z-index: 1;
    display: block; cursor: pointer;
  }}

  .header-inner, .header-accent {{ position: relative; z-index: 2; }}

  /* CONTENT */
  .content {{ padding: 36px 40px; }}

  /* BREADCRUMB */
  .breadcrumb {{
    font-family: 'Raleway', sans-serif;
    font-size: 10px; font-weight: 500; letter-spacing: 1px;
    color: var(--muted); margin-bottom: 28px;
  }}

  .breadcrumb a {{ color: var(--accent); text-decoration: none; }}
  .breadcrumb a:hover {{ text-decoration: underline; }}
  .breadcrumb .sep {{ margin: 0 8px; color: var(--border); }}

  /* ARTICLE */
  .i101-eyebrow {{
    font-family: 'Raleway', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--accent); margin-bottom: 8px;
  }}

  .i101-title {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 32px; font-weight: 600;
    color: var(--navy); line-height: 1.2;
    margin-bottom: 6px;
  }}

  .i101-meta {{
    font-family: 'Raleway', sans-serif;
    font-size: 11px; color: var(--muted);
    margin-bottom: 32px;
  }}

  .i101-body p  {{ font-size: 16px; line-height: 1.85; margin-bottom: 20px; font-weight: 300; }}
  .i101-body h2 {{ font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 600;
                  color: var(--navy); margin: 36px 0 12px; }}
  .i101-body h3 {{ font-family: 'Cormorant Garamond', serif; font-size: 18px; font-weight: 600;
                  color: var(--navy); margin: 28px 0 10px; }}
  .i101-body strong {{ font-weight: 600; }}
  .i101-body em     {{ font-style: italic; }}
  .i101-body hr     {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}
  .i101-body ul, .i101-body ol {{ padding-left: 24px; margin-bottom: 18px; }}
  .i101-body li {{ font-size: 15px; line-height: 1.75; margin-bottom: 6px; font-weight: 300; }}
  .i101-body a  {{ color: var(--accent); text-decoration: none; border-bottom: 1px solid rgba(74,127,181,0.3); }}
  .i101-body a:hover {{ border-bottom-color: var(--accent); }}
  .i101-body table {{
    width: 100%; border-collapse: collapse; margin-bottom: 24px;
    font-family: 'Raleway', sans-serif; font-size: 13px;
  }}
  .i101-body th {{
    background: var(--navy); color: var(--white);
    padding: 8px 12px; font-weight: 500; font-size: 11px;
    letter-spacing: 1px; text-align: left;
  }}
  .i101-body td {{
    padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: middle;
  }}
  .i101-body tbody tr:nth-child(even) {{ background: var(--off-white); }}

  /* SUBSCRIBE */
  .subscribe-section {{
    background: var(--navy); padding: 36px 40px; text-align: center;
  }}

  .subscribe-section h2 {{
    font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 600;
    color: var(--white); margin: 0 0 6px; letter-spacing: 0.5px;
  }}

  .subscribe-section p {{
    font-family: 'Raleway', sans-serif; font-size: 11px;
    color: rgba(255,255,255,0.55); letter-spacing: 1px;
    text-transform: uppercase; margin: 0 0 20px;
  }}

  .subscribe-form {{
    display: flex; justify-content: center; gap: 0;
    max-width: 440px; margin: 0 auto;
  }}

  .subscribe-form input[type="email"] {{
    flex: 1; padding: 10px 16px;
    font-family: 'Raleway', sans-serif; font-size: 12px;
    border: 1px solid rgba(255,255,255,0.2); border-right: none;
    border-radius: 2px 0 0 2px; background: rgba(255,255,255,0.08);
    color: var(--white); outline: none;
  }}

  .subscribe-form input[type="email"]::placeholder {{ color: rgba(255,255,255,0.35); }}

  .subscribe-form button {{
    padding: 10px 20px; font-family: 'Raleway', sans-serif;
    font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    background: var(--accent); color: var(--white); border: none;
    border-radius: 0 2px 2px 0; cursor: pointer; transition: background 0.2s; white-space: nowrap;
  }}

  .subscribe-form button:hover {{ background: var(--accent-lt); }}

  /* FOOTER */
  .footer {{
    background: var(--navy); padding: 16px 40px;
    display: flex; align-items: center; justify-content: space-between;
  }}

  .footer-logo {{
    font-family: 'Cormorant Garamond', serif; font-size: 13px;
    font-weight: 400; letter-spacing: 2px; color: rgba(255,255,255,0.5);
  }}

  .footer-logo span {{ color: var(--accent); }}

  .footer-disclaimer {{
    font-family: 'Raleway', sans-serif; font-size: 8.5px;
    color: rgba(255,255,255,0.3); letter-spacing: 0.5px;
    text-align: right; max-width: 380px; line-height: 1.6;
  }}

  @media (max-width: 680px) {{
    .header-inner {{ padding: 20px 20px 16px; flex-wrap: wrap; }}
    .content      {{ padding: 24px 20px; }}
    .footer       {{ padding: 14px 20px; flex-direction: column; gap: 10px; }}
    .subscribe-section {{ padding: 28px 20px; }}
    .subscribe-form {{ flex-direction: column; }}
    .subscribe-form input[type="email"] {{
      border-right: 1px solid rgba(255,255,255,0.2);
      border-bottom: none; border-radius: 2px 2px 0 0;
    }}
    .subscribe-form button {{ border-radius: 0 0 2px 2px; }}
  }}
  </style>
</head>
<body>
<div class="page">

  <header class="header">
    <a href="../../../index.html" class="header-home-link" aria-label="Go to Framework Foundry home"></a>
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
        <span class="logo-tagline">The Blueprint &nbsp;&middot;&nbsp; Practical Investing Guides</span>
      </div>
    </div>
    <div class="header-accent"></div>
  </header>

  <div class="content">
    <nav class="breadcrumb">
      <a href="../../../index.html">Framework Foundry</a>
      <span class="sep">/</span>
      <a href="../../../index.html#investing">Investing</a>
      <span class="sep">/</span>
      <span>The Blueprint</span>
      <span class="sep">/</span>
      <span>{title}</span>
    </nav>
    <div class="i101-eyebrow">{eyebrow}</div>
    <div class="i101-title">{title}</div>
    <div class="i101-meta">{meta_str}</div>
    <div class="i101-body">
      {body_html}
    </div>
  </div>

  <div class="subscribe-section">
    <h2>Stay in the loop</h2>
    <p>Weekly macro intelligence and practical investing guides &mdash; free, every week.</p>
    <form class="subscribe-form" action="https://formspree.io/f/{FORMSPREE_ID}" method="POST">
      <input type="email" name="email" placeholder="your@email.com" required />
      <button type="submit">Subscribe free</button>
    </form>
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build Blueprint article HTML page.")
    parser.add_argument("--date",   help="Article date YYYY-MM-DD (used to find article)")
    parser.add_argument("--source", help="Override article file path")
    args = parser.parse_args()

    if not args.date and not args.source:
        parser.error("Provide --date or --source")

    if args.source:
        source_path = Path(args.source)
    else:
        source_path = find_article_by_date(args.date)

    if source_path is None or not source_path.exists():
        print(f"ERROR: No Blueprint article found for date {args.date}", file=sys.stderr)
        sys.exit(1)

    raw = source_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)

    slug = meta.get("slug")
    if not slug:
        print("ERROR: Article frontmatter missing 'slug' field.", file=sys.stderr)
        sys.exit(1)

    body_html = md_lib.markdown(body, extensions=["tables"])

    html = render_html(meta, body_html)

    out_dir = SITE_DIR / "investing-101" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")

    print(f"Article : {source_path.name}")
    print(f"Output  : {out_file}")
    print(f"URL     : {BASE_URL}/investing-101/{slug}/")


if __name__ == "__main__":
    main()
