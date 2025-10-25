# AI Agent Training & Pipeline Optimization Guide
## For AI Legal Tender Hackathon

---

## 🏗️ Current Architecture Assessment

### **What You Have Now:**
```
Client Input → Agent Selection → LLM Processing → Response
```

**Strengths:**
- ✅ 4 specialist agents with clear roles
- ✅ AMD vLLM for fast inference
- ✅ Modular design

**Weaknesses:**
- ❌ No feedback loop for improvement
- ❌ No standardized agent pipeline
- ❌ No prompt optimization process
- ❌ No quality metrics/evaluation

---

## 🚀 Optimized Pipeline Architecture

### **Recommended Structure:**

```
┌─────────────────────────────────────────────────────────────────┐
│  1. INPUT PROCESSING                                            │
│     ├─ Message Classifier (routes to correct agent)            │
│     ├─ Input Validation (format, completeness)                 │
│     └─ Context Enrichment (add relevant metadata)              │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. AGENT ORCHESTRATION                                         │
│     ├─ Agent Registry (manages all agents)                     │
│     ├─ Prompt Templates (versioned, optimized)                 │
│     └─ Chain-of-Thought Wrapper (for complex tasks)            │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. LLM INFERENCE (AMD vLLM)                                    │
│     ├─ Model: Llama 3.2 / Mistral (your choice)               │
│     ├─ Batching: Process multiple requests together            │
│     └─ Caching: Store common responses                         │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. OUTPUT REFINEMENT                                           │
│     ├─ Response Validator (check format, completeness)         │
│     ├─ Fact Checker (validate legal claims)                    │
│     └─ Tone Adjuster (ensure professionalism)                  │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. FEEDBACK & LEARNING                                         │
│     ├─ Human Feedback Collection (thumbs up/down)              │
│     ├─ Error Logging (track failures)                          │
│     └─ Prompt Improvement (iterative refinement)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Training Optimization Strategies

### **Strategy 1: Prompt Engineering (Fastest - No Model Training)**

**What:** Optimize prompts through iterative testing

**How:**
1. Create a test dataset of 20-30 sample inputs per agent
2. Run each agent with different prompt variations
3. Measure output quality (accuracy, completeness, tone)
4. Select best-performing prompts

**Example Prompt Evolution:**

```python
# Version 1 (Basic)
"You are a legal assistant. Respond to this client message."

# Version 2 (Better)
"You are a compassionate legal assistant specializing in personal injury.
Transform this messy client message into a professional response."

# Version 3 (Best - Current)
"You are a compassionate legal assistant specializing in personal injury law.
Guidelines:
- Maintain empathetic, professional tone
- Ask clarifying questions
- Avoid legal conclusions
- Explain next steps clearly
Input: {message}"

# Version 4 (Chain-of-Thought - For Complex Cases)
"You are a legal assistant. Follow these steps:
1. Identify the client's main concern
2. List missing information needed
3. Draft a professional response
4. Review for tone and completeness
Input: {message}"
```

**Time Investment:** 2-3 hours
**Impact:** 30-50% quality improvement

---

### **Strategy 2: Few-Shot Learning (Medium Effort)**

**What:** Provide example input/output pairs in the prompt

**How:**
```python
SYSTEM_PROMPT = """You are a legal assistant.

Example 1:
Input: "hey i got hurt at store help!!!"
Output: "Thank you for reaching out. I understand you were injured at a store. 
To better assist you, could you please provide:
- The name and location of the store
- The date and time of the incident
- A description of how the injury occurred
- Any medical treatment you've received"

Example 2:
Input: "fell on wet floor 3 weeks ago still hurts"
Output: "I'm sorry to hear about your injury. Slip and fall cases can be complex.
To evaluate your case, I need to know:
- Were there any warning signs about the wet floor?
- What injuries did you sustain?
- Have you seen a doctor? If so, what was the diagnosis?
- Do you have photos of the scene or your injuries?"

Now process this input:
{user_input}
"""
```

**Time Investment:** 4-6 hours
**Impact:** 40-60% quality improvement

---

### **Strategy 3: Retrieval-Augmented Generation (RAG)**

**What:** Give agents access to a knowledge base of legal precedents

**How:**
```python
# Create a simple legal knowledge base
knowledge_base = {
    "slip_and_fall": {
        "statute_of_limitations": "4 years in Florida",
        "key_factors": ["Property owner negligence", "Hazard visibility", "Injury severity"],
        "typical_settlements": "$10,000 - $50,000 for minor injuries"
    },
    "medical_malpractice": {
        "statute_of_limitations": "2 years in Florida",
        "key_factors": ["Standard of care breach", "Causation", "Damages"],
        "expert_testimony": "Required in most cases"
    }
}

