"""
config.py — Environment variable loader for FireReach backend.
All secrets and runtime flags are sourced from .env (never hardcoded).
"""

import os
from dotenv import load_dotenv

# Load .env file from the backend directory
load_dotenv()


def get_gemini_api_key() -> str:
    """Return the Gemini API key — raises if missing."""
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )
    return key


def get_resend_api_key() -> str:
    """Return Resend API key, empty string if not configured."""
    return os.getenv("RESEND_API_KEY", "")


def get_sender_email() -> str:
    """Return the from-address used for outbound emails."""
    return os.getenv("SENDER_EMAIL", "onboarding@resend.dev")


def get_smtp_user() -> str:
    """Return Gmail SMTP username, empty string if not configured."""
    return os.getenv("SMTP_USER", "")


def get_smtp_pass() -> str:
    """Return Gmail SMTP password / app-password, empty string if not configured."""
    return os.getenv("SMTP_PASS", "")


def is_demo_mode() -> bool:
    """Return True when DEMO_MODE=true — forces mock data for all signals."""
    return os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
