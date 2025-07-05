# app/scheduling/calcom.py

import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from ..utils.config_loader import get_settings
from ..models.appointment import Appointment

settings = get_settings()

class CalcomClient:
    """
    Cal.com integration client for appointment scheduling
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.CALCOM_API_KEY
        self.base_url = settings.CALCOM_BASE_URL or "https://api.cal.com/v1"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def get_event_types(self) -> List[Dict[str, Any]]:
        """
        Get available event types from Cal.com
        """
        try:
            response = await self.client.get(f"{self.base_url}/event-types")
            response.raise_for_status()
            
            event_types = response.json().get("event_types", [])
            logger.info(f"Retrieved {len(event_types)} event types from Cal.com")
            return event_types
            
        except Exception as e:
            logger.error(f"Error getting event types from Cal.com: {str(e)}")
            return []
    
    async def get_availability(self, event_type_id: int, date: str) -> List[Dict[str, Any]]:
        """
        Get available time slots for a specific event type and date
        
        Args:
            event_type_id: Cal.com event type ID
            date: Date in YYYY-MM-DD format
        """
        try:
            params = {
                "eventTypeId": event_type_id,
                "date": date
            }
            
            response = await self.client.get(
                f"{self.base_url}/availability",
                params=params
            )
            response.raise_for_status()
            
            availability = response.json().get("availability", [])
            logger.info(f"Retrieved {len(availability)} available slots for {date}")
            return availability
            
        except Exception as e:
            logger.error(f"Error getting availability from Cal.com: {str(e)}")
            return []
    
    async def create_booking(self, booking_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new booking in Cal.com
        
        Args:
            booking_data: Dictionary containing booking information
        """
        try:
            # Prepare booking payload
            payload = {
                "eventTypeId": booking_data.get("event_type_id"),
                "start": booking_data.get("start_time"),  # ISO format
                "end": booking_data.get("end_time"),      # ISO format
                "attendee": {
                    "name": booking_data.get("customer_name"),
                    "email": booking_data.get("customer_email"),
                    "timeZone": booking_data.get("timezone", "UTC")
                },
                "metadata": {
                    "phone": booking_data.get("customer_phone"),
                    "notes": booking_data.get("notes", ""),
                    "source": "phone_call_assistant"
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/bookings",
                json=payload
            )
            response.raise_for_status()
            
            booking = response.json()
            logger.info(f"Created booking in Cal.com: {booking.get('id')}")
            return booking
            
        except Exception as e:
            logger.error(f"Error creating booking in Cal.com: {str(e)}")
            return None
    
    async def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """
        Get booking details by ID
        """
        try:
            response = await self.client.get(f"{self.base_url}/bookings/{booking_id}")
            response.raise_for_status()
            
            booking = response.json()
            logger.info(f"Retrieved booking from Cal.com: {booking_id}")
            return booking
            
        except Exception as e:
            logger.error(f"Error getting booking from Cal.com: {str(e)}")
            return None
    
    async def cancel_booking(self, booking_id: str, reason: str = "") -> bool:
        """
        Cancel a booking in Cal.com
        """
        try:
            payload = {
                "reason": reason
            }
            
            response = await self.client.delete(
                f"{self.base_url}/bookings/{booking_id}",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Cancelled booking in Cal.com: {booking_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling booking in Cal.com: {str(e)}")
            return False
    
    async def reschedule_booking(self, booking_id: str, new_start_time: str, new_end_time: str) -> bool:
        """
        Reschedule a booking in Cal.com
        """
        try:
            payload = {
                "start": new_start_time,  # ISO format
                "end": new_end_time       # ISO format
            }
            
            response = await self.client.patch(
                f"{self.base_url}/bookings/{booking_id}",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Rescheduled booking in Cal.com: {booking_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rescheduling booking in Cal.com: {str(e)}")
            return False
    
    async def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get user profile information
        """
        try:
            response = await self.client.get(f"{self.base_url}/me")
            response.raise_for_status()
            
            profile = response.json()
            logger.info(f"Retrieved user profile from Cal.com")
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user profile from Cal.com: {str(e)}")
            return None
    
    async def find_available_slots(self, event_type_id: int, date_range: int = 7) -> List[Dict[str, Any]]:
        """
        Find available slots for the next N days
        
        Args:
            event_type_id: Cal.com event type ID
            date_range: Number of days to look ahead
        """
        available_slots = []
        
        for i in range(date_range):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            slots = await self.get_availability(event_type_id, date)
            
            for slot in slots:
                slot["date"] = date
                available_slots.append(slot)
        
        return available_slots
    
    async def book_appointment_from_phone_call(self, appointment: Appointment) -> Optional[str]:
        """
        Book appointment from phone call assistant
        
        Returns:
            Booking ID if successful, None otherwise
        """
        try:
            # Get event types to find the appropriate one
            event_types = await self.get_event_types()
            
            if not event_types:
                logger.error("No event types available in Cal.com")
                return None
            
            # Use the first event type or find by service type
            event_type_id = event_types[0]["id"]
            
            # For specific service matching
            for et in event_types:
                if appointment.service_type.lower() in et.get("title", "").lower():
                    event_type_id = et["id"]
                    break
            
            # Prepare booking data
            booking_data = {
                "event_type_id": event_type_id,
                "start_time": appointment.start_time.isoformat(),
                "end_time": appointment.end_time.isoformat(),
                "customer_name": appointment.customer_name,
                "customer_email": appointment.customer_email,
                "customer_phone": appointment.customer_phone,
                "notes": appointment.notes,
                "timezone": "UTC"
            }
            
            # Create booking
            booking = await self.create_booking(booking_data)
            
            if booking:
                return booking.get("id")
            
            return None
            
        except Exception as e:
            logger.error(f"Error booking appointment from phone call: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Utility function to get Cal.com client instance
async def get_calcom_client() -> CalcomClient:
    """Get configured Cal.com client"""
    return CalcomClient()