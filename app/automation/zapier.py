# app/automation/zapier.py

import httpx
from typing import Dict, Any, Optional, List
from loguru import logger
from ..utils.config_loader import get_settings

settings = get_settings()

class ZapierClient:
    """
    Zapier integration client for workflow automation
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.ZAPIER_WEBHOOK_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def trigger_appointment_booked(self, appointment_data: Dict[str, Any]) -> bool:
        """
        Trigger Zapier webhook when appointment is booked
        """
        try:
            payload = {
                "event_type": "appointment_booked",
                "customer_name": appointment_data.get("customer_name"),
                "customer_phone": appointment_data.get("customer_phone"),
                "customer_email": appointment_data.get("customer_email"),
                "appointment_date": appointment_data.get("appointment_date"),
                "appointment_time": appointment_data.get("appointment_time"),
                "service_type": appointment_data.get("service_type"),
                "appointment_id": appointment_data.get("appointment_id"),
                "notes": appointment_data.get("notes"),
                "booking_source": "phone_call",
                "timestamp": appointment_data.get("created_at")
            }
            
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Zapier webhook triggered successfully for appointment {appointment_data.get('appointment_id')}")
                return True
            else:
                logger.error(f"Zapier webhook failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering Zapier webhook: {str(e)}")
            return False
    
    async def trigger_appointment_cancelled(self, appointment_data: Dict[str, Any]) -> bool:
        """
        Trigger Zapier webhook when appointment is cancelled
        """
        try:
            payload = {
                "event_type": "appointment_cancelled",
                "customer_name": appointment_data.get("customer_name"),
                "customer_phone": appointment_data.get("customer_phone"),
                "customer_email": appointment_data.get("customer_email"),
                "appointment_date": appointment_data.get("appointment_date"),
                "appointment_time": appointment_data.get("appointment_time"),
                "appointment_id": appointment_data.get("appointment_id"),
                "cancellation_reason": appointment_data.get("cancellation_reason"),
                "cancelled_by": appointment_data.get("cancelled_by"),
                "timestamp": appointment_data.get("cancelled_at")
            }
            
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Zapier cancellation webhook triggered successfully for appointment {appointment_data.get('appointment_id')}")
                return True
            else:
                logger.error(f"Zapier cancellation webhook failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering Zapier cancellation webhook: {str(e)}")
            return False
    
    async def trigger_customer_inquiry(self, inquiry_data: Dict[str, Any]) -> bool:
        """
        Trigger Zapier webhook for customer inquiries
        """
        try:
            payload = {
                "event_type": "customer_inquiry",
                "customer_name": inquiry_data.get("customer_name"),
                "customer_phone": inquiry_data.get("customer_phone"),
                "customer_email": inquiry_data.get("customer_email"),
                "inquiry_type": inquiry_data.get("inquiry_type"),
                "inquiry_message": inquiry_data.get("inquiry_message"),
                "call_id": inquiry_data.get("call_id"),
                "timestamp": inquiry_data.get("created_at")
            }
            
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Zapier inquiry webhook triggered successfully for call {inquiry_data.get('call_id')}")
                return True
            else:
                logger.error(f"Zapier inquiry webhook failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering Zapier inquiry webhook: {str(e)}")
            return False
    
    async def send_custom_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Send custom event to Zapier
        """
        try:
            payload = {
                "event_type": event_type,
                "timestamp": data.get("timestamp"),
                **data
            }
            
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Zapier custom event '{event_type}' triggered successfully")
                return True
            else:
                logger.error(f"Zapier custom event failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering Zapier custom event: {str(e)}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Utility function to get Zapier client instance
async def get_zapier_client() -> ZapierClient:
    """Get configured Zapier client"""
    return ZapierClient()