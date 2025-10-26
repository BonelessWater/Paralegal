"""
LLM-Powered Query Generator
Uses Saul-7B to generate intelligent legal search queries from user questions.
Determines search strategy: CourtListener (common) vs LexisNexis (rare/premium).
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchSource(Enum):
    """Legal database source selection"""
    COURTLISTENER = "courtlistener"  # FREE, common cases, millions of opinions
    LEXISNEXIS = "lexisnexis"  # Premium, rare cases, secondary sources
    BOTH = "both"  # Use both sources


class QueryPriority(Enum):
    """Query importance/urgency level"""
    HIGH = "high"  # Critical, rare cases - use LexisNexis
    MEDIUM = "medium"  # Standard research - use both
    LOW = "low"  # Common cases - CourtListener only


@dataclass
class GeneratedQuery:
    """Represents a generated search query with metadata"""
    query: str
    source: SearchSource
    priority: QueryPriority
    reasoning: str
    expected_results: str
    search_terms: List[str]
    filters: Dict[str, str]
    
    def to_dict(self) -> Dict:
        return {
            'query': self.query,
            'source': self.source.value,
            'priority': self.priority.value,
            'reasoning': self.reasoning,
            'expected_results': self.expected_results,
            'search_terms': self.search_terms,
            'filters': self.filters
        }


class QueryGeneratorAgent:
    """
    LLM-powered agent that generates optimized legal search queries.
    
    Features:
    - Analyzes user questions to extract legal concepts
    - Generates multiple search query variations
    - Determines optimal source (CourtListener vs LexisNexis)
    - Prioritizes queries by importance/rarity
    - Suggests search filters and parameters
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/v1", api_key: str = "dummy"):
        """
        Initialize the query generator.
        
        Args:
            base_url: vLLM server URL (default: localhost:8000)
            api_key: API key (not needed for local vLLM, use "dummy")
        """
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=60.0)
        
        # Auto-detect model from vLLM server
        try:
            models = self.client.models.list()
            self.model = models.data[0].id if models.data else "neuralmagic/Llama-3.2-1B-Instruct-FP8"
        except Exception as e:
            logger.warning(f"Could not detect model from server: {e}")
            self.model = "neuralmagic/Llama-3.2-1B-Instruct-FP8"
        
        logger.info(f"Query generator initialized with model: {self.model}")
    
    def generate_queries(self, user_question: str, num_queries: int = 3) -> List[GeneratedQuery]:
        """
        Generate optimized search queries from a user question.
        
        Args:
            user_question: User's legal question
            num_queries: Number of query variations to generate
            
        Returns:
            List of GeneratedQuery objects
        """
        logger.info(f"Generating {num_queries} queries for: '{user_question}'")
        
        # Build the prompt for Saul-7B
        prompt = self._build_query_generation_prompt(user_question, num_queries)
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse response into GeneratedQuery objects
        queries = self._parse_llm_response(response, user_question)
        
        logger.info(f"Generated {len(queries)} queries")
        return queries
    
    def _build_query_generation_prompt(self, user_question: str, num_queries: int) -> str:
        """Build the prompt for query generation"""
        prompt = f"""You are a legal research expert AI. Given a user's legal question, generate {num_queries} optimized search queries for legal databases.

For each query, determine:
1. The search query string (optimized for case law databases)
2. Which source to use:
   - CourtListener: FREE, millions of opinions, common cases, federal & state courts
   - LexisNexis: Premium, rare cases, secondary sources, treatises, recent cases
   - Both: Use both sources for comprehensive research
3. Priority level:
   - HIGH: Rare, specific, or recent cases requiring premium access
   - MEDIUM: Standard legal research, use both sources
   - LOW: Common legal concepts, CourtListener sufficient
4. Reasoning for source selection
5. Expected type of results
6. Key search terms to use
7. Suggested filters (jurisdiction, date range, court, etc.)

User Question: "{user_question}"

Respond in valid JSON format with an array of queries. Example:
```json
{{
  "queries": [
    {{
      "query": "employment discrimination wrongful termination retaliation",
      "source": "courtlistener",
      "priority": "low",
      "reasoning": "Common employment law issue with many precedents available in free databases",
      "expected_results": "Federal and state court opinions on employment discrimination claims",
      "search_terms": ["employment discrimination", "wrongful termination", "retaliation", "Title VII"],
      "filters": {{
        "jurisdiction": "federal",
        "date_after": "2015-01-01",
        "court_type": "appellate"
      }}
    }},
    {{
      "query": "employment discrimination disparate impact statistical evidence",
      "source": "both",
      "priority": "medium",
      "reasoning": "Requires both common cases for precedent and premium sources for expert analysis",
      "expected_results": "Cases discussing statistical methods in discrimination cases, plus secondary sources",
      "search_terms": ["disparate impact", "statistical evidence", "pattern and practice"],
      "filters": {{
        "jurisdiction": "any",
        "date_after": "2010-01-01"
      }}
    }}
  ]
}}
```

Generate {num_queries} distinct queries now:"""
        
        return prompt
    
    def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """Call the Saul-7B LLM via vLLM API"""
        try:
            # Combine system message into user prompt for Saul-7B compatibility
            full_prompt = "You are a legal research expert AI that generates optimized search queries for legal databases.\n\n" + prompt
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            logger.info(f"LLM response received ({len(result)} chars)")
            return result
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            # Fallback to simple query generation
            return self._fallback_query_generation(prompt)
    
    def _fallback_query_generation(self, prompt: str) -> str:
        """Fallback query generation if LLM fails"""
        logger.warning("Using fallback query generation")
        
        # Extract user question from prompt
        import re
        question_match = re.search(r'User Question: "(.*?)"', prompt)
        user_question = question_match.group(1) if question_match else "legal research"
        
        # Generate simple queries
        fallback = {
            "queries": [
                {
                    "query": user_question,
                    "source": "courtlistener",
                    "priority": "medium",
                    "reasoning": "Fallback query - using user question directly",
                    "expected_results": "Legal cases related to query",
                    "search_terms": user_question.split(),
                    "filters": {}
                }
            ]
        }
        
        return json.dumps(fallback)
    
    def _parse_llm_response(self, response: str, user_question: str) -> List[GeneratedQuery]:
        """Parse LLM JSON response into GeneratedQuery objects"""
        try:
            # Extract JSON from response (may have markdown formatting)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            queries = []
            
            # Handle both dict with "queries" key and direct array
            query_list = data.get("queries", []) if isinstance(data, dict) else data
            
            for q in query_list:
                try:
                    query = GeneratedQuery(
                        query=q.get("query", user_question),
                        source=SearchSource(q.get("source", "courtlistener")),
                        priority=QueryPriority(q.get("priority", "medium")),
                        reasoning=q.get("reasoning", ""),
                        expected_results=q.get("expected_results", ""),
                        search_terms=q.get("search_terms", []),
                        filters=q.get("filters", {})
                    )
                    queries.append(query)
                except Exception as e:
                    logger.error(f"Error parsing query: {e}")
                    continue
            
            return queries
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response: {response[:500]}")
            # Return fallback query
            return [GeneratedQuery(
                query=user_question,
                source=SearchSource.COURTLISTENER,
                priority=QueryPriority.MEDIUM,
                reasoning="Fallback - JSON parsing failed",
                expected_results="Legal cases",
                search_terms=user_question.split(),
                filters={}
            )]
    
    def analyze_query_difficulty(self, user_question: str) -> Tuple[QueryPriority, str]:
        """
        Analyze how difficult/rare a legal question is.
        
        Returns:
            Tuple of (priority level, reasoning)
        """
        # Use LLM to assess difficulty
        prompt = f"""Analyze this legal question and determine if it requires:
- HIGH priority: Rare, specific, or very recent cases (use premium LexisNexis)
- MEDIUM priority: Standard legal research (use both sources)
- LOW priority: Common legal concepts (free CourtListener sufficient)

Question: "{user_question}"

Respond with just: HIGH, MEDIUM, or LOW followed by a brief reason."""
        
        response = self._call_llm(prompt, temperature=0.3, max_tokens=100)
        
        # Parse priority
        response_upper = response.upper()
        if "HIGH" in response_upper:
            priority = QueryPriority.HIGH
        elif "LOW" in response_upper:
            priority = QueryPriority.LOW
        else:
            priority = QueryPriority.MEDIUM
        
        return priority, response.strip()
    
    def suggest_filters(self, query: str) -> Dict[str, str]:
        """
        Suggest database filters based on query content.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary of suggested filters
        """
        filters = {}
        
        query_lower = query.lower()
        
        # Detect jurisdiction
        if any(word in query_lower for word in ['federal', 'supreme court', 'circuit']):
            filters['jurisdiction'] = 'federal'
        elif any(word in query_lower for word in ['state', 'california', 'new york', 'texas']):
            filters['jurisdiction'] = 'state'
        
        # Detect court type
        if 'appellate' in query_lower or 'appeal' in query_lower:
            filters['court_type'] = 'appellate'
        elif 'district' in query_lower or 'trial' in query_lower:
            filters['court_type'] = 'district'
        
        # Suggest date range (last 10 years for most queries)
        filters['date_after'] = '2015-01-01'
        
        # Detect if recent cases needed
        if any(word in query_lower for word in ['recent', 'latest', 'current', '2024', '2025']):
            filters['date_after'] = '2020-01-01'
        
        return filters


