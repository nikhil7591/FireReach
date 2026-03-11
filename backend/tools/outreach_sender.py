import json
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

from groq import Groq
from config import (
    get_groq_api_key,
    get_groq_model,
    get_resend_api_key,
    get_sender_email,
    get_smtp_user,
    get_smtp_pass,
)

logger = logging.getLogger(__name__)

EMAIL_PROMPT = """
You are an expert B2B copywriter for Rabbitt AI. Write a cold outreach email.

TARGET:
  Company: {company_name}
  Recipient Email: {recipient_email}

ACCOUNT BRIEF (key analysis — use this to personalize):
{account_brief}

KEY SIGNALS FOUND (SPECIFIC data — reference at least 2 of these):
{key_signals}

ICP CONTEXT (what we sell):
{icp}

STRICT RULES:
1. Subject line MUST reference a SPECIFIC signal (funding amount, hiring surge, new leader's name, etc.)
2. Opening sentence MUST prove research was done — name a specific finding immediately
3. Under 150 words total (subject + body)
4. Sound like a real human — conversational, NOT corporate robot
5. Soft CTA: suggest a quick 15-minute chat, do NOT use "I wanted to reach out" or "Hope this email finds you"
6. Sign off as: Alex from Rabbitt AI
7. ZERO TEMPLATE: every sentence must be unique to {company_name}
8. Body should have 3 short paragraphs: (1) hook with signal, (2) value prop, (3) CTA

Respond ONLY with valid JSON — no markdown fences, no extra text:
{{
  "subject": "<subject line referencing a specific signal>",
  "body": "<full email body — plain text, use \\n for line breaks>"
}}
"""


def _extract_json(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object in model response.")
    return json.loads(raw[start:end])


def _signals_to_bullets(signals: dict) -> str:
    result = []
    for cat, findings in signals.get("signals", {}).items():
        for f in findings[:2]:
            result.append(f"• [{cat.upper()}] {f.get('finding', '')}")
    return "\n".join(result) if result else "No specific signals available."


def _generate_email(
    recipient_email: str,
    company_name: str,
    account_brief: str,
    key_signals_identified: list,
    icp: str,
    signals: dict,
) -> dict:
    try:
        client = Groq(api_key=get_groq_api_key())
    except Exception as exc:
        logger.error("Groq config failed for email generation: %s", exc)
        return _fallback_email(company_name, recipient_email)

    signals_bullets = _signals_to_bullets(signals or {})
    key_signals_str = "\n".join(f"• {s}" for s in (key_signals_identified or []))

    prompt = EMAIL_PROMPT.format(
        company_name=company_name,
        recipient_email=recipient_email,
        account_brief=account_brief,
        key_signals=key_signals_str or signals_bullets,
        icp=icp,
    )

    try:
        response = client.chat.completions.create(
            model=get_groq_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )
        raw = response.choices[0].message.content or ""
    except Exception as exc:
        logger.error("Groq email generation failed: %s", exc)
        return _fallback_email(company_name, recipient_email)

    try:
        return _extract_json(raw)
    except Exception as exc:
        logger.warning("JSON parse failed: %s — using raw text fallback", exc)
        return _fallback_email(company_name, recipient_email)


def _fallback_email(company_name: str, recipient_email: str) -> dict:
    return {
        "subject": f"Quick thought on {company_name}'s growth trajectory",
        "body": (
            f"Hey,\n\n"
            f"Noticed {company_name} has been making some significant moves lately. "
            "Given your current growth phase, I thought our work at Rabbitt AI might be relevant.\n\n"
            "We help companies like yours build structured, scalable programmes that remove friction "
            "as you scale. Happy to share a specific example that might resonate.\n\n"
            "Worth a 15-minute call this week?\n\n"
            "Alex from Rabbitt AI"
        ),
    }


def _send_via_resend(
    sender: str, recipient: str, subject: str, body: str
) -> dict:
    try:
        import resend  # type: ignore

        resend.api_key = get_resend_api_key()
        params = {
            "from": sender,
            "to": [recipient],
            "subject": subject,
            "text": body,
        }
        response = resend.Emails.send(params)
        return {
            "method": "resend",
            "success": True,
            "details": str(response),
        }
    except Exception as exc:
        logger.warning("Resend failed: %s", exc)
        return {"method": "resend", "success": False, "details": str(exc)}


def _send_via_smtp(
    sender: str, recipient: str, subject: str, body: str
) -> dict:
    smtp_user = get_smtp_user()
    smtp_pass = get_smtp_pass()
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = recipient
        msg.attach(MIMEText(body, "plain"))

        logger.info("Connecting to smtp.gmail.com:465 as %s", smtp_user)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [recipient], msg.as_string())

        logger.info("Email sent successfully to %s", recipient)
        return {"method": "smtp_gmail", "success": True, "details": f"Sent from {sender} to {recipient}"}
    except smtplib.SMTPAuthenticationError as exc:
        msg_txt = ("Gmail authentication failed. Make sure you are using an App Password "
                   "(not your regular Gmail password). Go to myaccount.google.com → Security → App Passwords.")
        logger.error("SMTP Auth Error: %s — %s", exc, msg_txt)
        return {"method": "smtp_gmail", "success": False, "details": msg_txt}
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return {"method": "smtp_gmail", "success": False, "details": str(exc)}


