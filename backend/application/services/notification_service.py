from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from domain.entities.alert import Alert

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Sends email notifications via SMTP.

    Configure via environment variables:
      SMTP_HOST  — e.g. smtp.gmail.com
      SMTP_PORT  — default 587 (STARTTLS)
      SMTP_USER  — login username
      SMTP_PASS  — login password / app-password
      SMTP_FROM  — sender address (defaults to SMTP_USER)
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        smtp_from: Optional[str] = None,
    ):
        self._host = smtp_host
        self._port = smtp_port
        self._user = smtp_user
        self._pass = smtp_pass
        self._from = smtp_from or smtp_user

    @property
    def is_configured(self) -> bool:
        return bool(self._host and self._user and self._pass)

    def send_email(self, to: str, subject: str, body_html: str) -> bool:
        """Send an HTML email. Returns True on success."""
        if not self.is_configured:
            logger.debug("Email not configured — skipping send to %s", to)
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._from
        msg["To"] = to
        msg.attach(MIMEText(body_html, "html"))

        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(self._host, self._port) as server:
                server.ehlo()
                server.starttls(context=ctx)
                server.login(self._user, self._pass)
                server.sendmail(self._from, [to], msg.as_string())
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception as exc:
            logger.warning("Email delivery failed to %s: %s", to, exc)
            return False

    def send_alert_email(self, to: str, alert: Alert) -> bool:
        """Format and send a trading alert email."""
        subject = f"[{alert.severity.value.upper()}] {alert.title}"
        body = f"""
<html><body style="font-family: sans-serif; color: #1e293b;">
<h2 style="color: {'#dc2626' if alert.severity.value == 'critical' else '#d97706'};">
  {alert.title}
</h2>
<p>{alert.detail}</p>
<p style="color: #64748b; font-size: 12px;">
  Condition: {alert.condition.value} &nbsp;|&nbsp;
  Severity: {alert.severity.value} &nbsp;|&nbsp;
  Time: {alert.created_at.isoformat()}
</p>
<hr style="border: none; border-top: 1px solid #e2e8f0;">
<p style="color: #94a3b8; font-size: 11px;">
  Volatility Balancing &mdash; automated trading alert
</p>
</body></html>
"""
        return self.send_email(to, subject, body)

    def send_password_reset_email(self, to: str, reset_url: str) -> bool:
        """Send a password reset link email."""
        subject = "Reset your Volatility Balancing password"
        body = f"""
<html><body style="font-family: sans-serif; color: #1e293b; max-width: 480px; margin: 40px auto;">
<h2>Password Reset</h2>
<p>You requested a password reset. Click the button below to set a new password.</p>
<p style="margin: 28px 0;">
  <a href="{reset_url}"
     style="background: #3b82f6; color: #fff; padding: 12px 24px;
            border-radius: 6px; text-decoration: none; font-weight: 600;">
    Reset Password
  </a>
</p>
<p style="color: #64748b; font-size: 13px;">
  This link expires in 1 hour. If you didn't request a reset, you can ignore this email.
</p>
<p style="color: #64748b; font-size: 13px;">Or copy this link: {reset_url}</p>
<hr style="border: none; border-top: 1px solid #e2e8f0; margin-top: 32px;">
<p style="color: #94a3b8; font-size: 11px;">Volatility Balancing</p>
</body></html>
"""
        return self.send_email(to, subject, body)
