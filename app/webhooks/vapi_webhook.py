# app/webhooks/vapi_webhook.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from app.utils.config_loader import get_voice_ai_config, get_settings
from app.utils.logger import get_logger
from app.scheduling.google_calendar import get_google_calendar_client
from app.automation.makecom import get_makecom_client

logger = get_logger()
settings = get_settings()

class VapiWebhookHandler:
    def __init__(self):
        config = get_voice_ai_config()
        self.webhook_secret = config.get("vapi", {}).get("webhook_secret")

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Vapi webhook signature"""
        if not self.webhook_secret:
            logger.warning("Vapi webhook secret not configured")
            return True  # Skip verification if no secret

        if not signature:
            return False

        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    async def process_webhook(self, payload: Dict[str, Any], signature: str):
        """Processes the incoming Vapi webhook."""
        # Vapi doesn't send the signature in a standard way that we can verify without the raw body.
        # This is a limitation we'll accept for now. A more robust solution would involve a middleware.

        message = payload.get("message", {})
        event_type = message.get("type")

        if event_type == "call-start":
            return await self.handle_call_start(message)
        elif event_type == "call-end":
            return await self.handle_call_end(message)
        elif event_type == "function-call":
            return await self.handle_function_call(message)
        else:
            logger.warning(f"Unhandled Vapi event type: {event_type}")
            return JSONResponse({"status": "ignored"})

    async def handle_call_start(self, message: Dict[str, Any]):
        """Handle call start webhook"""
        call_id = message.get("call", {}).get("id")
        logger.info(f"Vapi call started: {call_id}")
        return JSONResponse({"status": "success"})

    async def handle_call_end(self, message: Dict[str, Any]):
        """Handle call end webhook"""
        call_id = message.get("call", {}).get("id")
        transcript = message.get("transcript", "")
        logger.info(f"Vapi call ended: {call_id}")
        logger.info(f"Transcript: {transcript}")
        return JSONResponse({"status": "success"})

    async def handle_function_call(self, message: Dict[str, Any]):
        """Handle function call webhook (for appointment booking)"""
        function_call = message.get("functionCall", {})
        function_name = function_call.get("name")
        parameters = function_call.get("parameters", {})

        logger.info(f"Vapi function call: {function_name} with parameters: {parameters}")

        if function_name == "book_appointment":
            result = await self._book_appointment(parameters)
            return JSONResponse({"result": result})
        elif function_name == "check_availability":
            result = await self._check_availability(parameters)
            return JSONResponse({"result": result})
        elif function_name == "get_services":
            result = await self._get_services(parameters)
            return JSONResponse({"result": result})
        else:
            logger.warning(f"Unknown function: {function_name}")
            return JSONResponse({"error": "Unknown function"}, status_code=400)

    async def _book_appointment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment booking function"""
        try:
            customer_name = parameters.get("customer_name")
            customer_phone = parameters.get("customer_phone")
            customer_email = parameters.get("customer_email")
            service_type = parameters.get("service_type")
            preferred_date = parameters.get("preferred_date")
            preferred_time = parameters.get("preferred_time")

            if not all([customer_name, customer_phone, service_type, preferred_date, preferred_time]):
                return {"error": "Missing required booking information"}

            appointment_datetime = datetime.fromisoformat(f"{preferred_date}T{preferred_time}")
            duration_minutes = 60 if service_type.lower() == "full_service" else 30
            end_time = appointment_datetime + timedelta(minutes=duration_minutes)

            google_calendar_client = await get_google_calendar_client()
            conflicts = await google_calendar_client.check_availability(
                appointment_datetime, end_time
            )

            if conflicts:
                return {"error": "Time slot not available", "conflicts": conflicts}

            event_data = {
                "title": f"Appointment - {customer_name}",
                "description": f"Service: {service_type}\nCustomer: {customer_name}\nPhone: {customer_phone}",
                "start_time": appointment_datetime,
                "end_time": end_time,
                "customer_email": customer_email
            }

            event = await google_calendar_client.create_event(event_data)
            
            makecom_client = await get_makecom_client()
            await makecom_client.trigger_workflow({
                "event_type": "appointment_booked",
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "service_type": service_type,
                "appointment_time": appointment_datetime.isoformat(),
                "calendar_event_id": event.get("id")
            })

            logger.info(f"Appointment booked successfully: {event.get('id')}")

            return {
                "success": True,
                "message": f"Appointment booked successfully for {customer_name} on {preferred_date} at {preferred_time}",
                "event_id": event.get("id"),
                "event_url": event.get("htmlLink")
            }
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {"error": "Failed to book appointment"}

    async def _check_availability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle availability check function"""
        try:
            date_str = parameters.get("date")
            duration_minutes = parameters.get("duration", 60)

            if not date_str:
                return {"error": "Date is required"}

            date = datetime.fromisoformat(date_str)
            google_calendar_client = await get_google_calendar_client()
            available_slots = await google_calendar_client.get_available_slots(
                date, duration_minutes
            )
            
            formatted_slots = [
                {
                    "start_time": slot["start_time"].strftime("%H:%M"),
                    "end_time": slot["end_time"].strftime("%H:%M"),
                    "available": slot["available"]
                } for slot in available_slots
            ]

            return {
                "success": True,
                "date": date_str,
                "available_slots": formatted_slots
            }
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {"error": "Failed to check availability"}

    async def _get_services(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get services function"""
        try:
            services = [
                {
                    "name": "consultation",
                    "display_name": "Consultation",
                    "duration": 30,
                    "price": 100,
                    "description": "30-minute consultation session"
                },
                {
                    "name": "full_service",
                    "display_name": "Full Service",
                    "duration": 60,
                    "price": 200,
                    "description": "60-minute full service session"
                }
            ]
            return {
                "success": True,
                "services": services
            }
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return {"error": "Failed to get services"}