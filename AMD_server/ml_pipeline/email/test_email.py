"""
Email Pipeline Tests

Tests email loading, classification, and processing.
"""

import sys
from pathlib import Path
import unittest
from datetime import datetime

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml_pipeline.email import EmailLoader, EmailClassifier, EmailProcessor, EMAIL_TYPES


class TestEmailLoader(unittest.TestCase):
    """Test email loader functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = EmailLoader()
    
    def test_initialization(self):
        """Test loader initializes correctly."""
        self.assertIsNotNone(self.loader)
        self.assertEqual(self.loader.imap_host, "imap.gmail.com")
        print("✓ Email Loader initialized")
    
    def test_header_decoding(self):
        """Test email header decoding."""
        test_header = "Test Subject"
        decoded = EmailLoader.decode_header_str(test_header)
        self.assertEqual(decoded, "Test Subject")
        print("✓ Header decoding works")
    
    def test_body_extraction(self):
        """Test email body extraction."""
        import email
        from email.mime.text import MIMEText
        
        msg = MIMEText("Test body content")
        body = EmailLoader._extract_body(msg)
        self.assertEqual(body, "Test body content")
        print("✓ Body extraction works")


class TestEmailClassifier(unittest.TestCase):
    """Test email classification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = EmailClassifier()
    
    def test_initialization(self):
        """Test classifier initializes."""
        self.assertIsNotNone(self.classifier)
        print(f"✓ Email Classifier initialized")
    
    def test_email_types(self):
        """Test email type definitions."""
        self.assertIn('CLIENT_COMMUNICATION', EMAIL_TYPES)
        self.assertIn('RECORDS_REQUEST', EMAIL_TYPES)
        self.assertIn('LEGAL_RESEARCH', EMAIL_TYPES)
        print(f"✓ {len(EMAIL_TYPES)} email types defined")
    
    def test_keyword_labeling(self):
        """Test keyword-based label generation."""
        test_emails = [
            "I need my medical records from the hospital",
            "Settlement offer of $50,000 received",
            "Researching case law for Smith v. Jones",
            "Client called with questions about the case"
        ]
        
        labels = self.classifier.generate_training_labels(test_emails, use_llama=False)
        
        self.assertEqual(len(labels), len(test_emails))
        self.assertIn(labels[0], EMAIL_TYPES)
        
        print(f"✓ Generated {len(labels)} keyword labels")
        for i, (email, label) in enumerate(zip(test_emails, labels)):
            print(f"  {i+1}. {label:25s} <- {email[:50]}...")
    
    def test_training(self):
        """Test classifier training."""
        # Training data
        emails = [
            "Please send me the medical records for patient John Doe",
            "I found relevant case law in Smith v. Walmart regarding slip and fall",
            "Client wants to discuss settlement offer of $75,000",
            "Following up on our phone call yesterday about the case",
            "Need authorization form to request treatment records",
            "Researching precedent for premises liability cases",
        ]
        
        labels = [
            'RECORDS_REQUEST',
            'LEGAL_RESEARCH',
            'SETTLEMENT_DISCUSSION',
            'CLIENT_COMMUNICATION',
            'RECORDS_REQUEST',
            'LEGAL_RESEARCH'
        ]
        
        # Train
        metrics = self.classifier.train(emails, labels, test_size=0.3)
        
        self.assertGreater(metrics['accuracy'], 0.0)
        self.assertGreater(metrics['n_train'], 0)
        
        print(f"✓ Classifier trained successfully")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  F1 Score: {metrics['f1']:.3f}")
        print(f"  Classes: {metrics['n_classes']}")
    
    def test_prediction(self):
        """Test prediction on new emails."""
        # Train first
        emails = [
            "Please send medical records",
            "Researching case law",
            "Settlement offer received",
            "Client called today"
        ]
        
        labels = [
            'RECORDS_REQUEST',
            'LEGAL_RESEARCH', 
            'SETTLEMENT_DISCUSSION',
            'CLIENT_COMMUNICATION'
        ]
        
        self.classifier.train(emails, labels, test_size=0.25)
        
        # Test prediction
        test_email = "I need the hospital records for my client"
        prediction = self.classifier.predict(test_email)
        
        self.assertIsInstance(prediction, str)
        self.assertIn(prediction, EMAIL_TYPES)
        
        print(f"✓ Prediction: {prediction}")
        
        # Test probability
        proba = self.classifier.predict_proba(test_email)
        self.assertIsInstance(proba, dict)
        
        print(f"✓ Probabilities:")
        for label, prob in list(proba.items())[:3]:
            print(f"  {label:25s}: {prob:.3f}")


