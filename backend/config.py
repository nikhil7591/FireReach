import os
from dotenv import load_dotenv

load_dotenv()


def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
    return key


def get_resend_api_key() -> str:
    return os.getenv("RESEND_API_KEY", "")


def get_sender_email() -> str:
    return os.getenv("SENDER_EMAIL", "onboarding@resend.dev")


def get_smtp_user() -> str:
    return os.getenv("SMTP_USER", "")


def get_smtp_pass() -> str:
    return os.getenv("SMTP_PASS", "")


def is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
