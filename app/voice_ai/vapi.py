# app/voice_ai/vapi.py
import httpx
from typing import Dict, Any, Optional, List
from app.utils.config_loader import get_voice_ai_config
from app.utils.logger import get_logger

logger = get_logger()

class VapiClient:
    """Vapi AI client for voice assistant management"""
    
    def __init__(self):
        config = get_voice_ai_config()
        self.api_key = config["vapi"]["api_key"]
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_assistant(self, assistant_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new voice assistant"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/assistant",
                    json=assistant_config,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"Created assistant: {response.json()}")
                return response.json()
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            raise
    
    async def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Get assistant details"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/assistant/{assistant_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting assistant: {e}")
            raise
    
    async def update_assistant(self, assistant_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update assistant configuration"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/assistant/{assistant_id}",
                    json=update_data,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"Updated assistant: {assistant_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Error updating assistant: {e}")
            raise
    
    async def create_phone_number(self, phone_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a phone number for the assistant"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/phone-number",
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
                    f"{self.base_url}/call",
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
                    f"{self.base_url}/call/{call_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting call: {e}")
            raise
    
    async def get_calls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of calls"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/call",
                    params={"limit": limit},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting calls: {e}")
            raise

def create_appointment_booking_assistant():
    """Create a pre-configured assistant for appointment booking"""
    return {
        "name": "Appointment Booking Assistant",
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "systemMessage": """You are a professional appointment booking assistant. Your job is to:
1. Greet callers warmly and professionally
2. Answer questions about services and pricing
3. Help schedule appointments by collecting:
   - Customer name and contact information
   - Preferred date and time
   - Service type
4. Check availability and confirm bookings
5. Provide appointment confirmations
6. Handle rescheduling and cancellations professionally

Always be polite, helpful, and efficient. If you cannot handle a request, offer to connect them with a human representative."""
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM"
        },
        "firstMessage": "Hello! Thank you for calling. I'm here to help you schedule an appointment or answer any questions about our services. How can I assist you today?"
    }

# Create a global instance
vapi_client = VapiClient()