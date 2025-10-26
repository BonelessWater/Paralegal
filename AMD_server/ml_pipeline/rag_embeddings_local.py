#!/usr/bin/env python3
"""
RAG Embeddings Generation - LOCAL DATABASE VERSION
Uses localhost instead of external IP for database connection
"""

import sys
import os

# Import the RAG embeddings class
from rag_embeddings import RAGEmbeddings

# Override the data loader to use localhost
from data_loader import DataLoader

def generate_embeddings_pipeline_local(
    save_name: str = "morgan_documents",
    model_name: str = "all-MiniLM-L6-v2"
):
    """
    Generate embeddings using LOCAL database connection
    
    Args:
        save_name: Name for saved embeddings
        model_name: Sentence-transformer model to use
    
    Returns:
        RAGEmbeddings instance with generated embeddings
    """
    print("=" * 70)
    print("RAG EMBEDDINGS GENERATION PIPELINE (LOCAL DB)")
    print("=" * 70)
    
    # Initialize with custom model name
    rag = RAGEmbeddings(model_name=model_name)
    
    # Create data loader with LOCALHOST connection
    print("\nConnecting to LOCAL database (localhost)...")
    data_loader = DataLoader(
        db_host="localhost",  # ← Changed from 134.199.202.8
        db_name="paralegal_db",
        db_user="paralegal_user",
        db_password="hackathon2024",
        db_port=5432
    )
    
    # Load documents from database
    print("Loading documents from database...")
    documents = rag.load_documents(data_loader=data_loader)
    
    # Generate embeddings
    print(f"\nGenerating embeddings using {model_name}...")
    rag.generate_embeddings(documents)
    
    # Build search index
    print("\nBuilding FAISS search index...")
    rag.build_index()
    
    # Save to disk
    print(f"\nSaving embeddings as '{save_name}'...")
    rag.save(save_name)
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    summary = rag.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    print("\n✅ Embeddings generated successfully!")
    print(f"✅ Saved to: embeddings/{save_name}/")
    
    return rag


if __name__ == "__main__":
    # Generate embeddings
    rag = generate_embeddings_pipeline_local()
    
    # Test search
    print("\n" + "=" * 70)
    print("TESTING SEMANTIC SEARCH")
    print("=" * 70)
    
    test_queries = [
        "car accident with back injury",
        "slip and fall in parking lot",
        "settlement offer for medical expenses"
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
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 70)
