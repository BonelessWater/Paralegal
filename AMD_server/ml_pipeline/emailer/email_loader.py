"""
Email Loader - Load emails from Gmail IMAP and database

Integrates with backend/APIs/email/emailer.py for IMAP connectivity.
Provides ML-ready data loading for email classification and processing.
"""

import os
import sys
import email
import imaplib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from email.header import decode_header, make_header

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from integrations.db_operations import DatabaseManager
except ImportError:
    DatabaseManager = None

logger = logging.getLogger(__name__)


class EmailLoader:
    """
    Load emails from Gmail IMAP or PostgreSQL database.
    
    Provides training data for email classification models.
    """
    
    def __init__(
        self,
        email_user: Optional[str] = None,
        email_pass: Optional[str] = None,
        imap_host: str = "imap.gmail.com",
        db_manager: Optional[object] = None
    ):
        """
        Initialize email loader.
        
        Args:
            email_user: Gmail address (from .env if not provided)
            email_pass: Gmail app password (from .env if not provided)
            imap_host: IMAP server hostname
            db_manager: DatabaseManager instance (optional)
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        self.email_user = email_user or os.getenv('EMAIL_USER')
        self.email_pass = email_pass or os.getenv('EMAIL_PASS')
        self.imap_host = imap_host
        
        # Database connection
        if db_manager:
            self.db = db_manager
        elif DatabaseManager:
            self.db = DatabaseManager()
        else:
            logger.warning("DatabaseManager not available")
            self.db = None
        
        logger.info(f"Email Loader initialized (user: {self.email_user})")
    
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """
        Connect to Gmail IMAP server.
        
        Returns:
            IMAP connection object
        """
        if not self.email_user or not self.email_pass:
            raise ValueError("Email credentials not configured. Set EMAIL_USER and EMAIL_PASS in .env")
        
        mail = imaplib.IMAP4_SSL(self.imap_host)
        mail.login(self.email_user, self.email_pass)
        logger.info(f"✓ Connected to {self.imap_host}")
        return mail
    
    @staticmethod
    def decode_header_str(raw: str) -> str:
        """Decode email header string."""
        try:
            return str(make_header(decode_header(raw or "")))
        except Exception:
            return raw or ""
    
    def fetch_emails(
        self,
        mailbox: str = "INBOX",
        limit: Optional[int] = 100,
        since_days: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch emails from Gmail IMAP.
        
        Args:
            mailbox: Gmail folder (INBOX, [Gmail]/Sent, etc.)
            limit: Maximum number of emails to fetch
            since_days: Only fetch emails from last N days
            
        Returns:
            List of email dictionaries with parsed data
        """
        mail = self.connect_imap()
        mail.select(mailbox, readonly=True)
        
        # Build search criteria
        search_criteria = ['ALL']
        if since_days:
            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            search_criteria = [f'SINCE {since_date}']
        
        # Search for emails
        status, messages = mail.search(None, *search_criteria)
        email_ids = messages[0].split()
        
        if limit:
            email_ids = email_ids[-limit:]  # Get most recent
        
        logger.info(f"Fetching {len(email_ids)} emails from {mailbox}")
        
        emails = []
        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Parse email
                parsed = {
                    'email_id': email_id.decode(),
                    'message_id': msg.get('Message-ID'),
                    'subject': self.decode_header_str(msg.get('Subject', '')),
                    'from': self.decode_header_str(msg.get('From', '')),
                    'to': self.decode_header_str(msg.get('To', '')),
                    'date': msg.get('Date'),
                    'body': self._extract_body(msg),
                    'has_attachments': self._has_attachments(msg)
                }
                
                emails.append(parsed)
                
            except Exception as e:
                logger.error(f"Failed to parse email {email_id}: {e}")
        
        mail.close()
        mail.logout()
        
        logger.info(f"✓ Fetched {len(emails)} emails")
        return emails
    
    @staticmethod
    def _extract_body(msg: email.message.Message) -> str:
        """Extract plain text body from email."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except Exception:
                pass
        
        return body.strip()
    
    @staticmethod
    def _has_attachments(msg: email.message.Message) -> bool:
        """Check if email has attachments."""
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            return True
        return False
    
    def save_to_database(self, emails: List[Dict]) -> int:
        """
        Save emails to PostgreSQL database.
        
        Args:
            emails: List of parsed email dicts
            
        Returns:
            Number of emails saved
        """
        if not self.db:
            raise RuntimeError("Database not available")
        
        # Create communications table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS legal_data.communications (
            id SERIAL PRIMARY KEY,
            message_id TEXT UNIQUE,
            subject TEXT,
            sender TEXT,
            recipient TEXT,
            body TEXT,
            sent_date TIMESTAMP,
            has_attachments BOOLEAN,
            email_type TEXT,
            urgency_score FLOAT,
            sentiment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            self.db.execute_query(create_table_query)
        except Exception as e:
            logger.warning(f"Table creation warning: {e}")
        
        # Insert emails
        insert_query = """
        INSERT INTO legal_data.communications 
        (message_id, subject, sender, recipient, body, sent_date, has_attachments)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (message_id) DO NOTHING;
        """
        
        saved = 0
        for email_data in emails:
            try:
                # Parse date
                from email.utils import parsedate_to_datetime
                sent_date = None
                if email_data.get('date'):
                    try:
                        sent_date = parsedate_to_datetime(email_data['date'])
                    except Exception:
                        pass
                
                self.db.execute_query(
                    insert_query,
                    (
                        email_data.get('message_id'),
                        email_data.get('subject'),
                        email_data.get('from'),
                        email_data.get('to'),
                        email_data.get('body'),
                        sent_date,
                        email_data.get('has_attachments', False)
                    )
                )
                saved += 1
                
            except Exception as e:
                logger.error(f"Failed to save email: {e}")
        
        logger.info(f"✓ Saved {saved}/{len(emails)} emails to database")
        return saved
    
    def load_from_database(
        self,
        limit: Optional[int] = None,
        email_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Load emails from PostgreSQL database.
        
        Args:
            limit: Maximum number to load
            email_type: Filter by email type classification
            
        Returns:
            List of email dictionaries
        """
        if not self.db:
            raise RuntimeError("Database not available")
        
        query = """
        SELECT 
            id,
            message_id,
            subject,
            sender,
            recipient,
            body,
            sent_date,
            has_attachments,
            email_type,
            urgency_score,
            sentiment
        FROM legal_data.communications
        WHERE 1=1
        """
        
        params = []
        if email_type:
            query += " AND email_type = %s"
            params.append(email_type)
        
        query += " ORDER BY sent_date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if params:
            results = self.db.execute_query(query, tuple(params))
        else:
            results = self.db.execute_query(query)
        
        logger.info(f"Loaded {len(results)} emails from database")
        return results
    
    def get_training_data(
        self,
        labeled_only: bool = True
    ) -> Tuple[List[str], List[str]]:
        """
        Get email text and labels for training.
        
        Args:
            labeled_only: Only return emails with email_type label
            
        Returns:
            Tuple of (texts, labels)
        """
        if not self.db:
            raise RuntimeError("Database not available")
        
        query = """
        SELECT body, email_type
        FROM legal_data.communications
        WHERE body IS NOT NULL
        """
        
        if labeled_only:
            query += " AND email_type IS NOT NULL"
        
        results = self.db.execute_query(query)
        
        texts = [r['body'] for r in results]
        labels = [r['email_type'] for r in results]
        
        logger.info(f"Loaded {len(texts)} emails for training")
        return texts, labels


if __name__ == "__main__":
    # Test email loader
    loader = EmailLoader()
    print("✓ Email Loader initialized")
    print(f"  Email: {loader.email_user}")
    print(f"  IMAP: {loader.imap_host}")
    print("\nReady to fetch emails!")