# Inject relevant knowledge into prompts
def enhance_prompt_with_context(case_type, base_prompt):
    context = knowledge_base.get(case_type, {})
    return f"{base_prompt}\n\nRelevant Legal Context:\n{json.dumps(context, indent=2)}"
```

**Time Investment:** 6-8 hours (building knowledge base)
**Impact:** 50-70% quality improvement

---

### **Strategy 4: Fine-Tuning (Advanced - Only If Time Permits)**

**What:** Actually train the model on legal data

**⚠️ WARNING:** This is complex and time-consuming for a hackathon

**When to Consider:**
- You have 100+ labeled examples
- You have 8+ hours available
- You're comfortable with training scripts

**Better Alternatives for Hackathon:**
- Use a pre-trained legal model (e.g., `law-ai/InLegalBERT`)
- Focus on prompt engineering instead

---

## 🔧 Pipeline Structuring Best Practices

### **1. Create an Agent Registry**

```python
# backend/orchestrator/agent_registry.py

from backend.agents.client_communication_agent import ClientCommunicationAgent
from backend.agents.records_wrangler_agent import RecordsWranglerAgent
from backend.agents.legal_researcher_agent import LegalResearcherAgent
from backend.agents.evidence_sorter_agent import EvidenceSorterAgent

class AgentRegistry:
    """Central registry for all agents"""
    
    def __init__(self, llm_client):
        self.agents = {
            "client_communication": ClientCommunicationAgent(llm_client),
            "records_wrangler": RecordsWranglerAgent(llm_client),
            "legal_researcher": LegalResearcherAgent(llm_client),
            "evidence_sorter": EvidenceSorterAgent(llm_client)
        }
    
    def get_agent(self, agent_type: str):
        """Get agent by type"""
        return self.agents.get(agent_type)
    
    def list_agents(self):
        """List all available agents"""
        return list(self.agents.keys())
```

---

### **2. Build a Message Classifier**

```python
# backend/orchestrator/message_classifier.py

from typing import Dict
import re

class MessageClassifier:
    """Classifies incoming messages to route to correct agent"""
    
    # Keywords that suggest specific agent types
    PATTERNS = {
        "evidence_sorter": [
            r"document", r"photo", r"image", r"scan", r"pdf",
            r"medical record", r"bill", r"report"
        ],
        "records_wrangler": [
            r"medical records?", r"hospital", r"doctor",
            r"treatment", r"diagnosis", r"x-ray", r"MRI"
        ],
        "legal_researcher": [
            r"similar case", r"precedent", r"settlement",
            r"lawsuit", r"sue", r"case value", r"worth"
        ],
        "client_communication": [
            r"help", r"question", r"confused", r"what.*do",
            r"injured", r"hurt", r"accident"
        ]
    }
    
    def classify(self, message: str) -> str:
        """
        Classify message to determine which agent should handle it
        
        Args:
            message: Client message text
            
        Returns:
            Agent type identifier
        """
        message_lower = message.lower()
        
        # Check for evidence (documents/images)
        if self._matches_patterns(message_lower, "evidence_sorter"):
            return "evidence_sorter"
        
        # Check for records requests
        if self._matches_patterns(message_lower, "records_wrangler"):
            return "records_wrangler"
        
        # Check for legal research
        if self._matches_patterns(message_lower, "legal_researcher"):
            return "legal_researcher"
        
        # Default to client communication
        return "client_communication"
    
    def _matches_patterns(self, text: str, category: str) -> bool:
        """Check if text matches any patterns for a category"""
        patterns = self.PATTERNS.get(category, [])
        return any(re.search(pattern, text) for pattern in patterns)
```

---

### **3. Create a Unified Pipeline Orchestrator**

```python
# backend/orchestrator/pipeline.py

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AgentPipeline:
    """Orchestrates the full agent processing pipeline"""
    
    def __init__(self, llm_client):
        from backend.orchestrator.agent_registry import AgentRegistry
        from backend.orchestrator.message_classifier import MessageClassifier
        
        self.registry = AgentRegistry(llm_client)
        self.classifier = MessageClassifier()
    
    def process(self, message: str, agent_type: str = None) -> Dict[str, Any]:
        """
        Process a message through the agent pipeline
        
        Args:
            message: Input message
            agent_type: Optional - specify agent type, or auto-classify
            
        Returns:
            Dict with agent response and metadata
        """
        # Step 1: Classify message if agent not specified
        if agent_type is None:
            agent_type = self.classifier.classify(message)
            logger.info(f"Auto-classified message as: {agent_type}")
        
        # Step 2: Get appropriate agent
        agent = self.registry.get_agent(agent_type)
        if not agent:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Step 3: Process with agent
        logger.info(f"Processing with {agent_type} agent")
        
        # Different agents have different interfaces - normalize this
        if agent_type == "client_communication":
            result = agent.process(message)
        elif agent_type == "records_wrangler":
            # For demo, use a sample case description
            result = agent.process(case_description=message)
        elif agent_type == "legal_researcher":
            # Extract injury type and jurisdiction (or use defaults)
            result = agent.process(
                injury_type="personal injury",
                jurisdiction="Florida",
                case_details=message
            )
        elif agent_type == "evidence_sorter":
            # For demo, mock a document path
            result = agent.process(
                document_path="/path/to/document",
                document_text=message
            )
        
        # Step 4: Add metadata
        result["pipeline_metadata"] = {
            "agent_used": agent_type,
            "auto_classified": agent_type is None
        }
        
        return result
