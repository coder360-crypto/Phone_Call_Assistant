# app/webhooks/retell_webhook.py

import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from loguru import logger
from app.utils.config_loader import get_settings
from app.automation.makecom import get_makecom_client
from app.automation.zapier import get_zapier_client
from app.scheduling.google_calendar import get_google_calendar_client
from app.scheduling.calcom import get_calcom_client
from app.scheduling.crm import get_crm_client
from app.models.appointment import Appointment
from app.models.customer import Customer
from datetime import datetime, timedelta

settings = get_settings()

class RetellWebhookHandler:
    """
    Handle webhooks from Retell AI
    """
    
    def __init__(self):
        self.webhook_secret = settings.RETELL_WEBHOOK_SECRET
        self.scheduling_backend = settings.SCHEDULING_BACKEND or "google_calendar"
        self.automation_backend = settings.AUTOMATION_BACKEND or "makecom"
    
    def verify_signature(self, request_body: bytes, signature: str) -> bool:
        """
        Verify webhook signature from Retell AI
        """
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
            
        except Exception as e:
            logger.error(f"Error verifying Retell webhook signature: {str(e)}")
            return False
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle incoming webhook from Retell AI
        """
        try:
            # Get request body and signature
            body = await request.body()
            signature = request.headers.get("X-Retell-Signature", "")
            
            # Verify signature if webhook secret is configured
            if self.webhook_secret and not self.verify_signature(body, signature):
                logger.warning("Invalid Retell webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Parse webhook data
            webhook_data = json.loads(body)
            event_type = webhook_data.get("event", "")
            
            logger.info(f"Received Retell webhook: {event_type}")
            
            # Route to appropriate handler
            if event_type == "call_started":
                return await self.handle_call_started(webhook_data)
            elif event_type == "call_ended":
                return await self.handle_call_ended(webhook_data)
            elif event_type == "function_call":
                return await self.handle_function_call(webhook_data)
            elif event_type == "call_analyzed":
                return await self.handle_call_analyzed(webhook_data)
            else:
                logger.warning(f"Unknown Retell webhook event: {event_type}")
                return {"status": "ignored"}
                
        except Exception as e:
            logger.error(f"Error handling Retell webhook: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def handle_call_started(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call started event
        """
        try:
            call_id = webhook_data.get("call_id", "")
            caller_number = webhook_data.get("from_number", "")
            
            logger.info(f"Call started: {call_id} from {caller_number}")
            
            # Log call start in your system
            call_data = {
                "call_id": call_id,
                "caller_number": caller_number,
                "direction": "inbound",
                "status": "started",
                "start_time": datetime.now().isoformat()
            }
            
            # Here you could store call data in your database
            # or trigger any automation workflows
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Error handling call started: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_call_ended(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call ended event
        """
        try:
            call_id = webhook_data.get("call_id", "")
            call_length = webhook_data.get("call_length", 0)
            end_reason = webhook_data.get("end_reason", "")
            
            logger.info(f"Call ended: {call_id}, duration: {call_length}s, reason: {end_reason}")
            
            # Log call end in your system
            call_data = {
                "call_id": call_id,
                "duration": call_length,
                "end_reason": end_reason,
                "end_time": datetime.now().isoformat()
            }
            
            # Trigger automation workflows
            if self.automation_backend == "makecom":
                makecom_client = await get_makecom_client()
                await makecom_client.trigger_call_ended(call_data)
            elif self.automation_backend == "zapier":
                zapier_client = await get_zapier_client()
                await zapier_client.send_custom_event("call_ended", call_data)
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Error handling call ended: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_function_call(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle function call from Retell AI agent
        """
        try:
            call_id = webhook_data.get("call_id", "")
            function_name = webhook_data.get("function_name", "")
            function_args = webhook_data.get("function_arguments", {})
            
            logger.info(f"Function call: {function_name} for call {call_id}")
            
            # Route to appropriate function handler
            if function_name == "book_appointment":
                return await self.handle_book_appointment(call_id, function_args)
            elif function_name == "check_availability":
                return await self.handle_check_availability(call_id, function_args)
            elif function_name == "get_services":
                return await self.handle_get_services(call_id, function_args)
            elif function_name == "get_pricing":
                return await self.handle_get_pricing(call_id, function_args)
            elif function_name == "cancel_appointment":
                return await self.handle_cancel_appointment(call_id, function_args)
            elif function_name == "reschedule_appointment":
                return await self.handle_reschedule_appointment(call_id, function_args)
            else:
                logger.warning(f"Unknown function call: {function_name}")
                return {"status": "error", "error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            logger.error(f"Error handling function call: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_call_analyzed(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call analysis results
        """
        try:
            call_id = webhook_data.get("call_id", "")
            transcript = webhook_data.get("transcript", "")
            summary = webhook_data.get("summary", "")
            sentiment = webhook_data.get("sentiment", "")
            
            logger.info(f"Call analyzed: {call_id}")
            
            # Store call analysis results
            analysis_data = {
                "call_id": call_id,
                "transcript": transcript,
                "summary": summary,
                "sentiment": sentiment,
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Trigger automation workflows
            if self.automation_backend == "makecom":
                makecom_client = await get_makecom_client()
                await makecom_client.trigger_call_analyzed(analysis_data)
            elif self.automation_backend == "zapier":
                zapier_client = await get_zapier_client()
                await zapier_client.send_custom_event("call_analyzed", analysis_data)
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Error handling call analysis: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_book_appointment(self, call_id: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle appointment booking function call
        """
        try:
            # Extract appointment details
            customer_name = function_args.get("customer_name", "")
            customer_phone = function_args.get("customer_phone", "")
            customer_email = function_args.get("customer_email", "")
            service_type = function_args.get("service_type", "")
            appointment_date = function_args.get("appointment_date", "")
            appointment_time = function_args.get("appointment_time", "")
            duration = function_args.get("duration", 60)  # Default 60 minutes
            notes = function_args.get("notes", "")
            
            # Validate required fields
            if not all([customer_name, customer_phone, service_type, appointment_date, appointment_time]):
                return {
                    "status": "error",
                    "error": "Missing required fields for appointment booking"
                }
            
            # Parse appointment datetime
            start_datetime = datetime.fromisoformat(f"{appointment_date}T{appointment_time}")
            end_datetime = start_datetime + timedelta(minutes=duration)
            
            # Create customer and appointment objects
            customer = Customer(
                name=customer_name,
                phone=customer_phone,
                email=customer_email
            )
            
            appointment = Appointment(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                service_type=service_type,
                start_time=start_datetime,
                end_time=end_datetime,
                notes=notes
            )
            
            # Book appointment using configured backend
            appointment_id = None
            
            if self.scheduling_backend == "google_calendar":
                calendar_client = await get_google_calendar_client()
                appointment_id = await calendar_client.book_appointment_from_phone_call(appointment, customer)
            elif self.scheduling_backend == "calcom":
                calcom_client = await get_calcom_client()
                appointment_id = await calcom_client.book_appointment_from_phone_call(appointment)
            elif self.scheduling_backend == "crm":
                crm_client = await get_crm_client()
                appointment_id = await crm_client.book_appointment_from_phone_call(appointment, customer)
            
            if appointment_id:
                # Trigger automation workflows
                appointment_data = {
                    "appointment_id": appointment_id,
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "customer_email": customer_email,
                    "service_type": service_type,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "duration": duration,
                    "notes": notes,
                    "call_id": call_id,
                    "created_at": datetime.now().isoformat()
                }
                
                if self.automation_backend == "makecom":
                    makecom_client = await get_makecom_client()
                    await makecom_client.trigger_appointment_booked(appointment_data)
                elif self.automation_backend == "zapier":
                    zapier_client = await get_zapier_client()
                    await zapier_client.trigger_appointment_booked(appointment_data)
                
                return {
                    "status": "success",
                    "appointment_id": appointment_id,
                    "message": f"Appointment booked successfully for {customer_name} on {appointment_date} at {appointment_time}"
                }
            else:
                return {
                    "status": "error",
                    "error": "Failed to book appointment"
                }
                
        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_check_availability(self, call_id: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle availability check function call
        """
        try:
            date = function_args.get("date", "")
            service_type = function_args.get("service_type", "")
            
            if not date:
                return {"status": "error", "error": "Date is required"}
            
            # Check availability using configured backend
            available_slots = []
            
            if self.scheduling_backend == "google_calendar":
                calendar_client = await get_google_calendar_client()
                available_slots = await calendar_client.find_available_slots(date)
            elif self.scheduling_backend == "calcom":
                calcom_client = await get_calcom_client()
                # For Cal.com, you'd need to specify event type ID
                available_slots = await calcom_client.find_available_slots(1, 1)  # Default event type
            elif self.scheduling_backend == "crm":
                crm_client = await get_crm_client()
                available_slots = await crm_client.check_availability(date)
            
            return {
                "status": "success",
                "available_slots": available_slots,
                "date": date
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_get_services(self, call_id: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get services function call
        """
        try:
            # Return available services
            services = [
                {
                    "name": "Consultation",
                    "duration": 60,
                    "price": 100,
                    "description": "Initial consultation session"
                },
                {
                    "name": "Therapy Session",
                    "duration": 60,
                    "price": 150,
                    "description": "Individual therapy session"
                },
                {
                    "name": "Group Session",
                    "duration": 90,
                    "price": 75,
                    "description": "Group therapy session"
                }
            ]
            
            return {
                "status": "success",
                "services": services
            }
            
        except Exception as e:
            logger.error(f"Error getting services: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_get_pricing(self, call_id: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get pricing function call
        """
        try:
            service_type = function_args.get("service_type", "")
            
            # Return pricing information
            pricing = {
                "consultation": "$100/session",
                "therapy_session": "$150/session",
                "group_session": "$75/session"
            }
            
            if service_type:
                specific_price = pricing.get(service_type.lower().replace(" ", "_"))
                if specific_price:
                    return {
                        "status": "success",
                        "service": service_type,
                        "price": specific_price
                    }
            
            return {
                "status": "success",
                "pricing": pricing
            }
            
        except Exception as e:
            logger.error(f"Error getting pricing: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_cancel_appointment(self, call_id: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle appointment cancellation function call
        """
        try:
            appointment_id = function_args.get("appointment_id", "")
            cancellation_reason = function_args.get("reason", "")
            
            if not appointment_id:
                return {"status": "error", "error": "Appointment ID is required"}
            
            # Cancel appointment using configured backend
            success = False
            
            if self.scheduling_backend == "google_calendar":
                calendar_client = await get_google_calendar_client()
                success = await calendar_client.delete_event(appointment_id)
            elif self.scheduling_backend == "calcom":
                calcom_client = await get_calcom_client()
                success = await calcom_client.cancel_booking(appointment_id, cancellation_reason)
            elif self.scheduling_backend == "crm":
                crm_client = await get_crm_client()
                success = await crm_client.cancel_appointment(appointment_id, cancellation_reason)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Appointment {appointment_id} cancelled successfully"
                }
            else:
                return {
                    "status": "error",
                    "error": "Failed to cancel appointment"
                }
                
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def handle_reschedule_appointment(self, call_id: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle appointment rescheduling function call
        """
        try:
            appointment_id = function_args.get("appointment_id", "")
            new_date = function_args.get("new_date", "")
            new_time = function_args.get("new_time", "")
            
            if not all([appointment_id, new_date, new_time]):
                return {"status": "error", "error": "Missing required fields for rescheduling"}
            
            # Parse new datetime
            new_start_datetime = datetime.fromisoformat(f"{new_date}T{new_time}")
            new_end_datetime = new_start_datetime + timedelta(minutes=60)  # Default duration
            
            # Reschedule appointment using configured backend
            success = False
            
            if self.scheduling_backend == "google_calendar":
                calendar_client = await get_google_calendar_client()
                success = await calendar_client.update_event(appointment_id, {
                    "start_time": new_start_datetime.isoformat(),
                    "end_time": new_end_datetime.isoformat()
                })
            elif self.scheduling_backend == "calcom":
                calcom_client = await get_calcom_client()
                success = await calcom_client.reschedule_booking(
                    appointment_id, 
                    new_start_datetime.isoformat(),
                    new_end_datetime.isoformat()
                )
            elif self.scheduling_backend == "crm":
                crm_client = await get_crm_client()
                success = await crm_client.reschedule_appointment(
                    appointment_id,
                    new_start_datetime.isoformat(),
                    new_end_datetime.isoformat()
                )
            
            if success:
                return {
                    "status": "success",
                    "message": f"Appointment {appointment_id} rescheduled to {new_date} at {new_time}"
                }
            else:
                return {
                    "status": "error",
                    "error": "Failed to reschedule appointment"
                }
                
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            return {"status": "error", "error": str(e)}

# Utility function to get webhook handler
def get_retell_webhook_handler() -> RetellWebhookHandler:
    """Get Retell webhook handler instance"""
    return RetellWebhookHandler()