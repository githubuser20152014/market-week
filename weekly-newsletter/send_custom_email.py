#!/usr/bin/env python3
"""
send_custom_email.py — Send a one-off email to all subscribers.

Usage:
    python send_custom_email.py --subject "..." --message path/to/message.md [--dry-run]

The message file is plain Markdown. It is rendered to HTML using the same
template as the regular newsletter, so formatting (bold, links, lists) works.

Examples:
    python send_custom_email.py --subject "Quick check-in from Framework Foundry" \\
                                --message messages/friday_followup.md --dry-run
    python send_custom_email.py --subject "Quick check-in from Framework Foundry" \\
                                --message messages/friday_followup.md
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR / "config"


def main():
    parser = argparse.ArgumentParser(description="Send a one-off email to all subscribers.")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--message", required=True, help="Path to Markdown message file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print subscriber list and subject without sending.")
    parser.add_argument("--to", metavar="EMAIL",
                        help="Send to this address only (overrides subscribers.txt).")
    args = parser.parse_args()

    # Load credentials
    env_file = CONFIG_DIR / "api_keys.env"
    if env_file.exists():
        load_dotenv(env_file)

    gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")

    # Read message file
    msg_path = Path(args.message)
    if not msg_path.is_absolute():
        msg_path = SCRIPT_DIR / msg_path
    if not msg_path.exists():
        print(f"ERROR: Message file not found: {msg_path}", file=sys.stderr)
        sys.exit(1)

    md_content = msg_path.read_text(encoding="utf-8")

    # Load subscribers
    subscribers_file = CONFIG_DIR / "subscribers.txt"
    if not args.to and not subscribers_file.exists():
        print(f"ERROR: Subscriber file not found: {subscribers_file}", file=sys.stderr)
        sys.exit(1)

    if args.to:
        subscribers = [args.to]
        print(f"==> Sending to single address: {args.to} (--to override).")
    else:
        subscribers = [
            line.strip()
            for line in subscribers_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        print(f"==> Loaded {len(subscribers)} subscriber(s) from {subscribers_file.name}.")

    if args.dry_run:
        print("\n-- DRY RUN --")
        print(f"Subject : {args.subject}")
        print(f"Message : {msg_path}")
        print(f"Subscribers ({len(subscribers)}):")
        for addr in subscribers:
            print(f"  {addr}")
        print("\n-- MESSAGE PREVIEW --")
        print(md_content)
        return

    # Validate credentials
    if not gmail_addr or gmail_addr.startswith("your_"):
        print("ERROR: GMAIL_ADDRESS is not set in config/api_keys.env", file=sys.stderr)
        sys.exit(1)
    if not gmail_pass or gmail_pass.startswith("your_"):
        print("ERROR: GMAIL_APP_PASSWORD is not set in config/api_keys.env", file=sys.stderr)
        sys.exit(1)

    try:
        from data.email_sender import build_email_html, send_to_all
    except ImportError as exc:
        print(f"ERROR: Could not import email_sender — {exc}", file=sys.stderr)
        print("Run: pip install markdown", file=sys.stderr)
        sys.exit(1)

    html_body  = build_email_html(md_content, args.subject)
    plain_body = md_content

    print(f"==> Sending '{args.subject}' to {len(subscribers)} subscriber(s) ...")
    sent, failed = send_to_all(gmail_addr, gmail_pass, subscribers, args.subject, html_body, plain_body)

    print(f"\nDone. Sent: {sent}  Failed: {len(failed)}")
    if failed:
        print("Failed addresses:")
        for addr in failed:
            print(f"  {addr}")


if __name__ == "__main__":
    main()