```

---

## 📏 Quality Metrics & Evaluation

### **Create a Test Suite**

```python
# backend/testing/agent_evaluation.py

import json
from typing import List, Dict

class AgentEvaluator:
    """Evaluate agent performance on test cases"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def run_test_suite(self, test_cases: List[Dict]) -> Dict:
        """
        Run agents on test cases and score results
        
        Args:
            test_cases: List of dicts with 'input', 'expected_agent', 'quality_criteria'
            
        Returns:
            Evaluation results
        """
        results = {
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for i, test in enumerate(test_cases):
            print(f"\nTest {i+1}/{len(test_cases)}: {test['description']}")
            
            # Run pipeline
            output = self.pipeline.process(test['input'])
            
            # Check if correct agent was used
            correct_agent = output['pipeline_metadata']['agent_used'] == test['expected_agent']
            
            # Manual quality check (for hackathon, automate later)
            print(f"Input: {test['input']}")
            print(f"Output: {output}")
            quality_ok = input("Quality acceptable? (y/n): ").lower() == 'y'
            
            passed = correct_agent and quality_ok
            
            results['details'].append({
                'test': test['description'],
                'passed': passed,
                'agent_used': output['pipeline_metadata']['agent_used'],
                'expected_agent': test['expected_agent']
            })
            
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        results['success_rate'] = results['passed'] / results['total'] * 100
        
        return results


# Example test cases
TEST_CASES = [
    {
        "description": "Client asking for help with slip and fall",
        "input": "I fell at the grocery store on a wet floor. What should I do?",
        "expected_agent": "client_communication",
        "quality_criteria": ["Professional tone", "Asks clarifying questions", "No legal advice"]
    },
    {
        "description": "Request for medical records",
        "input": "I need to get my medical records from Baptist Hospital for my case",
        "expected_agent": "records_wrangler",
        "quality_criteria": ["Identifies hospital", "Lists needed records", "Professional letter"]
    },
    {
        "description": "Legal research question",
        "input": "What are similar cases to mine? Slip and fall with broken wrist",
        "expected_agent": "legal_researcher",
        "quality_criteria": ["Identifies injury type", "Discusses precedents", "Settlement ranges"]
    }
]
```

---

## 🎯 Hackathon Action Plan (Priority Order)

### **Phase 1: Foundation (2 hours)**
1. ✅ Create `AgentRegistry` class
2. ✅ Create `MessageClassifier` class
3. ✅ Create `AgentPipeline` orchestrator
4. ✅ Test basic routing

### **Phase 2: Prompt Optimization (3 hours)**
1. ✅ Create test dataset (10 examples per agent)
2. ✅ Test current prompts and record quality scores
3. ✅ Iterate on prompts (try 3-5 variations per agent)
4. ✅ Select best prompts and update agents

### **Phase 3: Few-Shot Learning (2 hours)**
1. ✅ Add 2-3 example input/output pairs to each agent
2. ✅ Re-test with examples included
3. ✅ Measure improvement

### **Phase 4: Quality Metrics (1 hour)**
1. ✅ Create evaluation script
2. ✅ Run full test suite
3. ✅ Document success rates for demo

### **Phase 5: Demo Polish (1 hour)**
1. ✅ Create simple web interface showing pipeline flow
2. ✅ Add logging/visualization of which agent was used
3. ✅ Prepare demo scenarios

---

## 💡 Quick Wins for Demo

### **1. Show the Pipeline Visually**
Create a simple diagram that lights up as each step processes

### **2. Display Agent Confidence**
Add a "confidence score" to routing decisions

### **3. Add Human-in-the-Loop**
Show an "Approve/Reject" button before sending responses

### **4. Metrics Dashboard**
Display:
- Total requests processed
- Most-used agent
- Average response time
- Success rate

---

## 🚀 Next Steps

Want me to:

1. **Build the orchestration code** (AgentRegistry, MessageClassifier, AgentPipeline)?
2. **Create test datasets** for each agent?
3. **Optimize prompts** with few-shot examples?
4. **Build evaluation framework** to measure quality?

**For a 24-hour hackathon, I recommend focusing on #1 and #3** - they give the biggest ROI with minimal time investment.

Let me know which you want to tackle first! 🎯
