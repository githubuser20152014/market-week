"""
send_welcome.py — Send the welcome email to new subscribers.

Usage:
    python send_welcome.py --to addr1@example.com addr2@example.com
    python send_welcome.py --dry-run --to addr1@example.com
    python send_welcome.py  # sends to all subscribers in config/subscribers.txt
"""

import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running from repo root or from weekly-newsletter/
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from data.email_sender import send_email, send_to_all

SUBJECT = "Welcome to Framework Foundry"
WELCOME_HTML = BASE_DIR / "output" / "welcome_preview.html"
SUBSCRIBERS_FILE = BASE_DIR / "config" / "subscribers.txt"
ENV_FILE = BASE_DIR / "config" / "api_keys.env"


def load_creds():
    load_dotenv(ENV_FILE)
    gmail = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail or not password:
        sys.exit("ERROR: GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set in config/api_keys.env")
    return gmail, password


def load_html() -> str:
    if not WELCOME_HTML.exists():
        sys.exit(f"ERROR: {WELCOME_HTML} not found")
    return WELCOME_HTML.read_text(encoding="utf-8")


def html_to_plain(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_subscribers() -> list[str]:
    if not SUBSCRIBERS_FILE.exists():
        sys.exit(f"ERROR: {SUBSCRIBERS_FILE} not found")
    lines = SUBSCRIBERS_FILE.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def main():
    parser = argparse.ArgumentParser(description="Send welcome email to new subscribers")
    parser.add_argument("--to", nargs="+", metavar="EMAIL", help="Specific recipient(s)")
    parser.add_argument("--dry-run", action="store_true", help="Print recipients; do not send")
    args = parser.parse_args()

    recipients = args.to if args.to else load_subscribers()

    if args.dry_run:
        print(f"DRY RUN — would send '{SUBJECT}' to:")
        for addr in recipients:
            print(f"  {addr}")
        return

    gmail, password = load_creds()
    html_body = load_html()
    plain_body = html_to_plain(html_body)

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
