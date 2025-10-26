"""
Email Classifier - Classify emails by task type

Routes emails to appropriate agents based on content.
"""

import os
import sys
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


# Email task types
EMAIL_TYPES = {
    'CLIENT_COMMUNICATION': 'Direct client correspondence',
    'RECORDS_REQUEST': 'Medical/legal records requests',
    'LEGAL_RESEARCH': 'Legal research or case law questions',
    'SETTLEMENT_DISCUSSION': 'Settlement negotiations',
    'COURT_FILING': 'Court document or filing related',
    'INTERNAL': 'Internal team communication',
    'OTHER': 'Uncategorized'
}


class EmailClassifier:
    """
    Classify emails into task types for routing.
    
    Uses TF-IDF + RandomForest for fast, accurate classification.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize email classifier.
        
        Args:
            model_path: Path to saved model (auto-creates if not found)
        """
        self.model_dir = Path(__file__).parent.parent.parent / "trained_models"
        self.model_dir.mkdir(exist_ok=True)
        
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = self.model_dir / "email_classifier.pkl"
        
        self.vectorizer = None
        self.classifier = None
        self.label_encoder = None
        
        # Try to load existing model
        if self.model_path.exists():
            self.load_model()
        
        logger.info(f"Email Classifier initialized (model: {self.model_path.name})")
    
    def train(
        self,
        emails: List[str],
        labels: List[str],
        test_size: float = 0.2
    ) -> Dict[str, float]:
        """
        Train email classification model.
        
        Args:
            emails: List of email text
            labels: List of corresponding task types
            test_size: Fraction for validation
            
        Returns:
            Training metrics (accuracy, precision, recall, f1)
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        
        logger.info(f"Training on {len(emails)} emails...")
        
        # Encode labels
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(labels)
        
        # TF-IDF vectorization
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # Unigrams + bigrams
            min_df=2,
            max_df=0.8,
            stop_words='english'
        )
        
        X = self.vectorizer.fit_transform(emails)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train RandomForest
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            random_state=42,
            n_jobs=-1
        )
        
        self.classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'n_train': len(X_train),
            'n_test': len(X_test),
            'n_classes': len(self.label_encoder.classes_)
        }
        
        logger.info(f"✓ Training complete - Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
        
        # Save model
        self.save_model()
        
        return metrics
    
    def predict(self, email_text: str) -> str:
        """
        Predict email task type.
        
        Args:
            email_text: Email body text
            
        Returns:
            Predicted task type (e.g., 'CLIENT_COMMUNICATION')
        """
        if not self.classifier or not self.vectorizer:
            raise RuntimeError("Model not trained. Call train() first.")
        
        # Vectorize
        X = self.vectorizer.transform([email_text])
        
        # Predict
        y_pred = self.classifier.predict(X)[0]
        
        # Decode label
        label = self.label_encoder.inverse_transform([y_pred])[0]
        
        return label
    
    def predict_proba(self, email_text: str) -> Dict[str, float]:
        """
        Get probability distribution over task types.
        
        Args:
            email_text: Email body text
            
        Returns:
            Dict mapping task type to probability
        """
        if not self.classifier or not self.vectorizer:
            raise RuntimeError("Model not trained. Call train() first.")
        
        # Vectorize
        X = self.vectorizer.transform([email_text])
        
        # Get probabilities
        proba = self.classifier.predict_proba(X)[0]
        
        # Map to labels
        classes = self.label_encoder.classes_
        result = {classes[i]: float(proba[i]) for i in range(len(classes))}
        
        # Sort by probability
        result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
        
        return result
    
    def predict_batch(self, emails: List[str]) -> List[str]:
        """
        Predict task types for multiple emails.
        
        Args:
            emails: List of email texts
            
        Returns:
            List of predicted task types
        """
        if not self.classifier or not self.vectorizer:
            raise RuntimeError("Model not trained. Call train() first.")
        
        # Vectorize
        X = self.vectorizer.transform(emails)
        
        # Predict
        y_pred = self.classifier.predict(X)
        
        # Decode labels
        labels = self.label_encoder.inverse_transform(y_pred)
        
        return labels.tolist()
    
    def save_model(self):
        """Save trained model to disk."""
        if not self.classifier:
            logger.warning("No model to save")
            return
        
        model_data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'label_encoder': self.label_encoder,
            'version': '1.0'
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✓ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return
        
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vectorizer = model_data['vectorizer']
        self.classifier = model_data['classifier']
        self.label_encoder = model_data['label_encoder']
        
        logger.info(f"✓ Model loaded from {self.model_path}")
    
    def generate_training_labels(
        self,
        emails: List[str],
        use_llama: bool = True
    ) -> List[str]:
        """
        Auto-generate training labels using keyword matching or Llama.
        
        Args:
            emails: List of email texts
            use_llama: Use Llama for labeling (more accurate but slower)
            
        Returns:
            List of predicted labels
        """
        if use_llama:
            return self._label_with_llama(emails)
        else:
            return self._label_with_keywords(emails)
    
    def _label_with_keywords(self, emails: List[str]) -> List[str]:
        """Simple keyword-based labeling."""
        keywords = {
            'CLIENT_COMMUNICATION': [
                'client', 'spoke with', 'meeting', 'call', 'phone',
                'follow up', 'update', 'status', 'question'
            ],
            'RECORDS_REQUEST': [
                'medical records', 'records request', 'hospital',
                'doctor', 'treatment', 'diagnosis', 'patient',
                'authorization', 'release'
            ],
            'LEGAL_RESEARCH': [
                'case law', 'precedent', 'statute', 'regulation',
                'court', 'ruling', 'opinion', 'research'
            ],
            'SETTLEMENT_DISCUSSION': [
                'settlement', 'offer', 'negotiate', 'demand',
                'compensation', 'damages', 'agreement'
            ],
            'COURT_FILING': [
                'filing', 'motion', 'brief', 'complaint',
                'answer', 'discovery', 'deadline', 'docket'
            ]
        }
        
        labels = []
        for email in emails:
            email_lower = email.lower()
            
            # Count keyword matches
            scores = {}
            for label, words in keywords.items():
                score = sum(1 for word in words if word in email_lower)
                scores[label] = score
            
            # Pick best match
            if max(scores.values()) > 0:
                best_label = max(scores.items(), key=lambda x: x[1])[0]
            else:
                best_label = 'OTHER'
            
            labels.append(best_label)
        
        logger.info(f"Generated {len(labels)} keyword-based labels")
        return labels
    
    def _label_with_llama(self, emails: List[str]) -> List[str]:
        """Use Llama to generate labels (requires vLLM server)."""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                base_url="http://localhost:8000/v1",
                api_key="token-abc123"
            )
            
            labels = []
            for email in emails[:100]:  # Limit to avoid too many calls
                prompt = f"""Classify this email into ONE category:
