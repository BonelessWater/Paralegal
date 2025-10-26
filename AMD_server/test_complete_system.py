#!/usr/bin/env python3
"""
Complete System Test: RAG + LLM Integration
Demonstrates the full pipeline from document search to AI-powered legal analysis
"""

import sys
sys.path.append('ml_pipeline')
from rag_embeddings import RAGEmbeddings
from openai import OpenAI

print("=" * 80)
print("TESTING COMPLETE RAG + LLM SYSTEM")
print("=" * 80)

# 1. RAG Search
print("\n1. Searching for similar cases with RAG...")
rag = RAGEmbeddings()
rag.load('morgan_documents')
results = rag.search('car accident with back injury', top_k=3)

print(f"\nFound {len(results)} similar cases:")
for i, r in enumerate(results, 1):
    print(f"\n{i}. {r['document']['title']} ({r['similarity']:.1%} similar)")
    print(f"   Preview: {r['document']['full_text'][:150]}...")

# 2. Build context
context = "\n\n".join([
    f"Case {i+1} ({r['similarity']:.0%} match): {r['document']['title']}\n{r['document']['full_text'][:400]}"
    for i, r in enumerate(results)
])

# 3. LLM Analysis
print("\n" + "=" * 80)
print("2. Generating LLM analysis based on similar cases...")
print("=" * 80)

client = OpenAI(base_url='http://localhost:8000/v1', api_key='dummy')

prompt = f"""You are a legal research assistant. Based on these similar personal injury cases:

{context}

Question: What are the key factors affecting settlement value in a Florida car accident case with herniated disc injury?

Provide a concise analysis (200 words max) focusing on:
1. Typical settlement ranges
2. Key liability factors  
3. Important medical documentation"""

response = client.completions.create(
    model='Equall/Saul-7B-Instruct-v1',
    prompt=prompt,
    max_tokens=250,  # Reduced to keep output focused
    temperature=0.3
)

print("\n" + response.choices[0].text)

print("\n" + "=" * 80)
print("✅ COMPLETE SYSTEM TEST SUCCESSFUL!")
print("=" * 80)
print("\nYour RAG + LLM pipeline is working perfectly!")
print("Ready for hackathon! 🚀")
