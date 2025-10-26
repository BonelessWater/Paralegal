"""
Email Sender - SMTP email sending functionality

Sends email responses via SMTP with proper error handling and retries.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Send emails via SMTP.

    Supports Gmail, Outlook, and custom SMTP servers.
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True
    ):
        """
        Initialize email sender.

        Args:
            smtp_host: SMTP server hostname (defaults to env SMTP_HOST)
            smtp_port: SMTP server port (defaults to env SMTP_PORT)
            username: SMTP username (defaults to env EMAIL_USER)
            password: SMTP password (defaults to env EMAIL_PASS)
            use_tls: Use TLS encryption
        """
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.username = username or os.getenv('EMAIL_USER')
        self.password = password or os.getenv('EMAIL_PASS')
        self.use_tls = use_tls

        logger.info(f"Email Sender initialized (SMTP: {self.smtp_host}:{self.smtp_port})")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, any]:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            from_addr: Sender address (defaults to EMAIL_USER)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach
            html: Whether body is HTML

        Returns:
            Dict with 'success', 'message', and optional 'error'
        """
        if not self.username or not self.password:
            return {
                'success': False,
                'error': 'SMTP credentials not configured. Set EMAIL_USER and EMAIL_PASS in .env'
            }

        from_addr = from_addr or self.username

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ', '.join(cc)

            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for file_path in attachments:
                    if not Path(file_path).exists():
                        logger.warning(f"Attachment not found: {file_path}")
                        continue

                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(file_path).name}'
                        )
                        msg.attach(part)

            # Combine all recipients
            all_recipients = [to]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"✓ Email sent to {to}")

            return {
                'success': True,
                'message': f'Email sent to {to}',
                'to': to,
                'subject': subject
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return {
                'success': False,
                'error': 'SMTP authentication failed. Check EMAIL_USER and EMAIL_PASS.',
                'details': str(e)
            }

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                'success': False,
                'error': 'Failed to send email via SMTP',
                'details': str(e)
            }

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return {
                'success': False,
                'error': 'Unexpected error sending email',
                'details': str(e)
            }

    def send_email_with_retry(
        self,
        to: str,
        subject: str,
        body: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, any]:
        """
        Send email with automatic retry on failure.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for send_email()

        Returns:
            Dict with 'success', 'message', and optional 'error'
        """
        import time

        for attempt in range(max_retries):
            result = self.send_email(to, subject, body, **kwargs)

            if result['success']:
                return result

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)

        return result

    def test_connection(self) -> bool:
        """
        Test SMTP connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.username or not self.password:
            logger.error("SMTP credentials not configured")
            return False

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.username, self.password)
                logger.info("✓ SMTP connection successful")
                return True

        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            return False


def send_response_email(
    to: str,
    subject: str,
    body: str,
    classification: str = 'CLIENT_COMMUNICATION',
    urgency: float = 0.5
) -> Dict[str, any]:
    """
    Convenience function to send a response email.

    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        classification: Email type classification
        urgency: Urgency score (0.0-1.0)

    Returns:
        Dict with send result
    """
    sender = EmailSender()

    # Add metadata to email if needed
    if urgency > 0.7:
        subject = f"[URGENT] {subject}"

    return sender.send_email_with_retry(
        to=to,
        subject=subject,
        body=body,
        html=False
    )


if __name__ == "__main__":
    # Test email sender
    import sys

    logging.basicConfig(level=logging.INFO)

    sender = EmailSender()

    # Test connection
    print("\n" + "="*60)
    print("TESTING SMTP CONNECTION")
    print("="*60)

    if sender.test_connection():
        print("✓ SMTP connection successful")
    else:
        print("✗ SMTP connection failed")
        print("\nPlease configure EMAIL_USER and EMAIL_PASS in .env file")
        sys.exit(1)

    # Test sending email (dry run)
    print("\n" + "="*60)
    print("TEST EMAIL (not actually sent)")
    print("="*60)

    test_email = {
        'to': 'client@example.com',
        'subject': 'Re: Questions About My PIP Coverage',
        'body': """Dear Client,

Thank you for reaching out with your questions about PIP coverage.

I have received your email and am reviewing the details. I will get back to you within 24 hours.

Best regards,
Paralegal AI Assistant"""
    }

    print(f"To: {test_email['to']}")
    print(f"Subject: {test_email['subject']}")
    print(f"Body:\n{test_email['body']}")
    print("="*60)
