# app/automation/makecom.py
import httpx
from typing import Dict, Any, Optional
from app.utils.config_loader import get_automation_config
from app.utils.logger import get_logger

logger = get_logger()

class MakecomClient:
    """Make.com automation client"""
    
    def __init__(self):
        config = get_automation_config()
        self.webhook_url = config["makecom"]["webhook_url"]
    
    async def trigger_workflow(self, data: Dict[str, Any]) -> bool:
        """Trigger a Make.com workflow via webhook"""
        try:
            if not self.webhook_url:
                logger.warning("Make.com webhook URL not configured")
                return False
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                logger.info(f"Make.com workflow triggered successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error triggering Make.com workflow: {e}")
            return False
    
    async def send_appointment_confirmation(self, appointment_data: Dict[str, Any]) -> bool:
        """Send appointment confirmation workflow"""
        workflow_data = {
            "workflow_type": "appointment_confirmation",
            "customer_name": appointment_data.get("customer_name"),
            "customer_email": appointment_data.get("customer_email"),
            "customer_phone": appointment_data.get("customer_phone"),
            "service_type": appointment_data.get("service_type"),
            "appointment_time": appointment_data.get("appointment_time"),
            "calendar_event_id": appointment_data.get("calendar_event_id")
        }
        
        return await self.trigger_workflow(workflow_data)
    
    async def send_appointment_reminder(self, appointment_data: Dict[str, Any]) -> bool:
        """Send appointment reminder workflow"""
        workflow_data = {
            "workflow_type": "appointment_reminder",
            "customer_name": appointment_data.get("customer_name"),
            "customer_email": appointment_data.get("customer_email"),
            "customer_phone": appointment_data.get("customer_phone"),
            "service_type": appointment_data.get("service_type"),
            "appointment_time": appointment_data.get("appointment_time")
        }
        
        return await self.trigger_workflow(workflow_data)
    
    async def update_crm_contact(self, contact_data: Dict[str, Any]) -> bool:
        """Update CRM contact workflow"""
        workflow_data = {
            "workflow_type": "crm_update",
            "customer_name": contact_data.get("customer_name"),
            "customer_email": contact_data.get("customer_email"),
            "customer_phone": contact_data.get("customer_phone"),
            "last_interaction": contact_data.get("last_interaction"),
            "notes": contact_data.get("notes")
        }
        
        return await self.trigger_workflow(workflow_data)
    
    async def send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send notification workflow"""
        workflow_data = {
            "workflow_type": "notification",
            "type": notification_data.get("type"),
            "message": notification_data.get("message"),
            "recipient": notification_data.get("recipient"),
            "priority": notification_data.get("priority", "normal")
        }
        
        return await self.trigger_workflow(workflow_data)

# Create a global instance
makecom_client = MakecomClient()

async def trigger_makecom_workflow(data: Dict[str, Any]) -> bool:
    """Helper function to trigger Make.com workflow"""
    return await makecom_client.trigger_workflow(data)


# Utility function to get Make.com client instance
async def get_makecom_client() -> "MakecomClient":
    """Get configured Make.com client"""
    return MakecomClient()