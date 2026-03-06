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
