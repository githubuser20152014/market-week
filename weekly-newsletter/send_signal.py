#!/usr/bin/env python3
"""
send_signal.py — Send The Signal (news digest) to subscribers.

Usage:
    python send_signal.py --date 2026-03-22 [--dry-run]
    python send_signal.py --date 2026-03-22 --save-preview
    python send_signal.py --date 2026-03-22 --to test@example.com
    python send_signal.py --md /path/to/digest.md --date 2026-03-22
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent
CONFIG_DIR   = SCRIPT_DIR / "config"
OUTPUT_DIR   = SCRIPT_DIR / "output"
DIGEST_DIR   = Path("C:/Users/Akhil/Documents/ContentRepo/07-Reading/news-digest")

SUBSCRIPTION_NAME = "Framework Foundry — The Signal"
EDITION_LABEL     = "THE SIGNAL"


def resolve_digest_path(date_str: str | None) -> Path:
    """Find the digest .md file for a given date, or the most recent one."""
    if date_str:
        candidate = DIGEST_DIR / f"{date_str}-digest.md"
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"No digest found for {date_str}: {candidate}")

    # Auto-detect: latest file in the digest directory
    digests = sorted(DIGEST_DIR.glob("*-digest.md"))
    if not digests:
        raise FileNotFoundError(f"No digest files found in {DIGEST_DIR}")
    return digests[-1]


def main():
    parser = argparse.ArgumentParser(description="Send The Signal digest to subscribers.")
    parser.add_argument("--date", help="YYYY-MM-DD (used to find the digest and name the preview)")
    parser.add_argument("--md", dest="md_override",
                        help="Override the Markdown file path.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print subscriber list and subject without sending.")
    parser.add_argument("--save-preview", action="store_true",
                        help="Build and save the email HTML to output/signal_preview_DATE.html without sending.")
    parser.add_argument("--to", dest="to_override",
                        help="Send to a single address only (for test sends).")
    args = parser.parse_args()

    # Load env
    env_file = CONFIG_DIR / "api_keys.env"
    if env_file.exists():
        load_dotenv(env_file)

    gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")

    # Resolve digest path
    try:
        md_path = Path(args.md_override) if args.md_override else resolve_digest_path(args.date)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if not md_path.exists():
        print(f"ERROR: Digest file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    # Extract date from filename if not provided (e.g. "2026-03-22-digest.md" → "2026-03-22")
    date_str = args.date or md_path.stem.replace("-digest", "")

    # Format readable date for subject (e.g. "March 22, 2026")
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        readable_date = f"{dt.strftime('%B')} {dt.day}, {dt.year}"
    except Exception:
        readable_date = date_str

    subject = f"The Signal: News that matters — {readable_date}"
    md_content = md_path.read_text(encoding="utf-8")

    # Import email utilities
    try:
        from data.email_sender import build_email_html, send_to_all
    except ImportError as exc:
        print(f"ERROR: Could not import email_sender — {exc}", file=sys.stderr)
        print("Run: pip install markdown", file=sys.stderr)
        sys.exit(1)

    # Load Signal subscribers
    subscribers_file = CONFIG_DIR / "signal_subscribers.txt"
    if not subscribers_file.exists():
        print(f"ERROR: Signal subscriber file not found: {subscribers_file}", file=sys.stderr)
        print(f"Create {subscribers_file} with one email address per line.", file=sys.stderr)
        sys.exit(1)

    if args.to_override:
        subscribers = [args.to_override]
        print(f"==> Test send — single recipient: {args.to_override}")
    else:
        subscribers = [
            line.strip()
            for line in subscribers_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        print(f"==> Loaded {len(subscribers)} Signal subscriber(s) from {subscribers_file.name}.")

    if args.dry_run:
        print("\n-- DRY RUN --")
        print(f"Subject    : {subject}")
        print(f"File       : {md_path}")
        print(f"Subscribers ({len(subscribers)}):")
        for addr in subscribers:
            print(f"  {addr}")
        return

    # Build HTML
    html_body = build_email_html(
        md_content,
        subject,
        subscription_name=SUBSCRIPTION_NAME,
        edition_label=EDITION_LABEL,
    )

    if args.save_preview:
        preview_path = OUTPUT_DIR / f"signal_preview_{date_str}.html"
        preview_path.write_text(html_body, encoding="utf-8")
        print(f"Signal preview saved -> {preview_path}")
        print(f"Subject : {subject}")
        print(f"To      : {len(subscribers)} subscriber(s)")
        print("Open the preview file in a browser to review before sending.")
        return

    if not gmail_addr or gmail_addr.startswith("your_"):
        print("ERROR: GMAIL_ADDRESS is not set in config/api_keys.env", file=sys.stderr)
        sys.exit(1)
    if not gmail_pass or gmail_pass.startswith("your_"):
        print("ERROR: GMAIL_APP_PASSWORD is not set in config/api_keys.env", file=sys.stderr)
        sys.exit(1)

    plain_body = md_content  # raw Markdown is a readable plain-text fallback

    print(f"==> Sending '{subject}' to {len(subscribers)} subscriber(s) ...")
    sent, failed = send_to_all(gmail_addr, gmail_pass, subscribers, subject, html_body, plain_body)

    print(f"\nDone. Sent: {sent}  Failed: {len(failed)}")
    if failed:
        print("Failed addresses:")
        for addr in failed:
            print(f"  {addr}")


if __name__ == "__main__":
    main()
