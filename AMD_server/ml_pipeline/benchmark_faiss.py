#!/usr/bin/env python3
"""
Benchmark FAISS Index Performance
Compares Flat (exact) vs HNSW (approximate) search
"""

import time
import numpy as np
from rag_embeddings import RAGEmbeddings

def benchmark_search(rag, queries, top_k=5, num_runs=10):
    """Benchmark search performance"""
    latencies = []
    
    for _ in range(num_runs):
        start = time.time()
        for query in queries:
            results = rag.search(query, top_k=top_k)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        latencies.append(elapsed)
    
    return {
        'mean': np.mean(latencies),
        'std': np.std(latencies),
        'min': np.min(latencies),
        'max': np.max(latencies),
        'median': np.median(latencies)
    }

def main():
    print("=" * 80)
    print("FAISS INDEX BENCHMARK: FLAT vs HNSW")
    print("=" * 80)
    
    # Test queries
    test_queries = [
        "car accident with back injury",
        "slip and fall in parking lot",
        "settlement offer for medical expenses",
        "police report incident description",
        "medical bills and treatment records"
    ]
    
    print(f"\nTest Configuration:")
    print(f"  Queries: {len(test_queries)}")
    print(f"  Runs per test: 10")
    print(f"  Top-K results: 5")
    
    # =========================================================================
    # Test 1: Flat Index (Exact Search)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: FLAT INDEX (Exact Search, 100% Recall)")
    print("=" * 80)
    
    print("\nLoading embeddings with Flat index...")
    rag_flat = RAGEmbeddings()
    rag_flat.load("morgan_documents")
    
    # Rebuild with Flat index
    print("\nRebuilding with Flat index...")
    rag_flat.build_index(use_hnsw=False)
    
    print("\nRunning benchmark...")
    flat_stats = benchmark_search(rag_flat, test_queries)
    
    print(f"\nFlat Index Results:")
    print(f"  Mean latency:   {flat_stats['mean']:.2f} ms")
    print(f"  Median latency: {flat_stats['median']:.2f} ms")
    print(f"  Std deviation:  {flat_stats['std']:.2f} ms")
    print(f"  Min latency:    {flat_stats['min']:.2f} ms")
    print(f"  Max latency:    {flat_stats['max']:.2f} ms")
    
    # =========================================================================
    # Test 2: HNSW Index (Approximate Search)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: HNSW INDEX (Approximate Search, ~95-99% Recall)")
    print("=" * 80)
    
    print("\nLoading embeddings with HNSW index...")
    rag_hnsw = RAGEmbeddings()
    rag_hnsw.load("morgan_documents")
    
    # Rebuild with HNSW index
    print("\nRebuilding with HNSW index...")
    rag_hnsw.build_index(use_hnsw=True, M=32, efConstruction=200, efSearch=64)
    
    print("\nRunning benchmark...")
    hnsw_stats = benchmark_search(rag_hnsw, test_queries)
    
    print(f"\nHNSW Index Results:")
    print(f"  Mean latency:   {hnsw_stats['mean']:.2f} ms")
    print(f"  Median latency: {hnsw_stats['median']:.2f} ms")
    print(f"  Std deviation:  {hnsw_stats['std']:.2f} ms")
    print(f"  Min latency:    {hnsw_stats['min']:.2f} ms")
    print(f"  Max latency:    {hnsw_stats['max']:.2f} ms")
    
    # =========================================================================
    # Comparison
    # =========================================================================
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    
    speedup = flat_stats['mean'] / hnsw_stats['mean']
    
    print(f"\n{'Metric':<20} {'Flat Index':<15} {'HNSW Index':<15} {'Speedup':<10}")
    print("-" * 80)
    print(f"{'Mean latency':<20} {flat_stats['mean']:>10.2f} ms  {hnsw_stats['mean']:>10.2f} ms  {speedup:>6.2f}x")
    print(f"{'Median latency':<20} {flat_stats['median']:>10.2f} ms  {hnsw_stats['median']:>10.2f} ms")
    print(f"{'Index type':<20} {'Exact':<15} {'Approximate':<15}")
    print(f"{'Recall':<20} {'100%':<15} {'~95-99%':<15}")
    
    # =========================================================================
    # Quality Check: Compare top results
    # =========================================================================
    print("\n" + "=" * 80)
    print("QUALITY CHECK: Comparing Top Results")
    print("=" * 80)
    
    for query in test_queries[:2]:  # Test first 2 queries
        print(f"\nQuery: '{query}'")
        print("-" * 80)
        
        flat_results = rag_flat.search(query, top_k=3)
        hnsw_results = rag_hnsw.search(query, top_k=3)
        
        # Check if top-3 results match
        flat_ids = [r['document']['document_id'] for r in flat_results]
        hnsw_ids = [r['document']['document_id'] for r in hnsw_results]
        
        matches = sum(1 for fid in flat_ids if fid in hnsw_ids)
        recall = (matches / len(flat_ids)) * 100
        
        print(f"  Flat top-3: {', '.join([str(id) for id in flat_ids])}")
        print(f"  HNSW top-3: {', '.join([str(id) for id in hnsw_ids])}")
        print(f"  Match rate: {matches}/3 ({recall:.0f}%)")
        
        if recall >= 66:
            print(f"  ✅ Good recall")
        else:
            print(f"  ⚠️  Lower recall, consider increasing efSearch")
    
    # =========================================================================
    # Recommendations
    # =========================================================================
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if speedup > 1.5:
        print(f"\n✅ HNSW is {speedup:.1f}x faster!")
        print("   Recommendation: Use HNSW for production")
    elif speedup > 1.0:
        print(f"\n⚠️  HNSW is {speedup:.1f}x faster (modest improvement)")
        print("   Note: Small dataset (39 docs). HNSW shines with 1000+ documents")
    else:
        print(f"\n⚠️  Flat is faster ({1/speedup:.1f}x)")
        print("   Note: With small datasets, exact search can be faster")
    
    print("\nHNSW Performance Scaling:")
    print("  • 100 docs:     ~1-2x faster than Flat")
    print("  • 1,000 docs:   ~5-10x faster than Flat")
    print("  • 10,000 docs:  ~20-50x faster than Flat")
    print("  • 100,000 docs: ~50-100x faster than Flat")
    
    print("\nCurrent dataset: 39 documents")
    print("Expected speedup: Minimal (dataset too small)")
    print("HNSW benefit: Will scale much better as you add more documents")
    
    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
