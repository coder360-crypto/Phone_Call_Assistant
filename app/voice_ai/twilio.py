# app/voice_ai/twilio.py

import httpx
from typing import Dict, Any, Optional, List
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from loguru import logger
from app.utils.config_loader import get_settings
from app.models.customer import Customer
from app.models.appointment import Appointment

settings = get_settings()

class TwilioClient:
    """
    Twilio integration client for voice calls and SMS
    """
    
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.client = Client(self.account_sid, self.auth_token)
        
        # OpenAI integration for voice processing
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self.openai_api_key}"}
        )
    
    def create_twiml_response(self, message: str, gather_input: bool = False, 
                            gather_timeout: int = 5, gather_num_digits: int = 1) -> str:
        """
        Create TwiML response for voice calls
        """
        try:
            response = VoiceResponse()
            
            if gather_input:
                gather = response.gather(
                    num_digits=gather_num_digits,
                    timeout=gather_timeout,
                    action='/webhooks/twilio/gather'
                )
                gather.say(message, voice='alice')
            else:
                response.say(message, voice='alice')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error creating TwiML response: {str(e)}")
            return str(VoiceResponse().say("Sorry, there was an error processing your request."))
    
    async def make_call(self, to_number: str, message: str) -> Optional[str]:
        """
        Make an outbound call
        """
        try:
            call = self.client.calls.create(
                twiml=f'<Response><Say voice="alice">{message}</Say></Response>',
                to=to_number,
                from_=self.phone_number
            )
            
            logger.info(f"Made call to {to_number}: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Error making call: {str(e)}")
            return None
    
    async def send_sms(self, to_number: str, message: str) -> Optional[str]:
        """
        Send SMS message
        """
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            
            logger.info(f"Sent SMS to {to_number}: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return None
    
    async def process_voice_input(self, audio_url: str) -> Optional[str]:
        """
        Process voice input using OpenAI Whisper
        """
        try:
            # Download audio file
            async with httpx.AsyncClient() as client:
                audio_response = await client.get(audio_url)
                audio_data = audio_response.content
            
            # Send to OpenAI Whisper for transcription
            files = {"file": audio_data}
            data = {"model": "whisper-1"}
            
            response = await self.openai_client.post("/audio/transcriptions", files=files, data=data)
            
            if response.status_code == 200:
                transcription = response.json().get("text", "")
                logger.info(f"Transcribed audio: {transcription}")
                return transcription
            else:
                logger.error(f"OpenAI transcription failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing voice input: {str(e)}")
            return None
    
    async def generate_ai_response(self, user_input: str, conversation_context: List[Dict[str, str]]) -> str:
        """
        Generate AI response using OpenAI GPT
        """
        try:
            # Prepare conversation context
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful phone call assistant for appointment booking. 
                    You can help customers:
                    1. Book appointments
                    2. Answer questions about services and pricing
                    3. Reschedule or cancel appointments
                    
                    Be friendly, professional, and helpful. Ask for necessary information to complete bookings.
                    Available services: Consultation ($100), Therapy Session ($150), Group Session ($75).
                    Business hours: Monday-Friday 9 AM - 5 PM."""
                }
            ]
            
            # Add conversation context
            messages.extend(conversation_context)
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            response = await self.openai_client.post(
                "/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                logger.info(f"Generated AI response: {ai_response}")
                return ai_response
            else:
                logger.error(f"OpenAI chat completion failed: {response.status_code}")
                return "I'm sorry, I'm having trouble processing your request right now."
                
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "I'm sorry, I'm having trouble processing your request right now."
    
    async def handle_appointment_booking(self, customer_info: Dict[str, Any], 
                                       appointment_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle appointment booking workflow
        """
        try:
            # Create customer and appointment objects
            customer = Customer(
                name=customer_info.get("name", ""),
                phone=customer_info.get("phone", ""),
                email=customer_info.get("email", "")
            )
            
            appointment = Appointment(
                customer_name=customer.name,
                customer_phone=customer.phone,
                customer_email=customer.email,
                service_type=appointment_details.get("service_type", ""),
                start_time=appointment_details.get("start_time"),
                end_time=appointment_details.get("end_time"),
                notes=appointment_details.get("notes", "")
            )
            
            # Here you would integrate with your chosen scheduling backend
            # For now, we'll simulate successful booking
            
            booking_result = {
                "success": True,
                "appointment_id": f"twilio_{appointment.id}",
                "confirmation_message": f"Great! I've booked your {appointment.service_type} appointment for {appointment.start_time.strftime('%B %d, %Y at %I:%M %p')}. You'll receive a confirmation via SMS."
            }
            
            # Send confirmation SMS
            if customer.phone:
                await self.send_appointment_confirmation(customer.phone, appointment)
            
            return booking_result
            
        except Exception as e:
            logger.error(f"Error handling appointment booking: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "confirmation_message": "I'm sorry, there was an error booking your appointment. Please try again."
            }
    
    async def send_appointment_confirmation(self, phone_number: str, appointment: Appointment) -> bool:
        """
        Send appointment confirmation via SMS
        """
        try:
            message = f"""
Appointment Confirmed!

Service: {appointment.service_type}
Date: {appointment.start_time.strftime('%B %d, %Y')}
Time: {appointment.start_time.strftime('%I:%M %p')}
Customer: {appointment.customer_name}

Thank you for booking with us!
            """.strip()
            
            result = await self.send_sms(phone_number, message)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {str(e)}")
            return False
    
    async def send_appointment_reminder(self, phone_number: str, appointment: Appointment) -> bool:
        """
        Send appointment reminder via SMS
        """
        try:
            message = f"""
Appointment Reminder

You have a {appointment.service_type} appointment tomorrow at {appointment.start_time.strftime('%I:%M %p')}.

Please call us if you need to reschedule.
            """.strip()
            
            result = await self.send_sms(phone_number, message)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {str(e)}")
            return False
    
    def get_call_details(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Get call details from Twilio
        """
        try:
            call = self.client.calls(call_sid).fetch()
            
            call_details = {
                "sid": call.sid,
                "from": call.from_,
                "to": call.to,
                "duration": call.duration,
                "status": call.status,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "direction": call.direction
            }
            
            logger.info(f"Retrieved call details: {call_sid}")
            return call_details
            
        except Exception as e:
            logger.error(f"Error getting call details: {str(e)}")
            return None
    
    def get_message_details(self, message_sid: str) -> Optional[Dict[str, Any]]:
        """
        Get message details from Twilio
        """
        try:
            message = self.client.messages(message_sid).fetch()
            
            message_details = {
                "sid": message.sid,
                "from": message.from_,
                "to": message.to,
                "body": message.body,
                "status": message.status,
                "date_created": message.date_created,
                "date_sent": message.date_sent,
                "direction": message.direction
            }
            
            logger.info(f"Retrieved message details: {message_sid}")
            return message_details
            
        except Exception as e:
            logger.error(f"Error getting message details: {str(e)}")
            return None
    
    async def handle_inbound_call(self, call_data: Dict[str, Any]) -> str:
        """
        Handle inbound call webhook
        """
        try:
            caller_number = call_data.get("From", "")
            call_sid = call_data.get("CallSid", "")
            
            logger.info(f"Handling inbound call from {caller_number}: {call_sid}")
            
            # Generate greeting
            greeting = "Hello! Thank you for calling. I'm your AI assistant and I can help you book an appointment, answer questions about our services, or connect you with someone who can help. How can I assist you today?"
            
            # Create TwiML response to gather input
            twiml = self.create_twiml_response(greeting, gather_input=True, gather_timeout=10)
            
            return twiml
            
        except Exception as e:
            logger.error(f"Error handling inbound call: {str(e)}")
            return str(VoiceResponse().say("Sorry, there was an error processing your call."))
    
    async def handle_gather_input(self, gather_data: Dict[str, Any]) -> str:
        """
        Handle gathered input from caller
        """
        try:
            digits = gather_data.get("Digits", "")
            speech_result = gather_data.get("SpeechResult", "")
            
            # Process the input
            user_input = speech_result or digits
            
            if not user_input:
                return self.create_twiml_response("I didn't hear anything. Please try again.")
            
            # Generate AI response
            response = await self.generate_ai_response(user_input, [])
            
            # Create TwiML response
            return self.create_twiml_response(response, gather_input=True)
            
        except Exception as e:
            logger.error(f"Error handling gather input: {str(e)}")
            return str(VoiceResponse().say("Sorry, there was an error processing your input."))
    
    async def close(self):
        """Close HTTP clients"""
        await self.openai_client.aclose()

# Utility function to get Twilio client instance
def get_twilio_client() -> TwilioClient:
    """Get configured Twilio client"""
    return TwilioClient()