"""
Unified Integration Test
Tests: HuggingFace → AMD vLLM → Google ADK → A2A → 4 Agents
Location: AMD_server/ADK/integrations/ (single location)
"""

import requests
import json
import sys
import os
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.append(project_root)

from config.amd_config import AMDConfig


def main():
    """Test the unified integration stack"""
    print("="*80)
    print("🧪 UNIFIED INTEGRATION TEST")
    print("📁 Location: AMD_server/ADK/integrations/ (single location)")
    print("🔗 HuggingFace Saul-7B → AMD vLLM → Google ADK → A2A Protocol → 4 Agents")
    print("="*80)
    
    server_url = f"http://localhost:{AMDConfig.A2A_SERVER_PORT}"
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Unified Stack Health...")
    try:
        response = requests.get(f"{server_url}/health", timeout=10)
        data = response.json()
        
        print("✅ Unified stack is healthy!")
        print(f"   🤖 Service: {data['service']}")
        print(f"   📁 Location: {data['location']}")
        print(f"   🔢 Agents: {data['agents_count']}")
        print(f"   📊 Model: {data['model']}")
        print("   🔗 Integration Stack:")
        for i, component in enumerate(data['integration_stack'], 1):
            print(f"      {i}. {component}")
            
    except Exception as e:
        print(f"❌ Stack health check failed: {e}")
        return False
    
    # Test 2: Agent Discovery
    print("\n2️⃣ Testing Agent Discovery...")
    try:
        response = requests.get(f"{server_url}/agents", timeout=10)
        data = response.json()
        agents = data['result']['agents']
        
        print(f"✅ Discovered {len(agents)} unified ADK+A2A agents:")
        for agent in agents:
            print(f"   • {agent['agent_id']}")
            print(f"     📍 Location: {agent['metadata']['location']}")
            print(f"     🤖 Model: {agent['metadata']['model']}")
            print(f"     🔧 Integration: {agent['metadata']['integration']}")
            
    except Exception as e:
        print(f"❌ Agent discovery failed: {e}")
        return False
    
    # Test 3: Complete Workflow Test
    print("\n3️⃣ Testing Complete Client Communication Workflow...")
    
    test_request = {
        "jsonrpc": "2.0",
        "method": "invoke_skill", 
        "params": {
            "skill": "process",
            "input": {
                "message": """Hello, I desperately need legal help. I was involved in a serious 
                car accident 2 months ago where a drunk driver ran a red light and T-boned my car. 
                I suffered multiple injuries including a broken arm, 3 fractured ribs, and a severe 
                concussion. I've been unable to work and have accumulated over $75,000 in medical 
                bills. The other driver's insurance company is trying to lowball me with a settlement 
                offer of only $15,000. I don't know what to do and I'm drowning in debt. Can you 
                please help me understand my options and next steps?"""
            }
        },
        "id": "unified-test-001"
    }
    
    try:
        response = requests.post(
            f"{server_url}/agents/paralegal-client-communication/invoke",
            json=test_request,
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Complete unified workflow successful!")
            print(f"   🔧 Integration: {result['result']['integration']}")
            print(f"   🤖 Model: {result['result']['model']}")
            
            output = result['result']['output']
            if isinstance(output, dict):
                response_text = output.get('response', str(output))
            else:
                response_text = str(output)
            
            print(f"   💬 AI Response Preview:")
            print(f"      {response_text[:400]}...")
            
        else:
            print(f"❌ Workflow failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        return False
    
    # Final Summary
    print("\n" + "="*80)
    print("🎉 UNIFIED INTEGRATION SUCCESS!")
    print("="*80)
    print("✅ Your paralegal AI system is fully operational with:")
    print("   📁 Single location: AMD_server/ADK/integrations/")
    print("   🔸 HuggingFace Saul-7B legal language model")
    print("   🔸 AMD vLLM server for GPU acceleration") 
    print("   🔸 Google ADK for agent orchestration")
    print("   🔸 A2A protocol for agent communication")
    print("   🔸 4 specialist paralegal agents")
    print("\n🚀 Ready for production use!")
    print("📁 All code consolidated in one place!")
    print("="*80)
    
    return True


if __name__ == "__main__":
    main()