def _preview_only(subject: str, body: str) -> dict:
    return {
        "method": "preview_only",
        "success": True,
        "details": (
            "No email credentials configured. "
            "Set RESEND_API_KEY or SMTP_USER/SMTP_PASS to enable sending."
        ),
    }


def generate_outreach_email(
    recipient_email: str,
    company_name: str,
    icp: str,
    signals: dict | None = None,
    brief: dict | None = None,
) -> dict[str, Any]:
    """Generate the email content only (no sending). Returns fast."""
    account_brief = ""
    key_signals_identified: list = []
    recommended_angle = ""

    if brief:
        account_brief = brief.get("account_brief", "")
        key_signals_identified = brief.get("key_signals_identified", [])
        recommended_angle = brief.get("recommended_angle", "")

    logger.info("Generating email for %s → %s", company_name, recipient_email)
    email_content = _generate_email(
        recipient_email=recipient_email,
        company_name=company_name,
        account_brief=account_brief,
        key_signals_identified=key_signals_identified,
        icp=icp,
        signals=signals or {},
    )

    return {
        "company": company_name,
        "recipient_email": recipient_email,
        "email": {
            "subject": email_content.get("subject", ""),
            "body": email_content.get("body", ""),
        },
        "account_brief_used": account_brief,
        "recommended_angle": recommended_angle,
        "status": "success",
    }


def deliver_email(recipient_email: str, subject: str, body: str) -> dict:
    """Send an already-generated email via SMTP/Resend. Can be run in background."""
    resend_key = get_resend_api_key()
    smtp_user = get_smtp_user()

    if resend_key:
        sender_email = get_sender_email()
        logger.info("Sending via Resend API from %s", sender_email)
        return _send_via_resend(sender_email, recipient_email, subject, body)
    elif smtp_user:
        logger.info("Sending via Gmail SMTP from %s → %s", smtp_user, recipient_email)
        return _send_via_smtp(smtp_user, recipient_email, subject, body)
    else:
        logger.info("No send credentials — preview mode")
        return _preview_only(subject, body)


def send_outreach(
    recipient_email: str,
    company_name: str,
    icp: str,
    signals: dict | None = None,
    brief: dict | None = None,
) -> dict[str, Any]:
    """Legacy wrapper — generates AND sends (used by non-streaming endpoint)."""
    result = generate_outreach_email(
        recipient_email=recipient_email,
        company_name=company_name,
        icp=icp,
        signals=signals,
        brief=brief,
    )
    subject = result["email"]["subject"]
    body = result["email"]["body"]
    result["send_status"] = deliver_email(recipient_email, subject, body)
    return result