- CLIENT_COMMUNICATION
- RECORDS_REQUEST
- LEGAL_RESEARCH
- SETTLEMENT_DISCUSSION
- COURT_FILING
- INTERNAL
- OTHER

Email:
{email[:500]}

Category:"""
                
                response = client.completions.create(
                    model="meta-llama/Llama-3.3-70B-Instruct",
                    prompt=prompt,
                    max_tokens=10,
                    temperature=0
                )
                
                label = response.choices[0].text.strip()
                if label not in EMAIL_TYPES:
                    label = 'OTHER'
                
                labels.append(label)
            
            logger.info(f"Generated {len(labels)} Llama-based labels")
            return labels
            
        except Exception as e:
            logger.warning(f"Llama labeling failed: {e}. Falling back to keywords.")
            return self._label_with_keywords(emails)


if __name__ == "__main__":
    # Test classifier
    classifier = EmailClassifier()
    
    # Test emails
    test_emails = [
        "Hi, I need a copy of my medical records from Dr. Smith. Please send authorization form.",
        "Following up on settlement offer of $50,000. Client wants to negotiate higher amount.",
        "Researching precedent for slip and fall cases in shopping malls. Found Smith v. Walmart.",
        "Client called asking about case status. Scheduled meeting for tomorrow at 2pm."
    ]
    
    # Generate labels
    labels = classifier.generate_training_labels(test_emails, use_llama=False)
    print(f"\n✓ Generated labels: {labels}")
    
    # Train
    metrics = classifier.train(test_emails, labels, test_size=0.25)
    print(f"\n✓ Training metrics: {metrics}")
    
    # Predict
    prediction = classifier.predict(test_emails[0])
    print(f"\n✓ Prediction: {prediction}")
    
    proba = classifier.predict_proba(test_emails[0])
    print(f"\n✓ Probabilities: {proba}")
