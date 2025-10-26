"""
RAG Embeddings Generator for Legal Document Search

Generates semantic embeddings for Morgan & Morgan documents using sentence-transformers.
Enables semantic search: "Find cases similar to car accident with back injury"

Usage:
    from rag_embeddings import RAGEmbeddings
    
    # Generate embeddings for all documents
    rag = RAGEmbeddings()
    rag.generate_embeddings()
    
    # Search for similar cases
    results = rag.search("client injured in parking lot slip and fall")
    for doc in results:
        print(f"{doc['title']}: {doc['similarity']:.3f}")
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pickle
from sentence_transformers import SentenceTransformer
import faiss


class RAGEmbeddings:
    """
    Generate and manage semantic embeddings for legal documents.
    
    Uses sentence-transformers to convert documents into dense vectors
    that capture semantic meaning, enabling similarity search.
    
    Attributes:
        model_name: HuggingFace model for embeddings
        model: Loaded sentence-transformer model
        index: FAISS index for fast similarity search
        documents: Document metadata
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        embeddings_dir: str = None
    ):
        """
        Initialize RAG embeddings generator.
        
        Args:
            model_name: Sentence-transformer model name
                - "all-MiniLM-L6-v2": Fast, 384-dim, good for most use cases
                - "all-mpnet-base-v2": Slower, 768-dim, better accuracy
                - "multi-qa-mpnet-base-dot-v1": Optimized for Q&A
            embeddings_dir: Directory to save/load embeddings
        """
        self.model_name = model_name
        self.embeddings_dir = embeddings_dir or str(
            Path(__file__).parent / "embeddings"
        )
        
        # Create embeddings directory
        Path(self.embeddings_dir).mkdir(parents=True, exist_ok=True)
        
        # Load sentence-transformer model
        print(f"Loading sentence-transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Placeholders
        self.index = None
        self.documents = []
        self.embeddings = None
    
    def load_documents(self, data_loader=None) -> List[Dict]:
        """
        Load documents from database.
        
        Args:
            data_loader: Optional DataLoader instance. If None, creates new one.
        
        Returns:
            List of document dictionaries with text and metadata
        """
        if data_loader is None:
            from data_loader import DataLoader
            data_loader = DataLoader()
        
        print("Loading documents from database...")
        documents = data_loader.load_morgan_documents()
        
        print(f"Loaded {len(documents)} documents")
        return documents
    
    def generate_embeddings(
        self,
        documents: List[Dict] = None,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for all documents.
        
        Args:
            documents: List of document dicts or DataFrame. If None, loads from database.
            batch_size: Number of documents to process at once
            show_progress: Show progress bar during encoding
        
        Returns:
            Numpy array of embeddings, shape (num_docs, embedding_dim)
        """
        # Load documents if not provided
        if documents is None:
            documents = self.load_documents()
        
        # Convert DataFrame to list of dicts if needed
        if hasattr(documents, 'to_dict'):
            # It's a DataFrame
            documents = documents.to_dict('records')
        
        self.documents = documents
        
        # Extract text from documents
        texts = []
        for doc in documents:
            # Combine title and full_text for richer embeddings
            text = f"{doc['title']}\n\n{doc['full_text']}"
            texts.append(text)
        
        print(f"\nGenerating embeddings for {len(texts)} documents...")
        print(f"Model: {self.model_name}")
        print(f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
        # Generate embeddings
        self.embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        print(f"✓ Generated embeddings: {self.embeddings.shape}")
        
        return self.embeddings
    
    def build_index(self, embeddings: np.ndarray = None):
        """
        Build FAISS index for fast similarity search.
        
        Args:
            embeddings: Embeddings array. If None, uses self.embeddings.
        """
        if embeddings is None:
            embeddings = self.embeddings
        
        if embeddings is None:
            raise ValueError("No embeddings available. Run generate_embeddings() first.")
        
        print("\nBuilding FAISS index...")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index (Inner Product = cosine similarity for normalized vectors)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        print(f"✓ Built FAISS index with {self.index.ntotal} vectors")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        Search for documents similar to query.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
        
        Returns:
            List of dictionaries with matching documents and scores:
                - document: Original document dict
                - similarity: Cosine similarity score (0-1)
                - rank: Result rank (1-based)
        """
        if self.index is None:
            raise ValueError("Index not built. Run build_index() first.")
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search index
        similarities, indices = self.index.search(
            query_embedding.astype('float32'),
            top_k
        )
        
        # Format results
        results = []
        for rank, (idx, similarity) in enumerate(zip(indices[0], similarities[0]), 1):
            if similarity >= min_similarity:
                results.append({
                    'document': self.documents[idx],
                    'similarity': float(similarity),
                    'rank': rank
                })
        
        return results
    
    def save(self, name: str = "default"):
        """
        Save embeddings, index, and metadata to disk.
        
        Args:
            name: Name for this embedding set
        """
        save_dir = Path(self.embeddings_dir) / name
        save_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nSaving embeddings to {save_dir}")
        
        # Save embeddings
        np.save(save_dir / "embeddings.npy", self.embeddings)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_dir / "faiss.index"))
        
        # Save document metadata
        with open(save_dir / "documents.pkl", 'wb') as f:
            pickle.dump(self.documents, f)
        
        # Save configuration
        config = {
            'model_name': self.model_name,
            'num_documents': len(self.documents),
            'embedding_dim': self.embeddings.shape[1]
        }
        with open(save_dir / "config.pkl", 'wb') as f:
            pickle.dump(config, f)
        
        print(f"✓ Saved embeddings, index, and metadata")
    
    def load(self, name: str = "default"):
        """
        Load saved embeddings, index, and metadata.
        
        Args:
            name: Name of embedding set to load
        """
        load_dir = Path(self.embeddings_dir) / name
        
        if not load_dir.exists():
            raise FileNotFoundError(f"Embeddings not found: {load_dir}")
        
        print(f"\nLoading embeddings from {load_dir}")
        
        # Load configuration
        with open(load_dir / "config.pkl", 'rb') as f:
            config = pickle.load(f)
        
        # Verify model matches
        if config['model_name'] != self.model_name:
            print(f"Warning: Loaded embeddings use {config['model_name']}, "
                  f"but current model is {self.model_name}")
        
        # Load embeddings
        self.embeddings = np.load(load_dir / "embeddings.npy")
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_dir / "faiss.index"))
        
        # Load document metadata
        with open(load_dir / "documents.pkl", 'rb') as f:
            self.documents = pickle.load(f)
        
        print(f"✓ Loaded {len(self.documents)} documents with "
              f"{config['embedding_dim']}-dim embeddings")
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics about embeddings.
        
        Returns:
            Dictionary with embedding statistics
        """
        if self.embeddings is None:
            return {'status': 'No embeddings generated'}
        
        return {
            'num_documents': len(self.documents),
            'embedding_dim': self.embeddings.shape[1],
            'model_name': self.model_name,
            'index_built': self.index is not None,
            'index_size': self.index.ntotal if self.index else 0
        }


def generate_embeddings_pipeline(
    save_name: str = "morgan_documents",
    model_name: str = "all-MiniLM-L6-v2"
) -> RAGEmbeddings:
    """
    Complete pipeline to generate and save embeddings.
    
    Args:
        save_name: Name for saved embeddings
        model_name: Sentence-transformer model to use
    
    Returns:
        RAGEmbeddings instance with generated embeddings
    """
    print("=" * 70)
    print("RAG EMBEDDINGS GENERATION PIPELINE")
    print("=" * 70)
    
    # Initialize
    rag = RAGEmbeddings(model_name=model_name)
    
    # Load documents
    documents = rag.load_documents()
    
    # Generate embeddings
    rag.generate_embeddings(documents)
    
    # Build search index
    rag.build_index()
    
    # Save to disk
    rag.save(save_name)
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    summary = rag.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    return rag


# Quick usage example
if __name__ == "__main__":
    import sys
    
    # Generate embeddings
    rag = generate_embeddings_pipeline()
    
    # Test search
    print("\n" + "=" * 70)
    print("TESTING SEMANTIC SEARCH")
    print("=" * 70)
    
    test_queries = [
        "car accident with back injury",
        "settlement offer for medical expenses",
        "police report about incident"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 70)
        
        results = rag.search(query, top_k=3)
        
        for result in results:
            doc = result['document']
            similarity = result['similarity']
            rank = result['rank']
            
            print(f"\n{rank}. {doc['title']} (similarity: {similarity:.3f})")
            print(f"   Type: {doc['document_type']}")
            print(f"   Preview: {doc['full_text'][:150]}...")
