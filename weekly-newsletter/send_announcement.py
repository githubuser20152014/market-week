#!/usr/bin/env python3
"""
send_announcement.py — Send the site relaunch announcement email.

Usage:
    python send_announcement.py --to addr@example.com [--dry-run]
    python send_announcement.py  # sends to all subscribers in config/subscribers.txt
"""

import argparse
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from data.email_sender import build_email_html, send_email, send_to_all

SUBJECT = "Framework Foundry: We rebuilt the site — and it's worth a look"
ANNOUNCEMENT_MD = BASE_DIR / "messages" / "site_launch_announcement.md"
SUBSCRIBERS_FILE = BASE_DIR / "config" / "subscribers.txt"
ENV_FILE = BASE_DIR / "config" / "api_keys.env"


def extract_email_body(md_path: Path) -> str:
    """Extract the Email/Subscriber version body from the announcement file.

    Strips the subject line and section headers; returns clean Markdown body.
    """
    text = md_path.read_text(encoding="utf-8")

    # Grab content between '## Email / Subscriber version' and the next '---'
    match = re.search(
        r"## Email / Subscriber version\s*\n(.*?)(?=\n---)",
        text,
        re.DOTALL,
    )
    if not match:
        sys.exit("ERROR: could not find '## Email / Subscriber version' section")

    body = match.group(1).strip()

    # Remove the bold subject line (first line: **Subject: ...**)
    body = re.sub(r"^\*\*Subject:.*?\*\*\s*\n", "", body).strip()

    return body


def html_to_plain(html: str) -> str:
    plain = re.sub(r"<[^>]+>", "", html)
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    return plain.strip()


def load_creds():
    load_dotenv(ENV_FILE)
    gmail = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail or not password:
        sys.exit("ERROR: GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set in config/api_keys.env")
    return gmail, password


def load_subscribers() -> list[str]:
    if not SUBSCRIBERS_FILE.exists():
        sys.exit(f"ERROR: {SUBSCRIBERS_FILE} not found")
    lines = SUBSCRIBERS_FILE.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def main():
    parser = argparse.ArgumentParser(description="Send the site relaunch announcement email")
    parser.add_argument("--to", nargs="+", metavar="EMAIL", help="Specific recipient(s)")
    parser.add_argument("--dry-run", action="store_true", help="Print email body; do not send")
    args = parser.parse_args()

    recipients = args.to if args.to else load_subscribers()

    md_body = extract_email_body(ANNOUNCEMENT_MD)
    html_body = build_email_html(md_body, SUBJECT, edition_label="Site Update")
    plain_body = html_to_plain(html_body)

    if args.dry_run:
        print(f"Subject : {SUBJECT}")
        print(f"To      : {', '.join(recipients)}")
        print("-" * 60)
        print(md_body)
        return

    gmail, password = load_creds()

    if len(recipients) == 1:
        print(f"Sending to {recipients[0]} …")
        send_email(gmail, password, recipients[0], SUBJECT, html_body, plain_body)
        print("Done.")
    else:
        print(f"Sending to {len(recipients)} recipient(s) …")
        sent, failed = send_to_all(gmail, password, recipients, SUBJECT, html_body, plain_body)
        print(f"Sent: {sent}  Failed: {len(failed)}")
        if failed:
            print("Failed addresses:")
            for addr in failed:
                print(f"  {addr}")


if __name__ == "__main__":
    main()
