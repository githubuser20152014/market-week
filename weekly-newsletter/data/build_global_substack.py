#!/usr/bin/env python3
"""
Build Substack HTML from approved global newsletter markdown.
Usage: cd weekly-newsletter && python data/build_global_substack.py --date 2026-03-27
"""
import argparse
import pathlib
from datetime import datetime, timedelta
import markdown as md_lib

HEADER_TMPL = """\
<p><strong>Framework Foundry: Global Investor Edition | {pub_date}</strong></p>
<p><em>Weekly macro briefing for globally diversified, long-term investors. What happened, why it matters, and what to do about it.</em></p>
<hr>
"""

FOOTER_TMPL = """\
<hr>
<p><em>Framework Foundry publishes three editions:</em></p>
<ul>
  <li><em><strong>Morning Brief</strong>: daily pre-market briefing, Monday through Friday</em></li>
  <li><em><strong>Global Investor Edition</strong>: international markets, FX, and positioning, every Saturday</em></li>
  <li><em><strong>The Blueprint</strong> — investment primers, every Wednesday</em></li>
</ul>
<p><em>Full edition with data tables and charts: <a href="https://frameworkfoundry.info/global/{date_str}/">frameworkfoundry.info/global/{date_str}</a></em></p>
<p><em>All editions: <a href="https://frameworkfoundry.info">frameworkfoundry.info</a></em></p>
<hr>
<p><strong>Disclaimer</strong></p>
<p><em>This newsletter is for informational and educational purposes only. Nothing in this publication constitutes investment advice, financial advice, trading advice, or any other sort of advice. Framework Foundry does not recommend that you buy, sell, or hold any security. Conduct your own due diligence and consult a licensed financial advisor before making any investment decisions. Past performance is not indicative of future results. All investments involve risk, including the possible loss of principal.</em></p>
"""


def build(date_str: str):
    root = pathlib.Path(__file__).parent.parent
    md_path = root / f"output/global_newsletter_{date_str}.md"
    out_path = root / f"output/global_substack_{date_str}.html"

    if not md_path.exists():
        raise FileNotFoundError(f"Approved markdown not found: {md_path}")

    raw = md_path.read_text(encoding="utf-8")

    # Strip the document-level title block at the top (# / ## headings, blanks, first ---)
    # so Substack's own title field carries the headline.
    lines = raw.splitlines()
    body_lines = []
    skip_header = True
    first_hr_seen = False
    for line in lines:
        if skip_header:
            if not line.strip():                          # blank lines in title block
                continue
            if line.startswith("# ") or line.startswith("## "):
                continue
            if line.strip() == "---" and not first_hr_seen:
                first_hr_seen = True
                continue
            skip_header = False
        body_lines.append(line)

    # Strip trailing inline disclaimer — replaced by the full FOOTER below
    while body_lines and body_lines[-1].strip() in ("", "---"):
        body_lines.pop()
    if body_lines and body_lines[-1].strip().startswith("*Framework Foundry Weekly"):
        body_lines.pop()
    while body_lines and body_lines[-1].strip() in ("", "---"):
        body_lines.pop()

    body_md = "\n".join(body_lines)

    body_html = md_lib.markdown(body_md, extensions=["tables"])

    # Derive a human-readable publication date (day after the week-end Friday)
    week_end = datetime.strptime(date_str, "%Y-%m-%d")
    pub_date = (week_end + timedelta(days=1)).strftime("%B %d, %Y").replace(" 0", " ")

    header = HEADER_TMPL.format(pub_date=pub_date)
    footer = FOOTER_TMPL.format(date_str=date_str)

    html = header + body_html + "\n" + footer
    out_path.write_text(html, encoding="utf-8")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Week-end date, e.g. 2026-03-27")
    args = parser.parse_args()
    build(args.date)
