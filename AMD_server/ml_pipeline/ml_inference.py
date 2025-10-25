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
        load_audio_transcriber: bool = True
    ):
        """
        Initialize ML inference with all models.
        
        Args:
            models_dir: Directory containing trained models
            load_document_classifier: Load document classification model
            load_rag_embeddings: Load RAG embeddings for semantic search
            load_audio_transcriber: Load audio transcription model
        """
        self.models_dir = models_dir or str(Path(__file__).parent / "trained_models")
        
        print("=" * 70)
        print("INITIALIZING ML INFERENCE")
        print("=" * 70)
        
        # Initialize components
        self.document_classifier = None
        self.rag_embeddings = None
        self.audio_transcriber = None
        
        # Load models
        if load_document_classifier:
            self._load_document_classifier()
        
        if load_rag_embeddings:
            self._load_rag_embeddings()
        
        if load_audio_transcriber:
            self._load_audio_transcriber()
        
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
