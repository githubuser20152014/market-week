#!/usr/bin/env python3
"""
send_welcome.py — Send a welcome email to a new subscriber.

Usage:
    python send_welcome.py --email new@subscriber.com [--dry-run]
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR / "config"

SUBJECT = "Welcome to Framework Foundry"


def main():
    parser = argparse.ArgumentParser(description="Send a welcome email to a new subscriber.")
    parser.add_argument("--email", required=True, help="Recipient email address")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print subject and recipient without sending.")
    args = parser.parse_args()

    env_file = CONFIG_DIR / "api_keys.env"
    if env_file.exists():
        load_dotenv(env_file)

    gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")

    if args.dry_run:
        print(f"Subject   : {SUBJECT}")
        print(f"Recipient : {args.email}")
        print("DRY RUN — no email sent.")
        return

    if not gmail_addr or gmail_addr.startswith("your_"):
        print("ERROR: GMAIL_ADDRESS is not set in config/api_keys.env", file=sys.stderr)
        sys.exit(1)
    if not gmail_pass or gmail_pass.startswith("your_"):
        print("ERROR: GMAIL_APP_PASSWORD is not set in config/api_keys.env", file=sys.stderr)
        sys.exit(1)

    try:
        from data.email_sender import send_welcome_email
    except ImportError as exc:
        print(f"ERROR: Could not import email_sender — {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"==> Sending welcome email to {args.email} ...")
    send_welcome_email(args.email, gmail_addr, gmail_pass)
    print("Done.")


if __name__ == "__main__":
    main()
