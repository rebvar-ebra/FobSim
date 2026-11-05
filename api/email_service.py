import html
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlencode


logger = logging.getLogger(__name__)

SendAsync = Callable[[dict[str, Any]], Awaitable[Any]]


def build_welcome_message(
    full_name: str,
    email: str,
    frontend_url: str,
    sender: str,
) -> dict[str, Any]:
    safe_name = html.escape(full_name)
    safe_email = html.escape(email)
    login_url = f"{frontend_url.rstrip('/')}/auth/login"

    return {
        "from": sender,
        "to": [email],
        "subject": "Welcome to the FobSim Research Community",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#0f172a">
          <h1 style="color:#0891b2">Welcome to FobSim, {safe_name}!</h1>
          <p>Thank you for joining our blockchain and fog-computing research community.</p>
          <p>Your login email is <strong>{safe_email}</strong>.</p>
          <p>
            <a href="{login_url}"
               style="display:inline-block;padding:12px 20px;background:#0891b2;color:white;text-decoration:none;border-radius:8px">
              Open FobSim
            </a>
          </p>
          <p>We look forward to seeing the experiments you build.</p>
          <p>The FobSim Research Team</p>
        </div>
        """.strip(),
    }


async def send_welcome_email(
    full_name: str,
    email: str,
    send_async: SendAsync | None = None,
) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("RESEND_FROM_EMAIL")
    frontend_url = os.environ.get(
        "FRONTEND_URL", "https://fobsim-frontend.onrender.com"
    )

    if not api_key or not sender:
        logger.warning(
            "Welcome email skipped because RESEND_API_KEY or RESEND_FROM_EMAIL is not configured"
        )
        return False

    if send_async is None:
        import resend

        resend.api_key = api_key
        send_async = resend.Emails.send_async

    message = build_welcome_message(
        full_name=full_name,
        email=email,
        frontend_url=frontend_url,
        sender=sender,
    )

    try:
        await send_async(message)
        return True
    except Exception:
        logger.exception("Failed to send welcome email to newly registered user")
        return False


def build_password_reset_message(
    full_name: str,
    email: str,
    reset_token: str,
    frontend_url: str,
    sender: str,
) -> dict[str, Any]:
    safe_name = html.escape(full_name)
    query = urlencode({"token": reset_token})
    reset_url = html.escape(
        f"{frontend_url.rstrip('/')}/auth/reset-password#{query}", quote=True
    )

    return {
        "from": sender,
        "to": [email],
        "subject": "Reset your FobSim password",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#0f172a">
          <h1 style="color:#0891b2">Reset your password</h1>
          <p>Hello {safe_name},</p>
          <p>Use the secure link below to choose a new FobSim password.</p>
          <p>
            <a href="{reset_url}"
               style="display:inline-block;padding:12px 20px;background:#0891b2;color:white;text-decoration:none;border-radius:8px">
              Choose a new password
            </a>
          </p>
          <p>This link expires in 30 minutes and stops working after your password changes.</p>
          <p>If you did not request this, you can safely ignore this email.</p>
          <p>The FobSim Research Team</p>
        </div>
        """.strip(),
    }


async def send_password_reset_email(
    full_name: str,
    email: str,
    reset_token: str,
    send_async: SendAsync | None = None,
) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("RESEND_FROM_EMAIL")
    frontend_url = os.environ.get(
        "FRONTEND_URL", "https://fobsim-frontend.onrender.com"
    )

    if not api_key or not sender:
        logger.warning(
            "Password reset email skipped because RESEND_API_KEY or RESEND_FROM_EMAIL is not configured"
        )
        return False

    if send_async is None:
        import resend

        resend.api_key = api_key
        send_async = resend.Emails.send_async

    message = build_password_reset_message(
        full_name=full_name,
        email=email,
        reset_token=reset_token,
        frontend_url=frontend_url,
        sender=sender,
    )

    try:
        await send_async(message)
        return True
    except Exception:
        logger.exception("Failed to send password reset email")
        return False
