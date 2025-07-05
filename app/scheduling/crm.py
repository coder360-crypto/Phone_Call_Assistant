# app/scheduling/crm.py

import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from ..utils.config_loader import get_settings
from ..models.appointment import Appointment
from ..models.customer import Customer

settings = get_settings()

class CRMClient:
    """
    Custom CRM integration client for appointment scheduling and customer management
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.CRM_API_KEY
        self.base_url = base_url or settings.CRM_BASE_URL
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new customer in CRM
        """
        try:
            payload = {
                "name": customer_data.get("name"),
                "email": customer_data.get("email"),
                "phone": customer_data.get("phone"),
                "source": "phone_call_assistant",
                "created_at": datetime.now().isoformat(),
                "custom_fields": customer_data.get("custom_fields", {}),
                "notes": customer_data.get("notes", "")
            }
            
            response = await self.client.post(
                f"{self.base_url}/customers",
                json=payload
            )
            response.raise_for_status()
            
            customer = response.json()
            logger.info(f"Created customer in CRM: {customer.get('id')}")
            return customer
            
        except Exception as e:
            logger.error(f"Error creating customer in CRM: {str(e)}")
            return None
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer details by ID
        """
        try:
            response = await self.client.get(f"{self.base_url}/customers/{customer_id}")
            response.raise_for_status()
            
            customer = response.json()
            logger.info(f"Retrieved customer from CRM: {customer_id}")
            return customer
            
        except Exception as e:
            logger.error(f"Error getting customer from CRM: {str(e)}")
            return None
    
    async def find_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Find customer by phone number
        """
        try:
            params = {"phone": phone}
            response = await self.client.get(
                f"{self.base_url}/customers/search",
                params=params
            )
            response.raise_for_status()
            
            customers = response.json().get("customers", [])
            if customers:
                logger.info(f"Found customer by phone: {phone}")
                return customers[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding customer by phone: {str(e)}")
            return None
    
    async def find_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find customer by email address
        """
        try:
            params = {"email": email}
            response = await self.client.get(
                f"{self.base_url}/customers/search",
                params=params
            )
            response.raise_for_status()
            
            customers = response.json().get("customers", [])
            if customers:
                logger.info(f"Found customer by email: {email}")
                return customers[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding customer by email: {str(e)}")
            return None
    
    async def update_customer(self, customer_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update customer information
        """
        try:
            payload = {
                **update_data,
                "updated_at": datetime.now().isoformat()
            }
            
            response = await self.client.patch(
                f"{self.base_url}/customers/{customer_id}",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Updated customer in CRM: {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating customer in CRM: {str(e)}")
            return False
    
    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new appointment in CRM
        """
        try:
            payload = {
                "customer_id": appointment_data.get("customer_id"),
                "title": appointment_data.get("title"),
                "description": appointment_data.get("description"),
                "start_time": appointment_data.get("start_time"),
                "end_time": appointment_data.get("end_time"),
                "service_type": appointment_data.get("service_type"),
                "status": "scheduled",
                "source": "phone_call_assistant",
                "created_at": datetime.now().isoformat(),
                "notes": appointment_data.get("notes", ""),
                "custom_fields": appointment_data.get("custom_fields", {})
            }
            
            response = await self.client.post(
                f"{self.base_url}/appointments",
                json=payload
            )
            response.raise_for_status()
            
            appointment = response.json()
            logger.info(f"Created appointment in CRM: {appointment.get('id')}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error creating appointment in CRM: {str(e)}")
            return None
    
    async def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get appointment details by ID
        """
        try:
            response = await self.client.get(f"{self.base_url}/appointments/{appointment_id}")
            response.raise_for_status()
            
            appointment = response.json()
            logger.info(f"Retrieved appointment from CRM: {appointment_id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error getting appointment from CRM: {str(e)}")
            return None
    
    async def cancel_appointment(self, appointment_id: str, reason: str = "") -> bool:
        """
        Cancel an appointment in CRM
        """
        try:
            payload = {
                "status": "cancelled",
                "cancellation_reason": reason,
                "cancelled_at": datetime.now().isoformat()
            }
            
            response = await self.client.patch(
                f"{self.base_url}/appointments/{appointment_id}",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Cancelled appointment in CRM: {appointment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling appointment in CRM: {str(e)}")
            return False
    
    async def reschedule_appointment(self, appointment_id: str, new_start_time: str, new_end_time: str) -> bool:
        """
        Reschedule an appointment in CRM
        """
        try:
            payload = {
                "start_time": new_start_time,
                "end_time": new_end_time,
                "status": "rescheduled",
                "rescheduled_at": datetime.now().isoformat()
            }
            
            response = await self.client.patch(
                f"{self.base_url}/appointments/{appointment_id}",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Rescheduled appointment in CRM: {appointment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rescheduling appointment in CRM: {str(e)}")
            return False
    
    async def get_customer_appointments(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all appointments for a customer
        """
        try:
            params = {"customer_id": customer_id}
            response = await self.client.get(
                f"{self.base_url}/appointments",
                params=params
            )
            response.raise_for_status()
            
            appointments = response.json().get("appointments", [])
            logger.info(f"Retrieved {len(appointments)} appointments for customer {customer_id}")
            return appointments
            
        except Exception as e:
            logger.error(f"Error getting customer appointments from CRM: {str(e)}")
            return []
    
    async def check_availability(self, date: str, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Check availability for a specific date
        """
        try:
            params = {
                "date": date,
                "duration": duration_minutes
            }
            
            response = await self.client.get(
                f"{self.base_url}/availability",
                params=params
            )
            response.raise_for_status()
            
            availability = response.json().get("available_slots", [])
            logger.info(f"Retrieved {len(availability)} available slots for {date}")
            return availability
            
        except Exception as e:
            logger.error(f"Error checking availability in CRM: {str(e)}")
            return []
    
    async def get_services(self) -> List[Dict[str, Any]]:
        """
        Get available services from CRM
        """
        try:
            response = await self.client.get(f"{self.base_url}/services")
            response.raise_for_status()
            
            services = response.json().get("services", [])
            logger.info(f"Retrieved {len(services)} services from CRM")
            return services
            
        except Exception as e:
            logger.error(f"Error getting services from CRM: {str(e)}")
            return []
    
    async def log_call_activity(self, call_data: Dict[str, Any]) -> bool:
        """
        Log call activity in CRM
        """
        try:
            payload = {
                "customer_id": call_data.get("customer_id"),
                "call_id": call_data.get("call_id"),
                "direction": "inbound",
                "duration": call_data.get("duration"),
                "summary": call_data.get("summary"),
                "outcome": call_data.get("outcome"),
                "created_at": datetime.now().isoformat(),
                "source": "phone_call_assistant"
            }
            
            response = await self.client.post(
                f"{self.base_url}/activities",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Logged call activity in CRM for customer {call_data.get('customer_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging call activity in CRM: {str(e)}")
            return False
    
    async def get_or_create_customer(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get existing customer or create new one
        """
        try:
            # Try to find existing customer by phone
            if customer_data.get("phone"):
                existing_customer = await self.find_customer_by_phone(customer_data["phone"])
                if existing_customer:
                    return existing_customer
            
            # Try to find existing customer by email
            if customer_data.get("email"):
                existing_customer = await self.find_customer_by_email(customer_data["email"])
                if existing_customer:
                    return existing_customer
            
            # Create new customer
            return await self.create_customer(customer_data)
            
        except Exception as e:
            logger.error(f"Error in get_or_create_customer: {str(e)}")
            return None
    
    async def book_appointment_from_phone_call(self, appointment: Appointment, customer: Customer) -> Optional[str]:
        """
        Book appointment from phone call assistant
        
        Returns:
            Appointment ID if successful, None otherwise
        """
        try:
            # Get or create customer
            customer_data = {
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "notes": f"Customer contacted via phone call assistant"
            }
            
            crm_customer = await self.get_or_create_customer(customer_data)
            
            if not crm_customer:
                logger.error("Failed to create/retrieve customer")
                return None
            
            # Prepare appointment data
            appointment_data = {
                "customer_id": crm_customer.get("id"),
                "title": f"{appointment.service_type} - {customer.name}",
                "description": f"Phone call appointment for {appointment.service_type}",
                "start_time": appointment.start_time.isoformat(),
                "end_time": appointment.end_time.isoformat(),
                "service_type": appointment.service_type,
                "notes": appointment.notes or ""
            }
            
            # Create appointment
            crm_appointment = await self.create_appointment(appointment_data)
            
            if crm_appointment:
                return crm_appointment.get("id")
            
            return None
            
        except Exception as e:
            logger.error(f"Error booking appointment from phone call: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Utility function to get CRM client instance
async def get_crm_client() -> CRMClient:
    """Get configured CRM client"""
    return CRMClient()