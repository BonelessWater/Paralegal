"""
A2A Protocol Agent Cards for Paralegal Specialist Agents
"""

from typing import Dict, Any, List
from config.amd_config import AMDConfig
import json


class ParalegalAgentCards:
    """Agent Cards for A2A Protocol discovery"""
    
    @staticmethod
    def get_client_communication_card() -> Dict[str, Any]:
        """Agent Card for Client Communication Agent"""
        return {
            "agent_id": "paralegal-client-communication",
            "name": "Paralegal Client Communication Agent",
            "description": "Transforms messy client messages into professional, empathetic legal responses",
            "version": "1.0.0",
            "capabilities": [
                "client-intake",
                "message-transformation",
                "empathetic-response"
            ],
            "skills": [
                {
                    "name": "process_client_message",
                    "description": "Process and respond to client communications",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        },
                        "required": ["message"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "response": {"type": "string"},
                            "case_summary": {"type": "string"}
                        }
                    }
                }
            ],
            "connection": {
                "protocol": "a2a",
                "endpoint": f"{AMDConfig.A2A_SERVER_URL}/agents/client-communication",
                "transport": ["http", "sse"]
            },
            "metadata": {
                "provider": "Paralegal AI System",
                "model": "Saul-7B-Instruct-v1",
                "domain": "legal"
            }
        }
    
    @staticmethod
    def get_all_agent_cards() -> List[Dict[str, Any]]:
        """Get all agent cards"""
        return [
            ParalegalAgentCards.get_client_communication_card(),
            # Add other agent cards similarly
        ]
    
    @staticmethod
    def save_agent_cards(output_dir: str = "agent_cards"):
        """Save all agent cards to JSON files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for card in ParalegalAgentCards.get_all_agent_cards():
            filename = f"{card['agent_id']}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(card, f, indent=2)
            
            print(f"Saved agent card: {filepath}")


if __name__ == "__main__":
    ParalegalAgentCards.save_agent_cards()