#!/usr/bin/env python3
"""
verify_site_content.py — Check that the published HTML matches the final .md file.

Compares free-text narrative sections (Morning Brief, What This Means) between
the approved .md file and the built site HTML.  Exits non-zero if any mismatch
is found, which causes publish_daybreak.sh to abort before committing.

Usage:
    python verify_site_content.py 2026-03-10
"""

import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# Narrative sections whose paragraph text must match exactly.
SECTIONS_TO_CHECK = ["Morning Brief", "What This Means"]


# ── Text normalisation ────────────────────────────────────────────────────────

def strip_md(text: str) -> str:
    """Convert a markdown paragraph to plain text."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # bold
    text = re.sub(r'__(.+?)__',     r'\1', text)   # bold alt
    text = re.sub(r'\*(.+?)\*',     r'\1', text)   # italic
    text = re.sub(r'_(.+?)_',       r'\1', text)   # italic alt
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # links → link text
    text = re.sub(r'^[-*]\s+', '', text)            # list bullet
    return text.strip()


def strip_html(text: str) -> str:
    """Strip HTML tags and decode common entities."""
    text = re.sub(r'<[^>]+>', '', text)
    text = (text
            .replace('&amp;', '&')
            .replace('&lt;', '<')
            .replace('&gt;', '>')
            .replace('&nbsp;', ' ')
            .replace('&#39;', "'")
            .replace('&quot;', '"'))
    return text.strip()


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_md_sections(md_path: Path) -> dict[str, list[str]]:
    """Return {section_title: [paragraph, …]} for every ## section in the MD."""
    content = md_path.read_text(encoding='utf-8')
    sections: dict[str, list[str]] = {}
    current: str | None = None
    paras: list[str] = []

    for line in content.splitlines():
        if line.startswith('## '):
            if current is not None:
                sections[current] = paras
            current = line[3:].strip()
            paras = []
        elif current is not None:
            stripped = line.strip()
            # Skip blank lines, horizontal rules, table rows, sub-headings,
            # and the italicised tagline at the top.
            if (not stripped
                    or stripped.startswith('|')
                    or stripped.startswith('#')
                    or stripped == '---'
                    or stripped.startswith('*Daily')):
                continue
            paras.append(strip_md(stripped))

    if current is not None:
        sections[current] = paras
    return sections


def parse_html_sections(html_path: Path) -> dict[str, list[str]]:
    """Return {section_title: [paragraph, …]} extracted from brief-text <p> tags."""
    content = html_path.read_text(encoding='utf-8')

    # Split on section-title divs to get (title, body) pairs.
    parts = re.split(r'<div class="section-title">(.*?)</div>', content, flags=re.DOTALL)
    # parts[0] = preamble, then alternating [title, body, title, body, …]
    sections: dict[str, list[str]] = {}
    for i in range(1, len(parts), 2):
        title = strip_html(parts[i]).strip()
        body  = parts[i + 1] if i + 1 < len(parts) else ''
        paras = re.findall(r'<p class="brief-text">(.*?)</p>', body, re.DOTALL)
        sections[title] = [strip_html(p) for p in paras]
    return sections


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    md_path   = SCRIPT_DIR / 'output' / f'market_day_break_{date_str}.md'
    html_path = SCRIPT_DIR / 'site' / 'daily' / date_str / 'index.html'

    for path in (md_path, html_path):
        if not path.exists():
            print(f"ERROR: File not found: {path}")
            sys.exit(1)

    md_sections   = parse_md_sections(md_path)
    html_sections = parse_html_sections(html_path)

    mismatches: list[str] = []

    for section in SECTIONS_TO_CHECK:
        md_paras   = md_sections.get(section, [])
        html_paras = html_sections.get(section, [])

        if len(md_paras) != len(html_paras):
            mismatches.append(
                f"[{section}] paragraph count differs — MD: {len(md_paras)}, HTML: {len(html_paras)}"
            )

        for j, (md_p, html_p) in enumerate(zip(md_paras, html_paras), 1):
            if md_p != html_p:
                mismatches.append(
                    f"[{section}] paragraph {j} mismatch:\n"
                    f"  MD  : {md_p}\n"
                    f"  HTML: {html_p}"
                )

    if mismatches:
        print(f"\nCONTENT MISMATCH — {len(mismatches)} issue(s) found for {date_str}:\n")
        for m in mismatches:
            print(f"  {m}\n")
        print("Fix the source data / generator so the HTML matches the approved MD, then re-run.")
        sys.exit(1)

    checked = ', '.join(SECTIONS_TO_CHECK)
    print(f"OK — HTML matches {md_path.name}  [{checked}]")


if __name__ == '__main__':
    main()
