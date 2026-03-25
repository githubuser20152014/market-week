#!/usr/bin/env python3
"""
send_email.py — Send a newsletter edition to all subscribers.

Usage:
    python send_email.py --edition daybreak --date 2026-03-06 [--dry-run]
    python send_email.py --edition weekly   --date 2026-03-06 [--dry-run]
    python send_email.py --edition intl     --date 2026-03-06 [--dry-run]
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR / "config"
OUTPUT_DIR = SCRIPT_DIR / "output"

FORM_ID = "mwpvyoal"

# ---------------------------------------------------------------------------
# Subject templates
# ---------------------------------------------------------------------------
SUBJECTS = {
    "daybreak":  "The Morning Brief — {date}",
    "weekly":    "Framework Foundry Weekly (US Edition) — {date}",
    "intl":      "Framework Foundry Weekly (Intl Edition) — {date}",
    "blueprint": "The Blueprint — {title} — {date}",
}

SUBSCRIPTION_NAMES = {
    "daybreak":  "Framework Foundry Daily (The Morning Brief)",
    "weekly":    "Framework Foundry Weekly",
    "intl":      "Framework Foundry Weekly",
    "blueprint": "Framework Foundry (The Blueprint)",
}

BLUEPRINT_CTA = (
    "Found this useful? Forward it to someone who's been meaning to get their 401(k) sorted. "
    'They can subscribe at <a href="https://frameworkfoundry.info" style="color:#4a7fb5;">frameworkfoundry.info</a>.'
)


def resolve_md_path(edition: str, date_str: str) -> Path:
    if edition == "daybreak":
        return OUTPUT_DIR / f"market_day_break_{date_str}.md"
    if edition == "intl":
        return OUTPUT_DIR / f"intl_newsletter_{date_str}.md"
    if edition == "blueprint":
        return OUTPUT_DIR / f"blueprint_{date_str}.md"
    return OUTPUT_DIR / f"newsletter_{date_str}.md"


def main():
    parser = argparse.ArgumentParser(description="Send newsletter to subscribers.")
    parser.add_argument("--edition", choices=["daybreak", "weekly", "intl", "blueprint"], required=True)
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print subscriber list and subject without sending.")
    parser.add_argument("--save-preview", action="store_true",
                        help="Build and save the email HTML to output/email_preview_DATE.html without sending.")
    parser.add_argument("--md", dest="md_override",
                        help="Override the Markdown file path (default: resolved from edition + date).")
    parser.add_argument("--subject", dest="subject_override",
                        help="Override the email subject line.")
    parser.add_argument("--to", dest="to_override",
                        help="Send to a single address only (for test sends).")
    args = parser.parse_args()

    # Load env
    env_file = CONFIG_DIR / "api_keys.env"
    if env_file.exists():
        load_dotenv(env_file)

    formspree_key = os.environ.get("FORMSPREE_API_KEY", "")
    gmail_addr    = os.environ.get("GMAIL_ADDRESS", "")
    gmail_pass    = os.environ.get("GMAIL_APP_PASSWORD", "")

    # For daybreak and blueprint, use the title saved during generation if available
    if args.subject_override:
        subject = args.subject_override
    elif args.edition == "daybreak":
        title_path = OUTPUT_DIR / f"title_{args.date}.txt"
        if title_path.exists():
            subject = f"The Morning Brief — {title_path.read_text(encoding='utf-8').strip()}"
        else:
            subject = SUBJECTS[args.edition].format(date=args.date)
    elif args.edition == "blueprint":
        title_path = OUTPUT_DIR / f"title_blueprint_{args.date}.txt"
        title = title_path.read_text(encoding="utf-8").strip() if title_path.exists() else args.date
        subject = SUBJECTS["blueprint"].format(title=title, date=args.date)
    else:
        subject = SUBJECTS[args.edition].format(date=args.date)
    md_path = Path(args.md_override) if args.md_override else resolve_md_path(args.edition, args.date)

    if not md_path.exists():
        print(f"ERROR: Newsletter file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    md_content = md_path.read_text(encoding="utf-8")

    # Import here so missing deps surface with a clear message
    try:
        from data.email_sender import build_email_html, send_to_all
    except ImportError as exc:
        print(f"ERROR: Could not import email_sender — {exc}", file=sys.stderr)
        print("Run: pip install markdown", file=sys.stderr)
        sys.exit(1)

    # Load subscribers from local file
    subscribers_file = CONFIG_DIR / "subscribers.txt"
    if not subscribers_file.exists():
        print(f"ERROR: Subscriber file not found: {subscribers_file}", file=sys.stderr)
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
        print(f"==> Loaded {len(subscribers)} subscriber(s) from {subscribers_file.name}.")

    if args.dry_run:
        print("\n-- DRY RUN --")
        print(f"Subject : {subject}")
        print(f"File    : {md_path}")
        print(f"Subscribers ({len(subscribers)}):")
        for addr in subscribers:
            print(f"  {addr}")
        return

    # Build email HTML
    html_body = build_email_html(
        md_content, subject, SUBSCRIPTION_NAMES[args.edition],
        date_str=args.date if args.edition == "daybreak" else "",
        edition_label="The Blueprint · Wednesday" if args.edition == "blueprint" else "",
        cta_text=BLUEPRINT_CTA if args.edition == "blueprint" else "",
    )

    if args.save_preview:
        preview_path = OUTPUT_DIR / f"email_preview_{args.date}.html"
        preview_path.write_text(html_body, encoding="utf-8")
        print(f"Email preview saved -> {preview_path}")
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

    plain_body = md_content  # plain-text fallback: raw Markdown is readable

    print(f"==> Sending '{subject}' to {len(subscribers)} subscriber(s) ...")
    sent, failed = send_to_all(gmail_addr, gmail_pass, subscribers, subject, html_body, plain_body)

    print(f"\nDone. Sent: {sent}  Failed: {len(failed)}")
    if failed:
        print("Failed addresses:")
        for addr in failed:
            print(f"  {addr}")


if __name__ == "__main__":
    main()
