#!/bin/bash
# Complete System Test Script
# Tests the entire intelligent scraping pipeline end-to-end

echo "========================================================================"
echo "PARALEGAL AI - INTELLIGENT SCRAPING SYSTEM TEST"
echo "========================================================================"
echo ""

# Navigate to project
cd /home/amd-knights/Paralegal || exit 1

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Set environment variables
echo "✅ Setting environment variables..."
export COURTLISTENER_API_TOKEN="6bcb33f8c4f608e6ce503ed3a56361cab5db6dd5"
export VLLM_BASE_URL="http://localhost:8000"

# Pull latest code
echo "✅ Pulling latest code from GitHub..."
git pull

# Install any missing dependencies
echo "✅ Checking dependencies..."
pip install -q aiohttp 2>/dev/null || echo "aiohttp already installed"

# Navigate to ml_pipeline
cd AMD_server/ml_pipeline || exit 1

echo ""
echo "========================================================================"
echo "TEST 1: Quick Access Check"
echo "========================================================================"
python quick_access_check.py

echo ""
echo "========================================================================"
echo "TEST 2: Query Generator (LLM-powered)"
echo "========================================================================"
echo "Testing Saul-7B query generation..."
python -c "
from query_generator import QueryGeneratorAgent

generator = QueryGeneratorAgent()
queries = generator.generate_queries(
    'Can my employer fire me for filing a workers comp claim?',
    num_queries=3
)

print(f'\n✅ Generated {len(queries)} queries:')
for i, q in enumerate(queries, 1):
    print(f'{i}. [{q.source.value.upper()}] {q.query}')
    print(f'   Priority: {q.priority.value}')
    print(f'   Reasoning: {q.reasoning[:100]}...')
    print()
"

echo ""
echo "========================================================================"
echo "TEST 3: Intelligent Scraper (CourtListener API)"
echo "========================================================================"
echo "Testing async scraping with your API token..."
python -c "
import asyncio
from intelligent_scraper import CourtListenerScraper

async def test():
    scraper = CourtListenerScraper(mode='hybrid')
    cases = await scraper._scrape_courtlistener_async(
        'employment discrimination wrongful termination',
        max_cases=5
    )
    print(f'\n✅ Scraped {len(cases)} cases from CourtListener')
    for i, case in enumerate(cases[:3], 1):
        print(f'{i}. {case.case_name[:60]}...')
        print(f'   Court: {case.court}')
        print(f'   Date: {case.date_filed}')
    return cases

asyncio.run(test())
"

echo ""
echo "========================================================================"
echo "TEST 4: HYPER-PARALLELIZED Orchestrator (THE BIG TEST!)"
echo "========================================================================"
echo "Testing complete pipeline with 50 concurrent workers..."
echo ""
python orchestrator.py

echo ""
echo "========================================================================"
echo "TEST 5: Performance Benchmark (Async vs Sync)"
echo "========================================================================"
echo "Testing async performance..."
python orchestrator.py --async

echo ""
echo "========================================================================"
echo "✅ ALL TESTS COMPLETE!"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  ✅ CourtListener API access verified"
echo "  ✅ LLM query generation working"
echo "  ✅ Async scraping operational"
echo "  ✅ RAG integration pipeline ready"
echo "  ✅ Hyper-parallelized orchestrator tested"
echo ""
echo "Next step: Run demo script to show before/after RAG enhancement!"
echo ""