def test_query_generator():
    """Test the query generator with sample questions"""
    logger.info("=" * 70)
    logger.info("Testing LLM-Powered Query Generator")
    logger.info("=" * 70)
    
    generator = QueryGeneratorAgent()
    
    # Test questions
    test_questions = [
        "Can my employer fire me for filing a workers compensation claim?",
        "What are the requirements for proving breach of contract in California?",
        "How do I challenge a non-compete agreement after being terminated?"
    ]
    
    for question in test_questions:
        logger.info(f"\n{'=' * 70}")
        logger.info(f"USER QUESTION: {question}")
        logger.info(f"{'=' * 70}")
        
        # Analyze difficulty
        priority, reasoning = generator.analyze_query_difficulty(question)
        logger.info(f"\nDifficulty Analysis:")
        logger.info(f"  Priority: {priority.value.upper()}")
        logger.info(f"  Reasoning: {reasoning}")
        
        # Generate queries
        queries = generator.generate_queries(question, num_queries=3)
        
        logger.info(f"\nGenerated {len(queries)} Search Queries:")
        for i, q in enumerate(queries, 1):
            logger.info(f"\n  Query {i}:")
            logger.info(f"    Search: {q.query}")
            logger.info(f"    Source: {q.source.value.upper()}")
            logger.info(f"    Priority: {q.priority.value.upper()}")
            logger.info(f"    Reasoning: {q.reasoning}")
            logger.info(f"    Expected: {q.expected_results}")
            logger.info(f"    Terms: {', '.join(q.search_terms)}")
            if q.filters:
                logger.info(f"    Filters: {json.dumps(q.filters, indent=6)}")
        
        # Save to JSON
        output_dir = Path(__file__).parent / "data" / "generated_queries"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"queries_{question[:30].replace(' ', '_').replace('?', '')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'question': question,
                'priority': priority.value,
                'queries': [q.to_dict() for q in queries]
            }, f, indent=2)
        
        logger.info(f"\n  Saved to: {output_file}")
    
    logger.info(f"\n{'=' * 70}")
    logger.info("Query Generation Test Complete!")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    test_query_generator()
