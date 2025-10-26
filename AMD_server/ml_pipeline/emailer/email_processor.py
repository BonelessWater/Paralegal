"""
Email Processor - Extract entities, urgency, sentiment

Combines NER, urgency scoring, and sentiment analysis for complete email analysis.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class EmailProcessor:
    """
    Process emails to extract structured information.
    
    - Entity extraction (NER)
    - Urgency scoring
    - Sentiment analysis
    """
    
    def __init__(self):
        """Initialize email processor."""
        self.ner_model = None
        self.sentiment_analyzer = None
        
        logger.info("Email Processor initialized")
    
    def _load_ner_model(self):
        """Load spaCy NER model (lazy loading)."""
        if self.ner_model:
            return
        
        try:
            import spacy
            
            # Try to load model
            try:
                self.ner_model = spacy.load("en_core_web_sm")
                logger.info("✓ Loaded spaCy en_core_web_sm")
            except OSError:
                # Download if not available
                logger.info("Downloading spaCy model...")
                os.system("python -m spacy download en_core_web_sm")
                self.ner_model = spacy.load("en_core_web_sm")
                logger.info("✓ Downloaded and loaded spaCy model")
                
        except Exception as e:
            logger.error(f"Failed to load NER model: {e}")
            self.ner_model = None
    
    def _load_sentiment_analyzer(self):
        """Load sentiment analysis model (lazy loading)."""
        if self.sentiment_analyzer:
            return
        
        try:
            from transformers import pipeline
            
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # CPU (use 0 for GPU)
            )
            logger.info("✓ Loaded sentiment analysis model")
            
        except Exception as e:
            logger.warning(f"Sentiment model not available: {e}")
            self.sentiment_analyzer = None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from email text.
        
        Args:
            text: Email body text
            
        Returns:
            Dict mapping entity type to list of entities
        """
        self._load_ner_model()
        
        if not self.ner_model:
            return {}
        
        # Process text
        doc = self.ner_model(text[:10000])  # Limit length
        
        # Group entities by type
        entities = {}
        for ent in doc.ents:
            label = ent.label_
            if label not in entities:
                entities[label] = []
            
            # Deduplicate
            if ent.text not in entities[label]:
                entities[label].append(ent.text)
        
        # Extract legal-specific patterns
        entities.update(self._extract_legal_entities(text))
        
        return entities
    
    def _extract_legal_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract legal-specific entities using regex."""
        entities = {}
        
        # Case numbers (e.g., "Case No. 2024-CV-1234")
        case_pattern = r'\b(?:Case|Docket|File)\s*(?:No\.|Number|#)?\s*:?\s*([A-Z0-9\-]+)'
        case_numbers = re.findall(case_pattern, text, re.IGNORECASE)
        if case_numbers:
            entities['CASE_NUMBER'] = case_numbers
        
        # Claim numbers
        claim_pattern = r'\b(?:Claim|Policy)\s*(?:No\.|Number|#)?\s*:?\s*([A-Z0-9\-]+)'
        claim_numbers = re.findall(claim_pattern, text, re.IGNORECASE)
        if claim_numbers:
            entities['CLAIM_NUMBER'] = claim_numbers
        
        # Phone numbers
        phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            entities['PHONE'] = phones
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            entities['EMAIL'] = emails
        
        # Monetary amounts
        money_pattern = r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?'
        amounts = re.findall(money_pattern, text)
        if amounts:
            entities['MONEY'] = amounts
        
        return entities
    
    def calculate_urgency(
        self,
        email_text: str,
        subject: Optional[str] = None,
        sent_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate urgency score (0.0 - 1.0).
        
        Higher scores indicate more urgent emails.
        
        Args:
            email_text: Email body
            subject: Email subject line
            sent_date: When email was sent
            
        Returns:
            Urgency score (0.0 = not urgent, 1.0 = very urgent)
        """
        score = 0.0
        
        # Combine subject and body
        full_text = (subject or "") + " " + email_text
        full_text_lower = full_text.lower()
        
        # High urgency keywords
        high_urgency_keywords = [
            'urgent', 'asap', 'immediately', 'emergency', 'critical',
            'need help', 'right away', 'time sensitive', 'deadline',
            'as soon as possible', '911', 'crisis'
        ]
        
        for keyword in high_urgency_keywords:
            if keyword in full_text_lower:
                score += 0.15
        
        # Medium urgency keywords
        medium_urgency_keywords = [
            'soon', 'quickly', 'prompt', 'expedite', 'priority',
            'important', 'pressing', 'time crunch'
        ]
        
        for keyword in medium_urgency_keywords:
            if keyword in full_text_lower:
                score += 0.08
        
        # Exclamation marks (multiple = more urgent)
        exclamation_count = full_text.count('!')
        score += min(exclamation_count * 0.05, 0.15)
        
        # ALL CAPS words
        caps_words = [w for w in full_text.split() if w.isupper() and len(w) > 3]
        score += min(len(caps_words) * 0.03, 0.10)
        
        # Time-based urgency (recent = more urgent)
        if sent_date:
            hours_ago = (datetime.now() - sent_date).total_seconds() / 3600
            if hours_ago < 1:
                score += 0.10
            elif hours_ago < 6:
                score += 0.05
        
        # Sentiment-based (angry/frustrated = more urgent)
        sentiment = self.analyze_sentiment(email_text)
        if sentiment == 'NEGATIVE':
            score += 0.10
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of email.
        
        Args:
            text: Email body text
            
        Returns:
            Sentiment label (POSITIVE, NEGATIVE, or NEUTRAL)
        """
        self._load_sentiment_analyzer()
        
        if not self.sentiment_analyzer:
            # Fallback to keyword-based
            return self._keyword_sentiment(text)
        
        try:
            # Limit text length
            text_sample = text[:512]
            
            result = self.sentiment_analyzer(text_sample)[0]
            label = result['label']  # POSITIVE or NEGATIVE
            confidence = result['score']
            
            # Convert to our labels
            if label == 'POSITIVE' and confidence > 0.7:
                return 'POSITIVE'
            elif label == 'NEGATIVE' and confidence > 0.7:
                return 'NEGATIVE'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return self._keyword_sentiment(text)
    
    def _keyword_sentiment(self, text: str) -> str:
        """Simple keyword-based sentiment analysis."""
        text_lower = text.lower()
        
        positive_words = [
            'thank', 'appreciate', 'great', 'excellent', 'wonderful',
            'helpful', 'happy', 'pleased', 'perfect', 'good'
        ]
        
        negative_words = [
            'angry', 'upset', 'frustrated', 'disappointed', 'terrible',
            'awful', 'horrible', 'bad', 'unacceptable', 'complaint',
            'problem', 'issue', 'wrong', 'error', 'fail'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if neg_count > pos_count + 1:
            return 'NEGATIVE'
        elif pos_count > neg_count + 1:
            return 'POSITIVE'
        else:
            return 'NEUTRAL'
    
    def process_email(
        self,
        email_text: str,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        sent_date: Optional[datetime] = None
    ) -> Dict:
        """
        Process email to extract all information.
        
        Args:
            email_text: Email body
            subject: Subject line
            sender: Sender email
            sent_date: When sent
            
        Returns:
            Complete analysis dict
        """
        # Extract entities
        entities = self.extract_entities(email_text)
        
        # Calculate urgency
        urgency = self.calculate_urgency(email_text, subject, sent_date)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(email_text)
        
        # Determine if action required
        action_keywords = [
            'please', 'need', 'request', 'can you', 'could you',
            'would you', 'send', 'provide', 'submit', 'review'
        ]
        
        action_required = any(
            keyword in email_text.lower()
            for keyword in action_keywords
        )
        
        return {
            'subject': subject,
            'sender': sender,
            'sent_date': sent_date.isoformat() if sent_date else None,
            'entities': entities,
            'urgency_score': round(urgency, 3),
            'sentiment': sentiment,
            'action_required': action_required,
            'word_count': len(email_text.split()),
            'has_attachments': False  # Set by caller
        }
    
    def process_batch(
        self,
        emails: List[Dict]
    ) -> List[Dict]:
        """
        Process multiple emails.
        
        Args:
            emails: List of email dicts with 'body', 'subject', etc.
            
        Returns:
            List of processed results
        """
        results = []
        
        for email in emails:
            try:
                result = self.process_email(
                    email.get('body', ''),
                    email.get('subject'),
                    email.get('from'),
                    email.get('sent_date')
                )
                
                # Preserve original fields
                result.update({
                    'email_id': email.get('email_id'),
                    'message_id': email.get('message_id')
                })
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process email: {e}")
                results.append({'error': str(e)})
        
        logger.info(f"✓ Processed {len(results)} emails")
        return results


if __name__ == "__main__":
    # Test processor
    processor = EmailProcessor()
    
    test_email = """
    Hi,
    
    This is URGENT! I need my medical records from Dr. Smith ASAP for my court case.
    My case number is 2024-CV-1234 and claim number is INS-98765.
    
    Please call me at 555-123-4567 or email john.doe@example.com.
    
    I'm very frustrated with the delay and need this immediately!
    
    Thanks,
    John
    """
    
    # Process email
    result = processor.process_email(
        test_email,
        subject="URGENT: Medical Records Request",
        sender="john.doe@example.com",
        sent_date=datetime.now()
    )
    
    print("\n" + "="*60)
    print("EMAIL PROCESSING RESULT")
    print("="*60)
    for key, value in result.items():
        print(f"{key:20s}: {value}")
    print("="*60)
