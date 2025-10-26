"""
ML Inference APIs for Production Use

Simple, agent-friendly interfaces for all ML models.
Load models once, call inference functions repeatedly.

Usage:
    from ml_inference import MLInference
    
    # Initialize (loads all models)
    ml = MLInference()
    
    # Classify document
    doc_type = ml.classify_document("This is a settlement offer...")
    
    # Search similar cases
    results = ml.search_similar_cases("car accident back injury")
    
    # Transcribe audio
    transcript = ml.transcribe_audio("call_recording.m4a")
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models.document_classifier import DocumentClassifier
from rag_embeddings import RAGEmbeddings
from audio.whisper_api import WhisperAPITranscriber
from audio.audio_loader import AudioLoader

# OCR processor (optional, will fail gracefully if not available)
try:
    from ocr.ocr_processor import OCRProcessor
except ImportError:
    OCRProcessor = None

# Email processor (optional, will fail gracefully if not available)
try:
    from emailer.email_classifier import EmailClassifier
    from emailer.email_processor import EmailProcessor
except ImportError:
    EmailClassifier = None
    EmailProcessor = None

# Structured data pipeline (optional, will fail gracefully if not available)
try:
    from structured.data_loader import DataLoader
    from structured.feature_engineering import FeatureEngineer
    from structured.settlement_predictor import SettlementPredictor
    from structured.case_matcher import CaseMatcher
except ImportError:
    DataLoader = None
    FeatureEngineer = None
    SettlementPredictor = None
    CaseMatcher = None


class MLInference:
    """
    Unified ML inference API for all models.
    
    Loads all trained models and provides simple functions for predictions.
    Designed to be called by AI agents in production.
    """
    
    def __init__(
        self,
        models_dir: str = None,
        load_document_classifier: bool = True,
        load_rag_embeddings: bool = True,
        load_audio_transcriber: bool = True,
        load_ocr: bool = True,
        load_email: bool = True,
        load_structured: bool = True
    ):
        """
        Initialize ML inference with all models.
        
        Args:
            models_dir: Directory containing trained models
            load_document_classifier: Load document classification model
            load_rag_embeddings: Load RAG embeddings for semantic search
            load_audio_transcriber: Load audio transcription model
            load_ocr: Load OCR processor for image text extraction
            load_email: Load email classification and processing
            load_structured: Load structured data pipeline (settlement prediction)
        """
        self.models_dir = models_dir or str(Path(__file__).parent / "trained_models")
        
        print("=" * 70)
        print("INITIALIZING ML INFERENCE")
        print("=" * 70)
        
        # Initialize components
        self.document_classifier = None
        self.rag_embeddings = None
        self.audio_transcriber = None
        self.ocr_processor = None
        self.email_classifier = None
        self.email_processor = None
        self.feature_engineer = None
        self.settlement_predictor = None
        self.case_matcher = None
        
        # Load models
        if load_document_classifier:
            self._load_document_classifier()
        
        if load_rag_embeddings:
            self._load_rag_embeddings()
        
        if load_audio_transcriber:
            self._load_audio_transcriber()
        
        if load_ocr:
            self._load_ocr_processor()
        
        if load_email:
            self._load_email_pipeline()
        
        if load_structured:
            self._load_structured_pipeline()
        
        print("\n✓ ML Inference ready!")
        print("=" * 70)
    
    def _load_document_classifier(self):
        """Load trained document classifier."""
        try:
            print("\nLoading document classifier...")
            model_path = Path(self.models_dir) / "document_classifier.pkl"
            
            if not model_path.exists():
                print(f"⚠️  Model not found: {model_path}")
                print("   Run train.py to train the model first")
                return
            
            self.document_classifier = DocumentClassifier.load(str(model_path))
            print("✓ Document classifier loaded")
            
        except Exception as e:
            print(f"❌ Failed to load document classifier: {e}")
    
    def _load_rag_embeddings(self):
        """Load RAG embeddings for semantic search."""
        try:
            print("\nLoading RAG embeddings...")
            
            self.rag_embeddings = RAGEmbeddings()
            self.rag_embeddings.load("morgan_documents")
            
            print("✓ RAG embeddings loaded")
            
        except Exception as e:
            print(f"⚠️  RAG embeddings not found: {e}")
            print("   Run rag_embeddings.py to generate embeddings first")
    
    def _load_audio_transcriber(self):
        """Load audio transcription model."""
        try:
            print("\nLoading audio transcriber...")
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("⚠️  OPENAI_API_KEY not set, audio transcription disabled")
                return
            
            self.audio_transcriber = WhisperAPITranscriber(api_key=api_key)
            print("✓ Audio transcriber loaded")
            
        except Exception as e:
            print(f"❌ Failed to load audio transcriber: {e}")
    
    def _load_ocr_processor(self):
        """Load OCR processor for image text extraction."""
        try:
            print("\nLoading OCR processor...")
            
            if OCRProcessor is None:
                print("⚠️  OCR processor not available")
                return
            
            self.ocr_processor = OCRProcessor(langs=['en'], gpu=True)
            print("✓ OCR processor loaded (GPU-accelerated)")
            
        except Exception as e:
            print(f"⚠️  OCR processor failed to load: {e}")
            print("   OCR functionality will be disabled")
    
    def _load_email_pipeline(self):
        """Load email classification and processing pipeline."""
        try:
            print("\nLoading email pipeline...")
            
            if EmailClassifier is None or EmailProcessor is None:
                print("⚠️  Email pipeline not available")
                return
            
            self.email_classifier = EmailClassifier()
            self.email_processor = EmailProcessor()
            
            model_path = Path(self.models_dir) / "email_classifier.pkl"
            if model_path.exists():
                self.email_classifier.load_model()
                print("✓ Email pipeline loaded (classifier trained)")
            else:
                print("✓ Email pipeline loaded (classifier not trained yet)")
            
        except Exception as e:
            print(f"⚠️  Email pipeline failed to load: {e}")
            print("   Email functionality will be limited")
    
    def _load_structured_pipeline(self):
        """Load structured data pipeline (settlement prediction, case matching)."""
        try:
            print("\nLoading structured data pipeline...")
            
            if FeatureEngineer is None or SettlementPredictor is None or CaseMatcher is None:
                print("⚠️  Structured data pipeline not available")
                return
            
            # Always load feature engineer
            self.feature_engineer = FeatureEngineer()
            
            # Load settlement predictor
            self.settlement_predictor = SettlementPredictor()
            predictor_path = Path(self.models_dir) / "settlement_predictor.pkl"
            if predictor_path.exists():
                self.settlement_predictor.load_model()
                print("✓ Settlement predictor loaded (trained)")
            else:
                print("✓ Settlement predictor loaded (not trained yet)")
            
            # Load case matcher
            self.case_matcher = CaseMatcher()
            matcher_path = Path(self.models_dir) / "case_matcher.pkl"
            if matcher_path.exists():
                self.case_matcher.load_model()
                print("✓ Case matcher loaded (fitted)")
            else:
                print("✓ Case matcher loaded (not fitted yet)")
            
        except Exception as e:
            print(f"⚠️  Structured data pipeline failed to load: {e}")
            print("   Settlement prediction will be unavailable")
    
    # =========================================================================
    # DOCUMENT CLASSIFICATION
    # =========================================================================
    
    def classify_document(
        self,
        text: str,
        return_probabilities: bool = False
    ) -> Union[str, Dict]:
        """
        Classify a legal document.
        
        Args:
            text: Document text to classify
            return_probabilities: If True, return class probabilities
        
        Returns:
            If return_probabilities=False: Predicted document type (str)
            If return_probabilities=True: Dict with type and probabilities
        
        Example:
            >>> ml.classify_document("This is a settlement offer...")
            'Settlement Offer'
            
            >>> ml.classify_document("...", return_probabilities=True)
            {
                'document_type': 'Settlement Offer',
                'confidence': 0.92,
                'probabilities': {
                    'Settlement Offer': 0.92,
                    'Police Report': 0.05,
                    ...
                }
            }
        """
        if self.document_classifier is None:
            raise RuntimeError("Document classifier not loaded")
        
        if return_probabilities:
            # Get class probabilities
            probs = self.document_classifier.predict_proba([text])[0]
            pred_class = self.document_classifier.predict([text])[0]
            
            # Format probabilities
            prob_dict = {
                label: float(prob)
                for label, prob in zip(
                    self.document_classifier.label_encoder.classes_,
                    probs
                )
            }
            
            return {
                'document_type': pred_class,
                'confidence': max(probs),
                'probabilities': prob_dict
            }
        else:
            # Just return predicted class
            return self.document_classifier.predict([text])[0]
    
    def classify_documents_batch(
        self,
        texts: List[str]
    ) -> List[str]:
        """
        Classify multiple documents at once.
        
        Args:
            texts: List of document texts
        
        Returns:
            List of predicted document types
        """
        if self.document_classifier is None:
            raise RuntimeError("Document classifier not loaded")
        
        return self.document_classifier.predict(texts)
    
    # =========================================================================
    # SEMANTIC SEARCH (RAG)
    # =========================================================================
    
    def search_similar_cases(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Search for similar legal cases using semantic search.
        
        Args:
            query: Search query (natural language)
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)
        
        Returns:
            List of matching documents with metadata:
                - title: Document title
                - document_type: Type of document
                - similarity: Similarity score (0-1)
                - text_preview: First 200 chars of text
                - full_text: Complete document text
        
        Example:
            >>> results = ml.search_similar_cases(
            ...     "car accident with back injury",
            ...     top_k=3
            ... )
            >>> for r in results:
            ...     print(f"{r['title']}: {r['similarity']:.2f}")
        """
        if self.rag_embeddings is None:
            raise RuntimeError("RAG embeddings not loaded")
        
        results = self.rag_embeddings.search(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        # Format results for agents
        formatted_results = []
        for result in results:
            doc = result['document']
            formatted_results.append({
                'title': doc['title'],
                'document_type': doc['document_type'],
                'similarity': result['similarity'],
                'text_preview': doc['full_text'][:200] + "...",
                'full_text': doc['full_text'],
                'metadata': {
                    'document_id': doc['document_id'],
                    'jurisdiction': doc.get('jurisdiction'),
                    'court': doc.get('court'),
                    'decision_date': doc.get('decision_date')
                }
            })
        
        return formatted_results
    
    def search_by_document(
        self,
        document_text: str,
        top_k: int = 5,
        exclude_self: bool = True
    ) -> List[Dict]:
        """
        Find documents similar to a given document.
        
        Useful for "find similar cases" functionality.
        
        Args:
            document_text: Text of the document to match against
            top_k: Number of similar documents to return
            exclude_self: Skip the exact same document if found
        
        Returns:
            List of similar documents
        """
        # Use first 500 chars as query for efficiency
        query = document_text[:500]
        
        results = self.search_similar_cases(query, top_k=top_k + 1)
        
        if exclude_self:
            # Filter out exact matches (similarity > 0.99)
            results = [r for r in results if r['similarity'] < 0.99]
        
        return results[:top_k]
    
    # =========================================================================
    # AUDIO TRANSCRIPTION
    # =========================================================================
    
    def transcribe_audio(
        self,
        audio_path: Union[str, Path],
        language: str = "en"
    ) -> Dict:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_path: Path to audio file (.m4a, .mp3, .wav, etc.)
            language: Audio language code (default: 'en')
        
        Returns:
            Dictionary with transcription results:
                - text: Transcribed text
                - language: Detected/specified language
                - file_size_mb: Audio file size
                - success: Boolean indicating success
        
        Example:
            >>> result = ml.transcribe_audio("call_recording.m4a")
            >>> print(result['text'])
            "Hi, my name is Alex and I was in a car accident..."
        """
        if self.audio_transcriber is None:
            raise RuntimeError("Audio transcriber not loaded")
        
        try:
            result = self.audio_transcriber.transcribe(
                audio_path=audio_path,
                language=language,
                prompt="This is a legal consultation phone call."
            )
            
            result['success'] = True
            return result
            
        except Exception as e:
            return {
                'text': None,
                'success': False,
                'error': str(e)
            }
    
    def transcribe_audio_batch(
        self,
        audio_paths: List[Union[str, Path]],
        language: str = "en",
        verbose: bool = True
    ) -> List[Dict]:
        """
        Transcribe multiple audio files.
        
        Args:
            audio_paths: List of audio file paths
            language: Audio language code
            verbose: Print progress messages
        
        Returns:
            List of transcription results
        """
        if self.audio_transcriber is None:
            raise RuntimeError("Audio transcriber not loaded")
        
        return self.audio_transcriber.transcribe_batch(
            audio_paths=audio_paths,
            language=language,
            verbose=verbose
        )
    
    # =========================================================================
    # COMBINED WORKFLOWS
    # =========================================================================
    
    def process_document(self, text: str) -> Dict:
        """
        Complete document processing pipeline.
        
        Classifies document and finds similar cases in one call.
        
        Args:
            text: Document text
        
        Returns:
            Dictionary with:
                - classification: Predicted document type + confidence
                - similar_cases: Top 3 similar documents
        """
        result = {}
        
        # Classify document
        if self.document_classifier:
            classification = self.classify_document(text, return_probabilities=True)
            result['classification'] = classification
        
        # Find similar cases
        if self.rag_embeddings:
            similar = self.search_similar_cases(text[:500], top_k=3)
            result['similar_cases'] = similar
        
        return result
    
    def process_audio_call(
        self,
        audio_path: Union[str, Path]
    ) -> Dict:
        """
        Complete audio call processing pipeline.
        
        Transcribes audio and searches for related cases.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dictionary with:
                - transcription: Transcribed text
                - related_cases: Similar cases based on transcript
        """
        result = {}
        
        # Transcribe audio
        if self.audio_transcriber:
            transcription = self.transcribe_audio(audio_path)
            result['transcription'] = transcription
            
            # Search for related cases using transcript
            if transcription['success'] and self.rag_embeddings:
                related = self.search_similar_cases(
                    transcription['text'][:500],
                    top_k=3
                )
                result['related_cases'] = related
        
        return result
    
    # =========================================================================
    # OCR (OPTICAL CHARACTER RECOGNITION)
    # =========================================================================
    
    def extract_text_from_image(
        self,
        image_path: Union[str, Path]
    ) -> Dict:
        """
        Extract text from an image using OCR.
        
        Args:
            image_path: Path to image file (.jpg, .png, .tif, etc.)
        
        Returns:
            Dictionary with OCR results:
                - text: Extracted text
                - word_count: Number of words extracted
                - success: Boolean indicating success
        
        Example:
            >>> result = ml.extract_text_from_image("scanned_doc.jpg")
            >>> print(result['text'])
            "Medical Bill ..."
        """
        if self.ocr_processor is None:
            raise RuntimeError("OCR processor not loaded")
        
        try:
            text = self.ocr_processor.extract_text_simple(str(image_path))
            
            return {
                'text': text,
                'word_count': len(text.split()),
                'success': True
            }
            
        except Exception as e:
            return {
                'text': None,
                'word_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def extract_and_classify_image(
        self,
        image_path: Union[str, Path]
    ) -> Dict:
        """
        Extract text from image and classify the document.
        
        Combines OCR + document classification in one call.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Dictionary with:
                - text: Extracted text
                - document_type: Classified document type
                - confidence: Classification confidence
        
        Example:
            >>> result = ml.extract_and_classify_image("medical_bill.jpg")
            >>> print(f"Type: {result['document_type']}")
            "Medical Bill"
        """
        result = {}
        
        # Extract text
        ocr_result = self.extract_text_from_image(image_path)
        result.update(ocr_result)
        
        # Classify if extraction succeeded
        if ocr_result['success'] and ocr_result['text'] and self.document_classifier:
            classification = self.classify_document(
                ocr_result['text'],
                return_probabilities=True
            )
            result['document_type'] = classification['document_type']
            result['confidence'] = classification['confidence']
            result['probabilities'] = classification['probabilities']
        
        return result
    
    def process_image_batch(
        self,
        image_paths: List[Union[str, Path]],
        classify: bool = True,
        verbose: bool = True
    ) -> List[Dict]:
        """
        Process multiple images with OCR (and optionally classify).
        
        Args:
            image_paths: List of image file paths
            classify: Also classify extracted text
            verbose: Print progress messages
        
        Returns:
            List of processing results
        """
        if self.ocr_processor is None:
            raise RuntimeError("OCR processor not loaded")
        
        results = []
        total = len(image_paths)
        
        if verbose:
            print(f"\nProcessing {total} images...")
        
        for i, path in enumerate(image_paths, 1):
            if verbose and i % 10 == 0:
                print(f"  Processed {i}/{total} images")
            
            if classify:
                result = self.extract_and_classify_image(path)
            else:
                result = self.extract_text_from_image(path)
            
            result['file_path'] = str(path)
            results.append(result)
        
        if verbose:
            success_count = sum(1 for r in results if r['success'])
            print(f"✓ Completed: {success_count}/{total} successful")
        
        return results
    
    # =========================================================================
    # EMAIL PROCESSING
    # =========================================================================
    
    def classify_email(
        self,
        email_text: str,
        return_probabilities: bool = False
    ) -> Union[str, Dict]:
        """
        Classify email by task type.
        
        Args:
            email_text: Email body text
            return_probabilities: Return probability distribution
            
        Returns:
            Email task type (or dict with probabilities)
        """
        if self.email_classifier is None:
            raise RuntimeError("Email classifier not loaded")
        
        if return_probabilities:
            return self.email_classifier.predict_proba(email_text)
        else:
            return self.email_classifier.predict(email_text)
    
    def analyze_email(
        self,
        email_text: str,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        sent_date: Optional[str] = None
    ) -> Dict:
        """
        Comprehensive email analysis (classification + entities + urgency + sentiment).
        
        Args:
            email_text: Email body
            subject: Subject line
            sender: Sender email
            sent_date: Sent timestamp
            
        Returns:
            Full analysis dict
        """
        if self.email_processor is None:
            raise RuntimeError("Email processor not loaded")
        
        # Parse date if string
        if sent_date and isinstance(sent_date, str):
            from datetime import datetime
            try:
                sent_date = datetime.fromisoformat(sent_date)
            except:
                sent_date = None
        
        # Process email
        result = self.email_processor.process_email(
            email_text,
            subject=subject,
            sender=sender,
            sent_date=sent_date
        )
        
        # Add classification
        if self.email_classifier:
            try:
                task_type = self.email_classifier.predict(email_text)
                result['task_type'] = task_type
            except:
                result['task_type'] = 'UNKNOWN'
        
        return result
    
    def process_email_batch(
        self,
        emails: List[Dict],
        verbose: bool = True
    ) -> List[Dict]:
        """
        Process multiple emails.
        
        Args:
            emails: List of email dicts with 'body', 'subject', etc.
            verbose: Print progress
            
        Returns:
            List of analysis results
        """
        if self.email_processor is None:
            raise RuntimeError("Email processor not loaded")
        
        if verbose:
            print(f"\nProcessing {len(emails)} emails...")
        
        results = self.email_processor.process_batch(emails)
        
        # Add classifications
        if self.email_classifier:
            for email, result in zip(emails, results):
                try:
                    task_type = self.email_classifier.predict(email.get('body', ''))
                    result['task_type'] = task_type
                except:
                    result['task_type'] = 'UNKNOWN'
        
        if verbose:
            print(f"✓ Processed {len(results)} emails")
        
        return results
    
    # =========================================================================
    # STRUCTURED DATA PIPELINE
    # =========================================================================
    
    def predict_settlement(
        self,
        case_data: Dict,
        include_confidence: bool = True
    ) -> Dict:
        """
        Predict settlement amount for a legal case.
        
        Args:
            case_data: Dict with case information (injury_severity, medical_costs, etc.)
            include_confidence: Include confidence interval
            
        Returns:
            Dict with settlement prediction
        """
        if self.settlement_predictor is None or self.feature_engineer is None:
            raise RuntimeError("Settlement predictor not loaded")
        
        # Extract features
        features = self.feature_engineer.extract_all_features(case_data)
        
        # Predict
        if include_confidence:
            result = self.settlement_predictor.predict_with_confidence(features)
        else:
            amount = self.settlement_predictor.predict(features)
            result = {'prediction': amount}
        
        return result
    
    def find_similar_cases(
        self,
        case_data: Dict,
        k: int = 5
    ) -> List[Dict]:
        """
        Find K most similar historical cases.
        
        Args:
            case_data: Dict with case information
            k: Number of similar cases to return
            
        Returns:
            List of similar case dicts with similarity scores
        """
        if self.case_matcher is None or self.feature_engineer is None:
            raise RuntimeError("Case matcher not loaded")
        
        # Extract features
        features = self.feature_engineer.extract_all_features(case_data)
        
        # Find similar
        similar_cases = self.case_matcher.find_similar_cases(features, k=k)
        
        return similar_cases
    
    def get_settlement_statistics(
        self,
        case_data: Dict,
        k: int = 10
    ) -> Dict:
        """
        Get settlement statistics from similar cases.
        
        Args:
            case_data: Dict with case information
            k: Number of similar cases to consider
            
        Returns:
            Dict with mean, median, min, max, range
        """
        if self.case_matcher is None or self.feature_engineer is None:
            raise RuntimeError("Case matcher not loaded")
        
        # Extract features
        features = self.feature_engineer.extract_all_features(case_data)
        
        # Get statistics
        stats = self.case_matcher.find_similar_settlements(features, k=k)
        
        return stats
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_status(self) -> Dict:
        """
        Get status of all loaded models.
        
        Returns:
            Dictionary with model status
        """
        return {
            'document_classifier': {
                'loaded': self.document_classifier is not None,
                'classes': list(self.document_classifier.label_encoder.classes_) if self.document_classifier else None
            },
            'rag_embeddings': {
                'loaded': self.rag_embeddings is not None,
                'num_documents': len(self.rag_embeddings.documents) if self.rag_embeddings else 0
            },
            'audio_transcriber': {
                'loaded': self.audio_transcriber is not None,
                'model': self.audio_transcriber.model if self.audio_transcriber else None
            },
            'ocr_processor': {
                'loaded': self.ocr_processor is not None,
                'gpu': self.ocr_processor.gpu if self.ocr_processor else False,
                'languages': self.ocr_processor.langs if self.ocr_processor else None
            },
            'email_classifier': {
                'loaded': self.email_classifier is not None,
                'trained': (self.email_classifier.classifier is not None) if self.email_classifier else False
            },
            'email_processor': {
                'loaded': self.email_processor is not None
            },
            'settlement_predictor': {
                'loaded': self.settlement_predictor is not None,
                'trained': (self.settlement_predictor.model is not None) if self.settlement_predictor else False,
                'n_features': len(self.settlement_predictor.feature_names) if (self.settlement_predictor and self.settlement_predictor.feature_names) else 0
            },
            'case_matcher': {
                'loaded': self.case_matcher is not None,
                'fitted': (self.case_matcher.matcher is not None) if self.case_matcher else False,
                'n_cases': len(self.case_matcher.case_database) if (self.case_matcher and self.case_matcher.case_database) else 0
            },
            'feature_engineer': {
                'loaded': self.feature_engineer is not None
            }
        }


# Quick usage example
if __name__ == "__main__":
    # Initialize ML inference
    ml = MLInference()
    
    # Print status
    print("\n" + "=" * 70)
    print("MODEL STATUS")
    print("=" * 70)
    status = ml.get_status()
    
    for model_name, model_status in status.items():
        print(f"\n{model_name}:")
        for key, value in model_status.items():
            print(f"  {key}: {value}")
    
    # Test document classification (if loaded)
    if ml.document_classifier:
        print("\n" + "=" * 70)
        print("TEST: DOCUMENT CLASSIFICATION")
        print("=" * 70)
        
        test_text = "This is a settlement offer for $50,000 to resolve all claims."
        result = ml.classify_document(test_text, return_probabilities=True)
        
        print(f"\nText: {test_text}")
        print(f"Predicted type: {result['document_type']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"\nTop 3 probabilities:")
        sorted_probs = sorted(
            result['probabilities'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for label, prob in sorted_probs:
            print(f"  {label}: {prob:.2%}")
    
    # Test semantic search (if loaded)
    if ml.rag_embeddings:
        print("\n" + "=" * 70)
        print("TEST: SEMANTIC SEARCH")
        print("=" * 70)
        
        query = "car accident with back injury"
        results = ml.search_similar_cases(query, top_k=3)
        
        print(f"\nQuery: '{query}'")
        print(f"Found {len(results)} similar cases:")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Similarity: {result['similarity']:.3f}")
            print(f"   Type: {result['document_type']}")
            print(f"   Preview: {result['text_preview']}")
