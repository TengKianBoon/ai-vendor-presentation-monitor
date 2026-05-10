from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_gmail(subject: str, text_body: str, html_body: str) -> None:
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("DIGEST_TO_EMAIL")
    sender_name = os.environ.get("DIGEST_FROM_NAME") or "AI Vendor Monitor"
    if not user or not password or not recipient:
        raise RuntimeError("Missing GMAIL_USER, GMAIL_APP_PASSWORD, or DIGEST_TO_EMAIL")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{sender_name} <{user}>"
    message["To"] = recipient
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(message)
