import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM") or SMTP_USER


def _is_email_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD and EMAIL_FROM)


def _send_email_sync(to_email: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
    """
    Synchronous email sender using standard SMTP (e.g. Gmail).

    This is executed in a thread via `send_email_async` so it does not
    block the event loop.
    """
    if not _is_email_configured():
        # Soft-fail if SMTP is not configured; backend continues to work.
        print("⚠️ SMTP not configured – skipping email send")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    if body_text:
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

    return True


async def send_email_async(to_email: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
    """
    Asynchronous wrapper around `_send_email_sync` to keep API routes non-blocking.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _send_email_sync,
        to_email,
        subject,
        body_html,
        body_text,
    )

