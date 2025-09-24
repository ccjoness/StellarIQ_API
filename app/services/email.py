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
        # Load SMTP settings from configuration
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.enable_email_sending = settings.enable_email_sending

        # Log configuration status
        if self.enable_email_sending and all(
            [self.smtp_host, self.smtp_username, self.smtp_password]
        ):
            logger.info(
                f"Email service initialized with SMTP: {self.smtp_host}:{self.smtp_port}"
            )
        else:
            logger.info(
                "Email service initialized in logging mode (SMTP not configured or disabled)"
            )

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        try:
            reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
            subject = "StellarIQ - Password Reset Request"

            body = f"""Hello,

You have requested to reset your password for your StellarIQ account.

Please click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
The StellarIQ Team
"""

            # Log the email content
            logger.info(f"Password reset email for {to_email}:")
            logger.info(f"Subject: {subject}")
            logger.info(f"Reset URL: {reset_url}")

            # Send actual email if SMTP is configured and enabled
            if self.enable_email_sending:
                return self._send_smtp_email(to_email, subject, body)
            else:
                logger.info("Email sending disabled - email content logged only")
                return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {e}")
            return False

    def _send_smtp_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
                logger.warning("SMTP not configured, email not sent")
                return False

            msg = MIMEMultipart()
            # Format the From field with name and email
            from_header = (
                f"{self.from_name} <{self.from_email}>"
                if self.from_name
                else self.from_email
            )
            msg["From"] = from_header
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
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

    def send_market_alert_email(
        self, to_email: str, title: str, body: str, alert_data
    ) -> bool:
        """Send market alert email"""
        try:
            subject = f"StellarIQ - {title}"

            # Create detailed email body
            email_body = f"""
Hello,

{body}

Market Details:
- Symbol: {alert_data.symbol}
- Condition: {alert_data.market_condition.title()}
- Confidence: {alert_data.confidence_score:.1%}
"""

            if alert_data.current_price:
                email_body += f"- Current Price: ${alert_data.current_price:.2f}\n"

            if alert_data.previous_condition:
                email_body += (
                    f"- Previous Condition: {alert_data.previous_condition.title()}\n"
                )

            email_body += """
This alert was generated based on technical analysis of market indicators.
Please conduct your own research before making any investment decisions.

Best regards,
The StellarIQ Team
"""

            # Log the email content
            logger.info(f"Market alert email for {to_email}:")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {email_body}")

            # Send actual email if SMTP is configured and enabled
            if self.enable_email_sending:
                return self._send_smtp_email(to_email, subject, email_body)
            else:
                logger.info("Email sending disabled - email content logged only")
                return True

        except Exception as e:
            logger.error(f"Failed to send market alert email to {to_email}: {e}")
            return False

    def send_price_alert_email(
        self,
        to_email: str,
        symbol: str,
        current_price: float,
        threshold: float,
        alert_type: str,
    ) -> bool:
        """Send price alert email"""
        try:
            subject = f"StellarIQ - {symbol} Price Alert"

            if alert_type == "above":
                body = f"""Hello,

Price Alert: {symbol} has reached ${current_price:.2f}, above your alert threshold of ${threshold:.2f}

This alert was triggered because the current price has crossed your configured threshold.

Current Market Data:
- Symbol: {symbol}
- Current Price: ${current_price:.2f}
- Alert Threshold: ${threshold:.2f}
- Alert Type: Price goes {alert_type}

Please review your investment strategy and consider taking appropriate action.

Best regards,
The StellarIQ Team
"""
            else:
                body = f"""Hello,

Price Alert: {symbol} has dropped to ${current_price:.2f}, below your alert threshold of ${threshold:.2f}

This alert was triggered because the current price has crossed your configured threshold.

Current Market Data:
- Symbol: {symbol}
- Current Price: ${current_price:.2f}
- Alert Threshold: ${threshold:.2f}
- Alert Type: Price goes {alert_type}

Please review your investment strategy and consider taking appropriate action.

Best regards,
The StellarIQ Team
"""

            # Log the email content
            logger.info(f"Price alert email for {to_email}:")
            logger.info(f"Subject: {subject}")
            logger.info(
                f"Symbol: {symbol}, Price: ${current_price:.2f}, Threshold: ${threshold:.2f}, Type: {alert_type}"
            )

            # Send actual email if SMTP is configured and enabled
            if self.enable_email_sending:
                return self._send_smtp_email(to_email, subject, body)
            else:
                logger.info("Email sending disabled - email content logged only")
                return True

        except Exception as e:
            logger.error(f"Failed to send price alert email to {to_email}: {e}")
            return False


# Global email service instance
email_service = EmailService()
