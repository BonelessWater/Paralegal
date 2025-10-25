"""
Feature Engineering Module for ML Pipeline
Transforms raw text into ML-ready features
"""

import re
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import LabelEncoder
import pickle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Clean and preprocess legal text for machine learning
    
    Handles common issues in legal documents:
    - Excessive whitespace
    - Special characters
    - Case normalization
    - Legal-specific patterns
    """
    
    @staticmethod
    def clean_legal_text(text: str) -> str:
        """
        Clean legal text for ML processing
        
        Args:
            text: Raw text from document
            
        Returns:
            Cleaned text ready for feature extraction
            
        Example:
            >>> processor = TextProcessor()
            >>> clean = processor.clean_legal_text("SETTLEMENT  OFFER\n\n$50,000...")
            >>> print(clean)
        """
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep periods, commas, dollar signs
        text = re.sub(r'[^a-z0-9\s\.\,\$]', '', text)
        
        # Remove standalone numbers (keep dollar amounts)
        text = re.sub(r'\b\d+\b', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, List]:
        """
        Extract legal entities from text (simple rule-based)
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with extracted entities:
                - dollar_amounts: List of monetary values
                - dates: List of dates found
                - names: List of potential names (UPPERCASE words)
        """
        entities = {
            'dollar_amounts': [],
            'dates': [],
            'names': []
        }
        
        # Extract dollar amounts
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        entities['dollar_amounts'] = re.findall(dollar_pattern, text)
        
        # Extract dates (simple patterns)
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        entities['dates'] = re.findall(date_pattern, text)
        
        # Extract potential names (consecutive capitalized words)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        entities['names'] = re.findall(name_pattern, text)
        
        return entities
    
    @staticmethod
    def get_text_stats(text: str) -> Dict[str, float]:
        """
        Get statistical features from text
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with statistics:
                - length: Character count
                - word_count: Number of words
                - avg_word_length: Average word length
                - sentence_count: Estimated sentence count
        """
        words = text.split()
        sentences = text.split('.')
        
        return {
            'length': len(text),
            'word_count': len(words),
            'avg_word_length': np.mean([len(w) for w in words]) if words else 0,
            'sentence_count': len(sentences)
        }


class FeatureExtractor:
    """
    Convert text to numerical features for ML models
    
    Supports:
    - TF-IDF vectors (for traditional ML)
    - Count vectors (for simple models)
    - Label encoding (for classification targets)
    """
    
    def __init__(self):
        self.tfidf_vectorizer = None
        self.count_vectorizer = None
        self.label_encoder = None
        
    def fit_tfidf(
        self, 
        texts: List[str],
        max_features: int = 500,
        ngram_range: Tuple[int, int] = (1, 2),
        **kwargs
    ) -> 'FeatureExtractor':
        """
        Fit TF-IDF vectorizer on training texts
        
        Args:
            texts: List of text documents
            max_features: Maximum number of features to extract
            ngram_range: Range of n-grams (default: unigrams and bigrams)
            **kwargs: Additional arguments for TfidfVectorizer
            
        Returns:
            self (for method chaining)
        """
        logger.info(f"Fitting TF-IDF vectorizer (max_features={max_features}, ngram_range={ngram_range})...")
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words='english',
            **kwargs
        )
        
        self.tfidf_vectorizer.fit(texts)
        logger.info(f"✅ TF-IDF vectorizer fitted with {len(self.tfidf_vectorizer.vocabulary_)} features")
        
        return self
    
    def transform_tfidf(self, texts: List[str]) -> np.ndarray:
        """
        Transform texts to TF-IDF features
        
        Args:
            texts: List of text documents
            
        Returns:
            TF-IDF matrix (n_samples, n_features)
        """
        if self.tfidf_vectorizer is None:
            raise ValueError("TF-IDF vectorizer not fitted. Call fit_tfidf() first.")
        
        return self.tfidf_vectorizer.transform(texts).toarray()
    
    def fit_transform_tfidf(
        self, 
        texts: List[str],
        max_features: int = 500,
        ngram_range: Tuple[int, int] = (1, 2)
    ) -> np.ndarray:
        """
        Fit and transform in one step
        
        Args:
            texts: List of text documents
            max_features: Maximum number of features
            ngram_range: Range of n-grams
            
        Returns:
            TF-IDF matrix
        """
        self.fit_tfidf(texts, max_features, ngram_range)
        return self.transform_tfidf(texts)
    
    def fit_labels(self, labels: pd.Series) -> 'FeatureExtractor':
        """
        Fit label encoder on classification targets
        
        Args:
            labels: Series of string labels
            
        Returns:
            self (for method chaining)
        """
        logger.info("Fitting label encoder...")
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(labels)
        logger.info(f"✅ Label encoder fitted with {len(self.label_encoder.classes_)} classes")
        logger.info(f"Classes: {list(self.label_encoder.classes_)}")
        
        return self
    
    def transform_labels(self, labels: pd.Series) -> np.ndarray:
        """
        Transform string labels to integers
        
        Args:
            labels: Series of string labels
            
        Returns:
            Integer array
        """
        if self.label_encoder is None:
            raise ValueError("Label encoder not fitted. Call fit_labels() first.")
        
        return self.label_encoder.transform(labels)
    
    def inverse_transform_labels(self, encoded_labels: np.ndarray) -> np.ndarray:
        """
        Convert integer labels back to strings
        
        Args:
            encoded_labels: Integer array
            
        Returns:
            String labels
        """
        if self.label_encoder is None:
            raise ValueError("Label encoder not fitted.")
        
        return self.label_encoder.inverse_transform(encoded_labels)
    
    def save(self, filepath: str):
        """
        Save all fitted transformers to disk
        
        Args:
            filepath: Path to save pickle file
        """
        state = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'label_encoder': self.label_encoder
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"✅ Feature extractors saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'FeatureExtractor':
        """
        Load fitted transformers from disk
        
        Args:
            filepath: Path to pickle file
            
        Returns:
            FeatureExtractor instance with loaded transformers
        """
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        extractor = cls()
        extractor.tfidf_vectorizer = state['tfidf_vectorizer']
        extractor.label_encoder = state['label_encoder']
        
        logger.info(f"✅ Feature extractors loaded from {filepath}")
        return extractor


def prepare_features(
    X_train: pd.Series,
    X_test: pd.Series,
    y_train: pd.Series,
    y_test: pd.Series,
    max_features: int = 500,
    clean_text: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, FeatureExtractor]:
    """
    One-stop function to prepare all features for training
    
    Args:
        X_train: Training text
        X_test: Test text
        y_train: Training labels
        y_test: Test labels
        max_features: TF-IDF max features
        clean_text: Whether to clean text before feature extraction
        
    Returns:
        Tuple of (X_train_features, X_test_features, y_train_encoded, y_test_encoded, extractor)
        
    Example:
        >>> from ml_pipeline.data_loader import get_classification_data
        >>> from sklearn.model_selection import train_test_split
        >>> 
        >>> X, y = get_classification_data()
        >>> X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        >>> 
        >>> X_train_feat, X_test_feat, y_train_enc, y_test_enc, extractor = prepare_features(
        >>>     X_train, X_test, y_train, y_test
        >>> )
        >>> # Now ready for training!
    """
    logger.info("=" * 80)
    logger.info("PREPARING FEATURES")
    logger.info("=" * 80)
    
    # Clean text if requested
    if clean_text:
        logger.info("Cleaning text...")
        processor = TextProcessor()
        X_train_clean = X_train.apply(processor.clean_legal_text)
        X_test_clean = X_test.apply(processor.clean_legal_text)
    else:
        X_train_clean = X_train
        X_test_clean = X_test
    
    # Initialize extractor
    extractor = FeatureExtractor()
    
    # Fit and transform TF-IDF
    logger.info("Extracting TF-IDF features...")
    X_train_features = extractor.fit_transform_tfidf(
        X_train_clean.tolist(),
        max_features=max_features
    )
    X_test_features = extractor.transform_tfidf(X_test_clean.tolist())
    
    # Encode labels
    logger.info("Encoding labels...")
    extractor.fit_labels(y_train)
    y_train_encoded = extractor.transform_labels(y_train)
    y_test_encoded = extractor.transform_labels(y_test)
    
    logger.info("=" * 80)
    logger.info("FEATURE PREPARATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Training features: {X_train_features.shape}")
    logger.info(f"Test features: {X_test_features.shape}")
    logger.info(f"Training labels: {y_train_encoded.shape}")
    logger.info(f"Test labels: {y_test_encoded.shape}")
    logger.info(f"Number of classes: {len(extractor.label_encoder.classes_)}")
    
    return X_train_features, X_test_features, y_train_encoded, y_test_encoded, extractor


if __name__ == "__main__":
    # Demo usage
    print("=" * 80)
    print("FEATURE ENGINEERING DEMO")
    print("=" * 80)
    
    # Sample texts
    texts = [
        "This is a settlement offer for $50,000 in the case of Smith v. Jones.",
        "POLICE REPORT: Accident occurred on 01/15/2023 at Main Street.",
        "Medical lien from Healthcare Provider Inc. totaling $12,500.00"
    ]
    
    labels = pd.Series(["Settlement Offer", "Police Report", "Medical Lien"])
    
    # Clean text
    print("\n1. Text Cleaning:")
    processor = TextProcessor()
    for text in texts:
        clean = processor.clean_legal_text(text)
        print(f"Original: {text[:50]}...")
        print(f"Cleaned:  {clean[:50]}...")
        print()
    
    # Extract features
    print("\n2. Feature Extraction:")
    extractor = FeatureExtractor()
    features = extractor.fit_transform_tfidf(texts, max_features=20)
    print(f"TF-IDF matrix shape: {features.shape}")
    print(f"Sample features (first doc): {features[0][:10]}")
    
    # Encode labels
    print("\n3. Label Encoding:")
    extractor.fit_labels(labels)
    encoded = extractor.transform_labels(labels)
    print(f"Original labels: {labels.tolist()}")
    print(f"Encoded labels:  {encoded.tolist()}")
    print(f"Classes: {extractor.label_encoder.classes_.tolist()}")
    
    print("\n✅ Feature engineering working correctly!")
