"""
Test script to check what imports actually work
"""

import sys
import os

print("Testing imports from AMD_server structure...")

# Test 1: Check if AMD_server agents exist
try:
    sys.path.append('AMD_server')
    from ADK.agents.client_communication_agent import ClientCommunicationAgent
    print("✅ ClientCommunicationAgent found in AMD_server/ADK/agents/")
except ImportError as e:
    print(f"❌ ClientCommunicationAgent not found: {e}")

# Test 2: Check backend LLM client
try:
    sys.path.append('backend')
    from APIs.AMD.llm_client import AMDLLMClient
    print("✅ AMDLLMClient found in backend/APIs/AMD/")
except ImportError as e:
    print(f"❌ AMDLLMClient not found: {e}")

# Test 3: Check config
try:
    from config.amd_config import AMDConfig
    print("✅ AMDConfig found")
except ImportError as e:
    print(f"❌ AMDConfig not found: {e}")

print("\nActual directory contents:")
print("AMD_server/ADK/agents/:", os.listdir("AMD_server/ADK/agents/") if os.path.exists("AMD_server/ADK/agents/") else "Does not exist")
print("backend/APIs/AMD/:", os.listdir("backend/APIs/AMD/") if os.path.exists("backend/APIs/AMD/") else "Does not exist")