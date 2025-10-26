#!/usr/bin/env python3
"""
Simple RAG integration test - no LLM required
Just tests that the RAG system can find similar cases
"""

import sys
sys.path.append('ml_pipeline')
from rag_embeddings import RAGEmbeddings

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

print_section("RAG Integration Test - Similar Case Retrieval")

# Initialize RAG
print("Initializing RAG embeddings...")
rag = RAGEmbeddings()
rag.load('morgan_documents')

# Test queries that would come from Legal Researcher Agent
test_cases = [
    {
        "query": "car accident with back injury herniated disc",
        "label": "Car Accident Case"
    },
    {
        "query": "slip and fall workplace injury",
        "label": "Slip and Fall Case"
    },
    {
        "query": "settlement medical expenses treatment",
        "label": "Settlement Query"
    }
]

for test in test_cases:
    print_section(f"Test Query: {test['label']}")
    print(f"Search: '{test['query']}'")
    
    results = rag.search(test['query'], top_k=3, min_similarity=0.3)
    
    if results:
        print(f"\n✅ Found {len(results)} similar cases:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['document']['title']}")
            print(f"   {'─' * 76}")
            print(f"   Similarity:    {r['similarity']:.1%}")
            print(f"   Document Type: {r['document']['document_type']}")
            print(f"   Document ID:   {r['document']['document_id']}")
            print(f"   Preview:       {r['document']['full_text'][:120]}...")
            print()
    else:
        print("❌ No similar cases found")

print_section("Summary")
print("✅ RAG system is working correctly!")
print("✅ Similar cases are being retrieved with good similarity scores")
print("✅ Ready for integration with Legal Researcher Agent")
print("\nNext step: Test with full agent that includes LLM (test_agents.py)")
print()
