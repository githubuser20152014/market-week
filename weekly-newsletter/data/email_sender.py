"""
email_sender.py — Utilities for fetching subscribers and sending newsletter emails.
"""

import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import markdown as md


FORMSPREE_API_BASE = "https://api.formspree.io/forms"


def fetch_subscribers(api_key: str, form_id: str) -> list[str]:
    """
    Fetch unique subscriber emails from a Formspree form.

    Requires a Formspree paid plan — free tier returns 403.
    Returns a list of unique email strings.
    """
    url = f"{FORMSPREE_API_BASE}/{form_id}/submissions"
    headers = {"Authorization": f"Bearer {api_key}"}

    resp = requests.get(url, headers=headers, timeout=15)

    if resp.status_code == 403:
        raise PermissionError(
            "Formspree returned 403. The submissions API requires a paid plan. "
            "Check your plan at formspree.io or export a CSV from the dashboard."
        )
    resp.raise_for_status()

    data = resp.json()
    submissions = data.get("submissions", [])

    seen = set()
    emails = []
    for sub in submissions:
        email = sub.get("email") or sub.get("_values", {}).get("email")
        if email and email not in seen:
            seen.add(email)
            emails.append(email)

    return emails


def build_email_html(md_content: str, subject: str, subscription_name: str = "Framework Foundry Weekly") -> str:
    """Convert Markdown content to a minimal inline-styled HTML email."""
    body_html = md.markdown(md_content, extensions=["tables"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Georgia,serif;">
  <div style="max-width:680px;margin:32px auto;background:#ffffff;border-radius:6px;
              overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

    <div style="padding:32px 40px 24px;">
      {body_html}
    </div>

    <div style="padding:20px 40px;background:#f9f9f9;border-top:1px solid #e8e8e8;
                font-size:13px;color:#888;font-family:Arial,sans-serif;text-align:center;">
      <p style="margin:0 0 6px;">
        Read the latest edition online at
        <a href="https://frameworkfoundry.info" style="color:#555;">frameworkfoundry.info</a>
      </p>
      <p style="margin:0;">
        You received this because you subscribed to {subscription_name}.
        To unsubscribe, reply with "unsubscribe" in the subject line.
      </p>
    </div>
  </div>
</body>
</html>"""


def send_email(
    gmail_address: str,
    app_password: str,
    to_addr: str,
    subject: str,
    html_body: str,
    plain_body: str,
) -> None:
    """Send a single email via Gmail SMTP with STARTTLS."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Framework Foundry <{gmail_address}>"
    msg["To"] = to_addr

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, to_addr, msg.as_string())


def build_welcome_html(to_addr: str) -> str:
    """Build a welcome HTML email for a new subscriber."""
    subject = "Welcome to Framework Foundry"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Georgia,serif;">
  <div style="max-width:680px;margin:32px auto;background:#ffffff;border-radius:6px;
              overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

    <div style="padding:32px 40px 24px;">
      <h1 style="margin:0 0 24px;font-size:24px;color:#1a1a1a;font-family:Georgia,serif;">
        You're in. Welcome to Framework Foundry!
      </h1>
      <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:#333;">
        We're really glad you're here. Framework Foundry is built for investors who want
        to understand <em>why</em> the market is moving — not just what it did. Every week,
        we cut through the noise and hand you a clear, confident read on macro conditions,
        major indices, and what it means for your portfolio.
      </p>
      <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:#333;">
        Here's what's coming your way:
      </p>
      <ul style="margin:0 0 16px;padding-left:24px;font-size:16px;line-height:1.9;color:#333;">
        <li><strong>Weekly US Edition</strong> — indices, macro recap, and positioning tips, every weekend</li>
        <li><strong>Weekly International Edition</strong> — Nikkei, FTSE, ECB, and global macro in focus</li>
        <li><strong>Market Day Break</strong> — sharp pre-market briefs on the days that matter most</li>
      </ul>
      <p style="margin:0 0 28px;font-size:16px;line-height:1.7;color:#333;">
        The latest edition is live right now — dive in!
      </p>
      <p style="margin:0 0 0;">
        <a href="https://frameworkfoundry.info"
           style="display:inline-block;padding:12px 24px;background:#1a1a1a;color:#ffffff;
                  text-decoration:none;border-radius:4px;font-family:Arial,sans-serif;
                  font-size:15px;font-weight:bold;">
          Read the Latest Edition →
        </a>
      </p>
    </div>

    <div style="padding:20px 40px;background:#f9f9f9;border-top:1px solid #e8e8e8;
                font-size:13px;color:#888;font-family:Arial,sans-serif;text-align:center;">
      <p style="margin:0 0 6px;">
        Read the latest edition online at
        <a href="https://frameworkfoundry.info" style="color:#555;">frameworkfoundry.info</a>
      </p>
      <p style="margin:0;">
        You received this because you subscribed to Framework Foundry Weekly.
        To unsubscribe, reply with "unsubscribe" in the subject line.
      </p>
    </div>
  </div>
</body>
</html>"""


def send_welcome_email(to_addr: str, gmail_address: str, app_password: str) -> None:
    """Send a welcome email to a new subscriber."""
    subject = "Welcome to Framework Foundry"
    html_body = build_welcome_html(to_addr)
    plain_body = (
        "You're in. Welcome to Framework Foundry!\n\n"
        "We're really glad you're here. Framework Foundry is built for investors who want\n"
        "to understand why the market is moving — not just what it did. Every week, we cut\n"
        "through the noise and hand you a clear, confident read on macro conditions, major\n"
        "indices, and what it means for your portfolio.\n\n"
        "Here's what's coming your way:\n"
        "- Weekly US Edition: indices, macro recap, and positioning tips, every weekend\n"
        "- Weekly International Edition: Nikkei, FTSE, ECB, and global macro in focus\n"
        "- Market Day Break: sharp pre-market briefs on the days that matter most\n\n"
        "The latest edition is live right now — dive in: https://frameworkfoundry.info\n\n"
        "To unsubscribe, reply with \"unsubscribe\" in the subject line."
    )
    send_email(gmail_address, app_password, to_addr, subject, html_body, plain_body)


def send_to_all(
    gmail_address: str,
    app_password: str,
    subscribers: list[str],
    subject: str,
    html_body: str,
    plain_body: str,
) -> tuple[int, list[str]]:
    """
    Send email to every subscriber. Returns (sent_count, failed_list).
    Per-address exceptions are caught and logged — one failure won't abort the rest.
    """
    sent = 0
    failed = []

    for addr in subscribers:
        try:
            send_email(gmail_address, app_password, addr, subject, html_body, plain_body)
            sent += 1
        except Exception as exc:
            print(f"  [FAILED] {addr}: {exc}")
            failed.append(addr)

    return sent, failed
