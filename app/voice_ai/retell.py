# app/voice_ai/retell.py
import httpx
from typing import Dict, Any, Optional, List
from app.utils.config_loader import get_voice_ai_config
from app.utils.logger import get_logger

logger = get_logger()

class RetellClient:
    """Retell AI client for voice assistant management"""
    
    def __init__(self):
        config = get_voice_ai_config()
        self.api_key = config["retell"]["api_key"]
        self.base_url = "https://api.retellai.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new voice agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/create-agent",
                    json=agent_config,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"Created agent: {response.json()}")
                return response.json()
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/get-agent/{agent_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting agent: {e}")
            raise
    
    async def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent configuration"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/update-agent/{agent_id}",
                    json=update_data,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"Updated agent: {agent_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Error updating agent: {e}")
            raise
    
    async def create_phone_number(self, phone_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a phone number for the agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/create-phone-number",
                    json=phone_config,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"Created phone number: {response.json()}")
                return response.json()
        except Exception as e:
            logger.error(f"Error creating phone number: {e}")
            raise
    
    async def make_call(self, call_config: Dict[str, Any]) -> Dict[str, Any]:
        """Make an outbound call"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/create-phone-call",
                    json=call_config,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"Made call: {response.json()}")
                return response.json()
        except Exception as e:
            logger.error(f"Error making call: {e}")
            raise
    
    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get call details"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/get-call/{call_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting call: {e}")
            raise
    
    async def list_calls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of calls"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/list-calls",
                    params={"limit": limit},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting calls: {e}")
            raise

def create_appointment_booking_agent():
    """Create a pre-configured agent for appointment booking"""
    return {
        "agent_name": "Appointment Booking Agent",
        "voice_id": "11labs-Adrian",
        "language": "en-US",
        "response_engine": {
            "type": "retell-llm",
            "llm_id": "gpt-4o"
        },
        "llm_websocket_url": "wss://api.retellai.com/llm-websocket",
        "begin_message": "Hello! Thank you for calling. I'm here to help you schedule an appointment or answer any questions about our services. How can I assist you today?",
        "general_prompt": """You are a professional appointment booking assistant. Your job is to:
1. Greet callers warmly and professionally
2. Answer questions about services and pricing
3. Help schedule appointments by collecting:
   - Customer name and contact information
   - Preferred date and time
   - Service type
4. Check availability and confirm bookings
5. Provide appointment confirmations
6. Handle rescheduling and cancellations professionally

Always be polite, helpful, and efficient. If you cannot handle a request, offer to connect them with a human representative.

Key information about our services:
- We offer consultation sessions (30 minutes, $100)
- We offer full services (60 minutes, $200)
- We're open Monday-Friday 9 AM to 6 PM
- We require 24-hour notice for cancellations""",
        "general_tools": [
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book an appointment for a customer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_name": {"type": "string"},
                            "customer_phone": {"type": "string"},
                            "customer_email": {"type": "string"},
                            "service_type": {"type": "string"},
                            "preferred_date": {"type": "string"},
                            "preferred_time": {"type": "string"}
                        },
                        "required": ["customer_name", "customer_phone", "service_type", "preferred_date", "preferred_time"]
                    }
                }
            }
        ]
    }

# Create a global instance
retell_client = RetellClient()