class TestEmailProcessor(unittest.TestCase):
    """Test email processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = EmailProcessor()
    
    def test_initialization(self):
        """Test processor initializes."""
        self.assertIsNotNone(self.processor)
        print("✓ Email Processor initialized")
    
    def test_entity_extraction(self):
        """Test entity extraction."""
        test_text = """
        Hi, I need records for case number 2024-CV-1234.
        The claim number is INS-98765.
        Please call me at 555-123-4567 or email john@example.com.
        The settlement offer was $50,000.
        """
        
        entities = self.processor.extract_entities(test_text)
        
        self.assertIsInstance(entities, dict)
        
        # Should extract case number, phone, email, money
        print(f"✓ Extracted {len(entities)} entity types:")
        for entity_type, values in entities.items():
            print(f"  {entity_type:15s}: {values}")
        
        # Check for legal entities
        if 'CASE_NUMBER' in entities:
            self.assertIn('2024-CV-1234', entities['CASE_NUMBER'])
        
        if 'MONEY' in entities:
            self.assertGreater(len(entities['MONEY']), 0)
    
    def test_urgency_scoring(self):
        """Test urgency calculation."""
        # High urgency
        urgent_email = "URGENT! Need medical records ASAP for court deadline tomorrow!"
        urgency_high = self.processor.calculate_urgency(urgent_email)
        
        # Low urgency  
        normal_email = "When you have time, could you send me the case files?"
        urgency_low = self.processor.calculate_urgency(normal_email)
        
        self.assertGreater(urgency_high, urgency_low)
        self.assertGreaterEqual(urgency_high, 0.0)
        self.assertLessEqual(urgency_high, 1.0)
        
        print(f"✓ Urgency scoring works")
        print(f"  Urgent email: {urgency_high:.3f}")
        print(f"  Normal email: {urgency_low:.3f}")
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis."""
        positive = "Thank you so much! This is wonderful and very helpful."
        negative = "I'm very frustrated and angry about this terrible situation!"
        neutral = "Please send the documents when available."
        
        sent_pos = self.processor.analyze_sentiment(positive)
        sent_neg = self.processor.analyze_sentiment(negative)
        sent_neu = self.processor.analyze_sentiment(neutral)
        
        print(f"✓ Sentiment analysis works")
        print(f"  Positive: {sent_pos}")
        print(f"  Negative: {sent_neg}")
        print(f"  Neutral: {sent_neu}")
        
        self.assertIn(sent_pos, ['POSITIVE', 'NEGATIVE', 'NEUTRAL'])
        self.assertIn(sent_neg, ['POSITIVE', 'NEGATIVE', 'NEUTRAL'])
    
    def test_email_processing(self):
        """Test complete email processing."""
        test_email = """
        Hi,
        
        This is URGENT! I need my medical records from Dr. Smith ASAP.
        My case number is 2024-CV-1234 and claim is INS-98765.
        
        Please call 555-123-4567 or email john.doe@example.com.
        
        Very frustrated with the delay!
        
        Thanks,
        John
        """
        
        result = self.processor.process_email(
            test_email,
            subject="URGENT: Medical Records Request",
            sender="john.doe@example.com",
            sent_date=datetime.now()
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('entities', result)
        self.assertIn('urgency_score', result)
        self.assertIn('sentiment', result)
        self.assertIn('action_required', result)
        
        print(f"✓ Email processed successfully")
        print(f"  Urgency: {result['urgency_score']:.3f}")
        print(f"  Sentiment: {result['sentiment']}")
        print(f"  Action Required: {result['action_required']}")
        print(f"  Entities: {len(result['entities'])} types")


def run_tests():
    """Run all email pipeline tests."""
    print("\n" + "="*70)
    print("EMAIL PIPELINE TESTS")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEmailLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailProcessor))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
