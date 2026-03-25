#!/usr/bin/env python3
"""
generate_blueprint.py — Prepare a Blueprint article for email distribution.

Usage:
    python generate_blueprint.py --date 2026-03-26
    python generate_blueprint.py --date 2026-03-26 --source path/to/article.md

Reads a Blueprint issue from ContentRepo/wednesday-series/Issues/, strips YAML
frontmatter, adds an email wrapper, and writes two output files:

    output/blueprint_YYYY-MM-DD.md       — send-ready markdown
    output/title_blueprint_YYYY-MM-DD.txt — article title for send_email.py subject
"""

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent
OUTPUT_DIR   = SCRIPT_DIR / "output"
CONTENT_REPO = Path("C:/Users/Akhil/Documents/ContentRepo")
ISSUES_DIR   = CONTENT_REPO / "wednesday-series/Issues"

BASE_URL = "https://frameworkfoundry.info"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Split YAML frontmatter from body.
    Returns (meta_dict, body_text). If no frontmatter, meta_dict is empty.
    """
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
    """Scan Issues/ for a markdown file whose frontmatter date matches date_str."""
    for md_file in ISSUES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        if meta.get("date") == date_str:
            return md_file
    return None


def build_email_markdown(meta: dict, body: str) -> str:
    """Wrap article body in email-appropriate header/footer."""
    issue_num = meta.get("issue", "")
    url       = meta.get("url", "")

    issue_line = f"*The Blueprint · Issue #{issue_num} · Every Wednesday*" if issue_num else "*The Blueprint · Every Wednesday*"
    read_online = f"\n\n---\n\n*Read this issue online: [{BASE_URL}{url}]({BASE_URL}{url})*" if url else ""

    return f"{issue_line}\n\n---\n\n{body.rstrip()}{read_online}\n"


def main():
    parser = argparse.ArgumentParser(description="Generate Blueprint email markdown.")
    parser.add_argument("--date", required=True, help="Issue date YYYY-MM-DD")
    parser.add_argument("--source", help="Override article file path")
    args = parser.parse_args()

    # Resolve source file
    if args.source:
        source_path = Path(args.source)
    else:
        source_path = find_article_by_date(args.date)

    if source_path is None or not source_path.exists():
        print(f"ERROR: No Blueprint article found for date {args.date} in {ISSUES_DIR}", file=sys.stderr)
        print("Use --source to specify the file path directly.", file=sys.stderr)
        sys.exit(1)

    raw = source_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)

    title = meta.get("title", f"The Blueprint — {args.date}")

    email_md = build_email_markdown(meta, body)

    OUTPUT_DIR.mkdir(exist_ok=True)

    md_out    = OUTPUT_DIR / f"blueprint_{args.date}.md"
    title_out = OUTPUT_DIR / f"title_blueprint_{args.date}.txt"

    md_out.write_text(email_md, encoding="utf-8")
    title_out.write_text(title, encoding="utf-8")

    print(f"Article  : {source_path.name}")
    print(f"Title    : {title}")
    print(f"Output   : {md_out}")
    print(f"Title txt: {title_out}")
    print(f"\nReady to send:")
    print(f"  python send_email.py --edition blueprint --date {args.date} --save-preview")
    print(f"  python send_email.py --edition blueprint --date {args.date}")


if __name__ == "__main__":
    main()
