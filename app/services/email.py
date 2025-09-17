"""
Email service for sending notifications
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        # For development, we'll just log emails instead of sending them
        # In production, you would configure SMTP settings
        self.smtp_server = getattr(settings, "smtp_server", None)
        self.smtp_port = getattr(settings, "smtp_port", 587)
        self.smtp_username = getattr(settings, "smtp_username", None)
        self.smtp_password = getattr(settings, "smtp_password", None)
        self.from_email = getattr(settings, "from_email", "noreply@stellariq.com")

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        try:
            # For development, just log the reset token
            # In production, you would send an actual email with a reset link
            reset_url = f"http://localhost:3000/reset-password?token={reset_token}"

            subject = "StellarIQ - Password Reset Request"
            # For development, we just log the reset URL
            # In production, you would construct and send an email body like:
            # body = f"""
            # Hello,
            #
            # You have requested to reset your password for your StellarIQ account.
            #
            # Please click the link below to reset your password:
            # {reset_url}
            #
            # This link will expire in 1 hour.
            #
            # If you did not request this password reset, please ignore this email.
            #
            # Best regards,
            # The StellarIQ Team
            # """

            # For development, just log the email content
            logger.info(f"Password reset email for {to_email}:")
            logger.info(f"Subject: {subject}")
            logger.info(f"Reset URL: {reset_url}")
            logger.info(f"Reset Token: {reset_token}")

            # In production, you would use SMTP to send the actual email:
            # self._send_smtp_email(to_email, subject, body)

            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {e}")
            return False

    def _send_smtp_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP (for production use)"""
        try:
            if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
                logger.warning("SMTP not configured, email not sent")
                return False

            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMTP email to {to_email}: {e}")
            return False


# Global email service instance
email_service = EmailService()
