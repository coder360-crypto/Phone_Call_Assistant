"""
Main FastAPI application for the Phone Call Assistant
"""
import os
import uvicorn
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging
from datetime import datetime, date, time

# Import our modules
from config.settings import settings
from app.models import (
    Customer, Appointment, Service, WebhookPayload # CallRecord
)
from app.voice_ai.service import get_voice_ai_service
from app.scheduling.service import get_scheduling_service
from app.automation.service import get_automation_service
from app.webhooks.service import get_webhook_handler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Phone Call Assistant API",
    description="AI-powered phone call assistant for appointment booking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for protected endpoints"""
    if credentials.credentials != settings.secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Configuration endpoint
@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "business_name": settings.business_name,
        "services": {}, # settings.services is not a dict
        "availability": {}, # settings.availability is not a dict
        "timezone": settings.timezone,
        "voice_ai_platform": settings.voice_ai_platform
    }

# Voice AI endpoints
@app.post("/voice-ai/create-assistant")
async def create_assistant(
    assistant_config: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Create a new AI assistant"""
    try:
        provider = assistant_config.get("provider", settings.voice_ai_platform)
        voice_ai_service = get_voice_ai_service(provider)
        result = await voice_ai_service.create_assistant(**assistant_config)
        return {"success": True, "assistant": result}
    except Exception as e:
        logger.error(f"Error creating assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-ai/initiate-call")
async def initiate_call(
    call_data: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Initiate an outbound call"""
    try:
        phone_number = call_data.get("phone_number")
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")

        provider = call_data.get("provider", settings.voice_ai_platform)
        voice_ai_service = get_voice_ai_service(provider)
        result = await voice_ai_service.initiate_call(phone_number, **call_data)
        return {"success": True, "call": result}
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice-ai/call/{call_id}")
async def get_call_details(
    call_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get details of a specific call"""
    try:
        # This might need a provider parameter if different providers are used
        voice_ai_service = get_voice_ai_service(settings.voice_ai_platform)
        result = await voice_ai_service.get_call_details(call_id)
        return {"success": True, "call": result}
    except Exception as e:
        logger.error(f"Error getting call details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Scheduling endpoints
@app.get("/scheduling/availability")
async def check_availability(
    date: str,
    service: str = "consultation",
    api_key: str = Depends(verify_api_key)
):
    """Check available appointment slots"""
    try:
        appointment_date = date.fromisoformat(date)

        # Get service duration
        # service_config = settings.services.get(service, {"duration": 60})
        duration = 60 # service_config.get("duration", 60)

        scheduling_service = get_scheduling_service(settings.scheduling_platform)
        slots = await scheduling_service.check_availability(appointment_date, duration)

        formatted_slots = [
            {
                "date": slot.date.isoformat(),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "available": slot.available
            }
            for slot in slots
        ]

        return {
            "success": True,
            "date": appointment_date.isoformat(),
            "available_slots": formatted_slots
        }
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduling/book")
async def book_appointment(
    appointment_data: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Book an appointment"""
    try:
        # Create customer object
        customer_data = appointment_data.get("customer", {})
        customer = Customer(
            name=customer_data.get("name", ""),
            phone=customer_data.get("phone", ""),
            email=customer_data.get("email", ""),
            notes=customer_data.get("notes", "")
        )

        # Create service object
        service_name = appointment_data.get("service", "consultation")
        # service_config = settings.services.get(service_name, {})
        service = Service(
            id=service_name,
            name=service_name, # service_config.get("name", service_name),
            duration=60, # service_config.get("duration", 60),
            price=0, # service_config.get("price", 0),
            description="" # service_config.get("description", "")
        )

        # Create appointment object
        appointment = Appointment(
            customer=customer,
            service=service,
            scheduled_date=date.fromisoformat(appointment_data.get("date")),
            scheduled_time=time.fromisoformat(appointment_data.get("time")),
            duration=service.duration,
            notes=appointment_data.get("notes", "")
        )

        # Book the appointment
        scheduling_service = get_scheduling_service(settings.scheduling_platform)
        result = await scheduling_service.book_appointment(appointment)

        if result.get("success"):
            automation_service = get_automation_service(settings.automation_platform)
            # Trigger automation workflows
            appointment.id = result.get("appointment_id")
            await automation_service.trigger_appointment_workflow(appointment, "created")
            await automation_service.trigger_customer_workflow(customer, "created")
            await automation_service.send_appointment_confirmation(appointment)

        return result

    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/scheduling/appointment/{appointment_id}")
async def cancel_appointment(
    appointment_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Cancel an appointment"""
    try:
        scheduling_service = get_scheduling_service(settings.scheduling_platform)
        result = await scheduling_service.cancel_appointment(appointment_id)

        if result.get("success"):
            automation_service = get_automation_service(settings.automation_platform)
            # Trigger automation workflow
            await automation_service.trigger_appointment_workflow(None, "cancelled")

        return result

    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/scheduling/appointment/{appointment_id}")
async def reschedule_appointment(
    appointment_id: str,
    reschedule_data: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Reschedule an appointment"""
    try:
        new_date = date.fromisoformat(reschedule_data.get("date"))
        new_time = time.fromisoformat(reschedule_data.get("time"))

        scheduling_service = get_scheduling_service(settings.scheduling_platform)
        result = await scheduling_service.reschedule_appointment(
            appointment_id, new_date, new_time
        )

        if result.get("success"):
            automation_service = get_automation_service(settings.automation_platform)
            # Trigger automation workflow
            await automation_service.trigger_appointment_workflow(None, "rescheduled")

        return result

    except Exception as e:
        logger.error(f"Error rescheduling appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoints
@app.post("/webhooks/vapi")
async def vapi_webhook(request: Request):
    """Handle Vapi AI webhooks"""
    try:
        payload = await request.json()
        signature = request.headers.get("X-Vapi-Signature")

        handler = get_webhook_handler("vapi")
        result = await handler.process_webhook(payload, signature)

        return result

    except Exception as e:
        logger.error(f"Error processing Vapi webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/retell")
async def retell_webhook(request: Request):
    """Handle Retell AI webhooks"""
    try:
        payload = await request.json()
        signature = request.headers.get("X-Retell-Signature")

        handler = get_webhook_handler("retell")
        result = await handler.process_webhook(payload, signature)

        return result

    except Exception as e:
        logger.error(f"Error processing Retell webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/twilio", response_class=Response)
async def twilio_webhook(request: Request):
    """Handle Twilio Voice webhooks"""
    try:
        # Twilio sends form data, not JSON
        form_data = await request.form()
        payload = dict(form_data)
        signature = request.headers.get("X-Twilio-Signature")

        handler = get_webhook_handler("twilio")
        twiml = await handler.process_webhook(payload, signature)

        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        error_twiml = f"<Response><Say>An error occurred: {str(e)}</Say></Response>"
        return Response(content=error_twiml, media_type="application/xml")

# Function calling endpoint (for AI assistants)
@app.post("/functions/execute")
async def execute_function(function_data: Dict[str, Any]):
    """Execute a function call from an AI assistant"""
    try:
        function_name = function_data.get("function_name")
        parameters = function_data.get("parameters", {})

        # Get appropriate webhook handler to process the function
        platform = function_data.get("platform", settings.voice_ai_platform)
        handler = get_webhook_handler(platform)

        result = await handler.process_function_call(function_name, parameters)

        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error executing function: {e}")
        return {"success": False, "error": str(e)}

# Automation endpoints
@app.post("/automation/trigger")
async def trigger_automation(
    automation_data: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Manually trigger automation workflows"""
    try:
        action = automation_data.get("action")
        data = automation_data.get("data", {})
        provider = automation_data.get("provider", settings.automation_platform)
        automation_service = get_automation_service(provider)

        if action == "appointment_created":
            # Create appointment object from data
            appointment = Appointment(**data)
            result = await automation_service.trigger_appointment_workflow(appointment, "created")
        elif action == "customer_created":
            # Create customer object from data
            customer = Customer(**data)
            result = await automation_service.trigger_customer_workflow(customer, "created")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

        return {"success": True, "results": result}

    except Exception as e:
        logger.error(f"Error triggering automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/analytics/calls")
async def get_call_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get call analytics data"""
    # This would typically query a database
    # For now, return placeholder data
    analytics_data = {
        "total_calls": 0,
        "successful_bookings": 0,
        "conversion_rate": 0.0,
        "average_call_duration": "0:00",
        "top_services": []
    }
    
    # Example of how you might fetch and process data:
    # from your_database_module import analytics_db
    # analytics_data = await analytics_db.get_call_analytics(start_date, end_date)
    
    return analytics_data

@app.get("/analytics/appointments")
async def get_appointment_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get appointment analytics data"""
    # This would typically query a database
    # For now, return placeholder data
    analytics_data = {
        "total_appointments": 0,
        "confirmed": 0,
        "cancelled": 0,
        "no_shows": 0,
        "revenue": 0.0,
        "average_booking_value": 0.0
    }

    # Example of how you might fetch and process data:
    # from your_database_module import analytics_db
    # analytics_data = await analytics_db.get_appointment_analytics(start_date, end_date)
    
    return analytics_data

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": str(exc)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Please try again later"}
    )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
