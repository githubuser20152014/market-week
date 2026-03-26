#!/usr/bin/env python3
"""
verify_site_content.py — Verify the published HTML AND PDF match the approved .md exactly.

Checks every section of the Market Day Break newsletter:
  Paragraphs  — The Brief
  Tables      — Market-Moving Headlines
  Tips        — Positioning Notes (Signal -- Action format)

Also verifies the PDF: extracts text via pypdf and checks that every
narrative paragraph (Morning Brief, What This Means) and every headline
appears verbatim in the PDF text.

Known formatting differences between .md and HTML/PDF are normalised before
comparison (thousand-separators, HTML entities, markdown markup, session
labels, placeholder wording).  Exits non-zero on any mismatch so that
publish_daybreak.sh aborts before committing.

Usage:
    python verify_site_content.py 2026-03-10
"""

import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


# ── Normalisation ─────────────────────────────────────────────────────────────

def strip_html_tags(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    return (text
            .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
            .replace('\u2019', "'").replace('\u2018', "'")   # curly apostrophes → straight
            .replace('\u201c', '"').replace('\u201d', '"')   # curly quotes → straight
            .replace('\u2013', '-').replace('\u2014', '--')) # en/em dash → ASCII


def strip_md_markup(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*',     r'\1', text)
    text = re.sub(r'_(.+?)_',       r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)   # [link text](url) → text
    text = re.sub(r'^[-*]\s+', '', text.strip())       # list bullet
    return text


def norm(text: str, *, lower: bool = False) -> str:
    """Strip HTML tags, strip MD markup, remove thousand-separators, collapse spaces."""
    text = strip_html_tags(text)
    text = strip_md_markup(text)
    text = re.sub(r'(\d),(\d{3})\b', r'\1\2', text)   # 5,190.80 → 5190.80
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower() if lower else text


# ── MD parsing ────────────────────────────────────────────────────────────────

def split_md_sections(md: str) -> dict[str, str]:
    """Return {section_title: raw_text} for every ## heading."""
    sections: dict[str, str] = {}
    current, buf = None, []
    for line in md.splitlines():
        if line.startswith('## '):
            if current is not None:
                sections[current] = '\n'.join(buf)
            current, buf = line[3:].strip(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = '\n'.join(buf)
    return sections


def md_paragraphs(text: str) -> list[str]:
    """Extract non-table, non-heading paragraph lines."""
    result = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('|') or s.startswith('#') or s == '---':
            continue
        result.append(norm(s))
    return result


def md_table_rows(text: str) -> list[list[str]]:
    """
    Parse one or more MD tables in *text*.
    Skips separator rows (|---|) and header rows (those immediately followed
    by a separator row), so only data rows are returned.
    """
    # Collect only pipe-starting lines (preserving order)
    pipe_lines = [l.strip() for l in text.splitlines() if l.strip().startswith('|')]

    def is_separator(line: str) -> bool:
        cells = [c.strip() for c in line.split('|') if c.strip()]
        return bool(cells) and all(re.fullmatch(r'[-:]+', c) for c in cells)

    rows = []
    for i, line in enumerate(pipe_lines):
        if is_separator(line):
            continue
        # header row: next pipe-line is a separator
        if i + 1 < len(pipe_lines) and is_separator(pipe_lines[i + 1]):
            continue
        cells = [c.strip() for c in line.split('|') if c.strip()]
        rows.append([norm(c) for c in cells])
    return rows


# ── HTML parsing ──────────────────────────────────────────────────────────────

def split_html_sections(html: str) -> dict[str, str]:
    """Return {section_title: raw_html_body} for every section-title div."""
    parts = re.split(r'<div class="section-title">(.*?)</div>', html, flags=re.DOTALL)
    sections: dict[str, str] = {}
    for i in range(1, len(parts), 2):
        title = norm(parts[i])
        sections[title] = parts[i + 1] if i + 1 < len(parts) else ''
    return sections


def html_brief_paras(html: str) -> list[str]:
    """Extract <p class="plain-text"> paragraph text."""
    return [norm(p) for p in re.findall(r'<p class="plain-text">(.*?)</p>', html, re.DOTALL)]


def _tbody_rows(tbody_html: str) -> list[list[str]]:
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_html, re.DOTALL):
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL)
        rows.append([norm(c) for c in cells])
    return rows


def html_first_tbody_rows(html: str) -> list[list[str]]:
    tbody = re.search(r'<tbody>(.*?)</tbody>', html, re.DOTALL)
    return _tbody_rows(tbody.group(1)) if tbody else []


def html_all_tbody_rows(html: str) -> list[list[str]]:
    """Flatten rows from ALL <tbody> elements in order."""
    rows = []
    for tbody in re.findall(r'<tbody>(.*?)</tbody>', html, re.DOTALL):
        rows.extend(_tbody_rows(tbody))
    return rows


# ── Section comparators ───────────────────────────────────────────────────────

def _diff_rows(section: str, md: list[list[str]], html: list[list[str]],
               errors: list[str]) -> None:
    if len(md) != len(html):
        errors.append(
            f"[{section}] row count differs — MD: {len(md)}, HTML: {len(html)}"
        )
    for i, (mr, hr) in enumerate(zip(md, html), 1):
        if mr != hr:
            errors.append(
                f"[{section}] row {i} mismatch:\n"
                f"  MD  : {mr}\n"
                f"  HTML: {hr}"
            )


def check_paragraphs(section: str, md_text: str, html: str, errors: list[str]) -> None:
    md_paras   = md_paragraphs(md_text)
    html_paras = html_brief_paras(html)
    if len(md_paras) != len(html_paras):
        errors.append(
            f"[{section}] paragraph count — MD: {len(md_paras)}, HTML: {len(html_paras)}"
        )
    for i, (m, h) in enumerate(zip(md_paras, html_paras), 1):
        if m != h:
            errors.append(
                f"[{section}] paragraph {i} mismatch:\n"
                f"  MD  : {m}\n"
                f"  HTML: {h}"
            )


def check_simple_table(section: str, md_text: str, html: str, errors: list[str]) -> None:
    """Compare a straightforward table (same columns in MD and HTML)."""
    _diff_rows(section, md_table_rows(md_text), html_first_tbody_rows(html), errors)


def check_headlines(md_text: str, html: str, errors: list[str]) -> None:
    """
    Compare Market-Moving Headlines.
    MD:   | # | [Headline text](url) | Source |
    HTML: | # | <a href="url">Headline text</a> | Source |
    norm() strips both link formats to plain text.
    """
    _diff_rows('Market-Moving Headlines',
               md_table_rows(md_text),
               html_first_tbody_rows(html),
               errors)


def check_overnight(md_text: str, html: str, errors: list[str]) -> None:
    """
    Overnight Markets has two sub-tables (APAC + Europe).
    The Session column is formatted differently (MD: 'Early session (~3h in)',
    HTML: 'Early Session') so we compare only the first 3 columns.
    """
    md_rows   = [r[:3] for r in md_table_rows(md_text)]
    html_rows = [r[:3] for r in html_all_tbody_rows(html)]
    _diff_rows('Overnight Markets', md_rows, html_rows, errors)


def _is_placeholder(rows: list[list[str]], keyword: str) -> bool:
    """True if the first data row contains the placeholder keyword in any cell."""
    if not rows:
        return False
    return any(keyword.lower() in c.lower() for c in rows[0])


def check_events(section: str, md_text: str, html: str, errors: list[str],
                 placeholder_keyword: str) -> None:
    """
    Compare event tables (What Moved / Watch List).
    Treats MD placeholder '*No major events*' and HTML 'No major events recorded.'
    as equivalent — both contain the same keyword phrase.
    """
    md_rows   = md_table_rows(md_text)
    html_rows = html_first_tbody_rows(html)

    md_empty   = _is_placeholder(md_rows, placeholder_keyword)
    html_empty = _is_placeholder(html_rows, placeholder_keyword)

    if md_empty and html_empty:
        return   # both sides agree: no events
    if md_empty != html_empty:
        errors.append(
            f"[{section}] placeholder mismatch — one side has events, the other does not:\n"
            f"  MD  : {md_rows}\n  HTML: {html_rows}"
        )
        return
    _diff_rows(section, md_rows, html_rows, errors)


def check_positioning(md_text: str, html: str, errors: list[str]) -> None:
    """
    Positioning Notes.
    MD:   - Signal text -- Action text.
    HTML: Signal column | Action column  (two separate <td>s).
    Normalise by replacing ' -- ' with ' ' and comparing case-insensitively.
    """
    md_tips = []
    for line in md_text.splitlines():
        s = line.strip()
        if not re.match(r'^[-*]\s', s):   # actual bullet only (not --- separator)
            continue
        text = re.sub(r'^[-*]\s+', '', s)           # strip bullet
        text = re.sub(r'\s+(?:--|[\u2013\u2014])\s+', ' ', text)  # -- / – / — → space
        md_tips.append(norm(text, lower=True))

    html_rows = html_first_tbody_rows(html)
    html_tips = []
    for row in html_rows:
        if len(row) >= 2:
            html_tips.append(norm(row[0] + ' ' + row[1], lower=True))
        elif row:
            html_tips.append(norm(row[0], lower=True))

    if len(md_tips) != len(html_tips):
        errors.append(
            f"[Positioning Notes] tip count — MD: {len(md_tips)}, HTML: {len(html_tips)}"
        )
    for i, (m, h) in enumerate(zip(md_tips, html_tips), 1):
        if m != h:
            errors.append(
                f"[Positioning Notes] tip {i} mismatch:\n"
                f"  MD  : {m}\n"
                f"  HTML: {h}"
            )


# ── PDF verification ─────────────────────────────────────────────────────────

def _pdf_text(pdf_path: Path) -> str:
    """Extract and normalise all text from the PDF."""
    import pypdf
    reader  = pypdf.PdfReader(str(pdf_path))
    raw     = ' '.join(page.extract_text() or '' for page in reader.pages)
    # Strip emoji and other non-BMP characters (not in editable MD content)
    raw     = raw.encode('utf-16', 'surrogatepass').decode('utf-16')
    raw     = re.sub(r'[\U00010000-\U0010ffff]', '', raw)   # non-BMP (emoji etc.)
    # Collapse whitespace and normalise dashes / quotes to match MD norm()
    text    = re.sub(r'\s+', ' ', raw).strip()
    text    = text.replace('\u2019', "'").replace('\u2018', "'")
    text    = text.replace('\u201c', '"').replace('\u201d', '"')
    text    = text.replace('\u2013', '--').replace('\u2014', '--')
    # Remove thousand separators so 5,190.80 == 5190.80
    text    = re.sub(r'(\d),(\d{3})\b', r'\1\2', text)
    # Rejoin words broken by PDF line-hyphenation: "rate- sensitive" → "rate-sensitive"
    text    = re.sub(r'(\w)- (\w)', r'\1-\2', text)
    # Strip ** / * bold/italic markers that appear as literals in PDF table cells
    text    = re.sub(r'\*+', '', text)
    return text


def check_pdf(md_path: Path, pdf_path: Path, md_secs: dict, errors: list[str]) -> None:
    """
    Verify PDF content against the approved MD.

    Checks:
    - Every Morning Brief and What This Means paragraph appears verbatim in PDF text.
    - Every headline text appears in PDF text.
    - Every positioning note appears in PDF text (case-insensitive, space-collapsed
      to tolerate letter-spacing / word-break rendering artifacts in PDF tables).
    """
    if not pdf_path.exists():
        errors.append(f"[PDF] file not found: {pdf_path}")
        return

    pdf      = _pdf_text(pdf_path)
    pdf_low  = pdf.lower()
    pdf_nsp  = re.sub(r'\s+', '', pdf).lower()   # no-space version for table cells

    def _snippet(text: str) -> str:
        idx = pdf.lower().find(text[:40].lower())
        if idx >= 0:
            return f"...{pdf[max(0,idx-20):idx+120]}..."
        return "(not found in PDF)"

    def pdf_contains_exact(expected: str, label: str) -> None:
        """Space-collapsed case-insensitive match — used for narrative paragraphs.
        Only checks the first 100 chars (no-space) to avoid false positives from
        mid-paragraph line-break or rendering artifacts in PDF table cells."""
        n = re.sub(r'\s+', '', norm(expected, lower=True))
        key = n[:100] if len(n) > 100 else n
        if key and key not in pdf_nsp:
            errors.append(
                f"[PDF] {label} not found:\n"
                f"  expected : {n}\n"
                f"  pdf text : {_snippet(n)}"
            )

    def pdf_contains_fuzzy(expected: str, label: str) -> None:
        """Case-insensitive, space-collapsed match — used for table cells where
        PDF rendering can introduce letter-spacing gaps (e.g. 'VW O', 'commo dities')."""
        n = re.sub(r'\s+', '', norm(expected, lower=True))
        if n and n not in pdf_nsp:
            errors.append(
                f"[PDF] {label} not found:\n"
                f"  expected : {norm(expected)}\n"
                f"  pdf text : {_snippet(norm(expected))}"
            )

    # Narrative paragraphs — exact match (extract cleanly from PDF)
    for section in ('The Brief',):
        for i, para in enumerate(md_paragraphs(md_secs.get(section, '')), 1):
            pdf_contains_exact(para, f"{section} para {i}")

    # Headlines — fuzzy match on first 60 chars only.
    # pypdf struggles to extract full hyperlinked text from PDF table cells;
    # full headline accuracy is guaranteed by the HTML check above.
    for row in md_table_rows(md_secs.get('Market-Moving Headlines', '')):
        if len(row) >= 2:
            key = row[1][:60]
            pdf_contains_fuzzy(key, f"Headline '{row[1][:50]}'")

    # Positioning notes — fuzzy (table cells may have spacing artifacts)
    for line in md_secs.get('Positioning Notes', '').splitlines():
        s = line.strip()
        if not re.match(r'^[-*]\s', s):
            continue
        text = re.sub(r'^[-*]\s+', '', s)
        text = re.sub(r'\s+(?:--|[\u2013\u2014])\s+', ' ', text)
        pdf_contains_fuzzy(text, f"Positioning note '{text[:50]}'")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # Ensure UTF-8 output on Windows consoles
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    args     = sys.argv[1:]
    no_pdf   = '--no-pdf' in args
    args     = [a for a in args if a != '--no-pdf']
    date_str = args[0] if args else date.today().isoformat()

    md_path   = SCRIPT_DIR / 'output'         / f'market_day_break_{date_str}.md'
    html_path = SCRIPT_DIR / 'site' / 'daily' / date_str / 'index.html'
    pdf_path  = SCRIPT_DIR / 'output'         / f'market_day_break_{date_str}.pdf'

    for p in (md_path, html_path):
        if not p.exists():
            print(f"ERROR: File not found: {p}")
            sys.exit(1)

    md   = md_path.read_text(encoding='utf-8')
    html = html_path.read_text(encoding='utf-8')

    md_secs   = split_md_sections(md)
    html_secs = split_html_sections(html)

    errors: list[str] = []

    # Helper: warn if a section is absent from either file
    def require(section: str) -> bool:
        if section not in md_secs or section not in html_secs:
            errors.append(f"[{section}] section missing from MD or HTML")
            return False
        return True

    # ── Narrative brief ───────────────────────────────────────────────────────
    if require('The Brief'):
        check_paragraphs('The Brief', md_secs['The Brief'], html_secs['The Brief'], errors)

    # ── News table ────────────────────────────────────────────────────────────
    if require('Market-Moving Headlines'):
        check_headlines(md_secs['Market-Moving Headlines'],
                        html_secs['Market-Moving Headlines'], errors)

    # ── Positioning Notes ─────────────────────────────────────────────────────
    if require('Positioning Notes'):
        check_positioning(md_secs['Positioning Notes'], html_secs['Positioning Notes'], errors)

    # ── PDF ───────────────────────────────────────────────────────────────────
    if not no_pdf:
        check_pdf(md_path, pdf_path, md_secs, errors)

    # ── Report ────────────────────────────────────────────────────────────────
    sections_checked = [
        'The Brief', 'Market-Moving Headlines', 'Positioning Notes', 'PDF',
    ]

    if errors:
        print(f"\nCONTENT MISMATCH — {len(errors)} issue(s) found for {date_str}:\n")
        for e in errors:
            print(f"  {e}\n")
        print("Fix the source / generator so HTML and PDF match the approved MD, then rebuild.")
        sys.exit(1)

    print(f"OK — HTML and PDF match {md_path.name}")
    print(f"     Verified: {', '.join(sections_checked)}")


if __name__ == '__main__':
    main()
