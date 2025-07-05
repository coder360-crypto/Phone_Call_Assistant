# app/scheduling/google_calendar.py

import json
import pickle
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger
from ..utils.config_loader import get_settings
from ..models.appointment import Appointment
from ..models.customer import Customer

settings = get_settings()

class GoogleCalendarClient:
    """
    Google Calendar integration client for appointment scheduling
    """
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_file: Optional[str] = None, token_file: Optional[str] = None):
        self.credentials_file = credentials_file or settings.GOOGLE_CREDENTIALS_FILE
        self.token_file = token_file or settings.GOOGLE_TOKEN_FILE or "token.pickle"
        self.calendar_id = settings.GOOGLE_CALENDAR_ID or "primary"
        self.service = None
        self.credentials = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API
        """
        try:
            # Load existing credentials
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If there are no valid credentials, request authorization
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Google credentials file not found: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            logger.info("Successfully authenticated with Google Calendar")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {str(e)}")
            return False
    
    async def get_calendar_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available calendars
        """
        try:
            if not self.service:
                await self.authenticate()
            
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            logger.info(f"Retrieved {len(calendars)} calendars from Google Calendar")
            return calendars
            
        except HttpError as e:
            logger.error(f"Error getting calendar list: {str(e)}")
            return []
    
    async def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new event in Google Calendar
        """
        try:
            if not self.service:
                await self.authenticate()
            
            event = {
                'summary': event_data.get('title', 'Phone Call Appointment'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data.get('start_time'),
                    'timeZone': event_data.get('timezone', 'UTC'),
                },
                'end': {
                    'dateTime': event_data.get('end_time'),
                    'timeZone': event_data.get('timezone', 'UTC'),
                },
                'attendees': [
                    {'email': event_data.get('attendee_email')},
                ] if event_data.get('attendee_email') else [],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            
            # Add additional fields if provided
            if event_data.get('location'):
                event['location'] = event_data['location']
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Created event in Google Calendar: {created_event.get('id')}")
            return created_event
            
        except HttpError as e:
            logger.error(f"Error creating event in Google Calendar: {str(e)}")
            return None
    
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get event details by ID
        """
        try:
            if not self.service:
                await self.authenticate()
            
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Retrieved event from Google Calendar: {event_id}")
            return event
            
        except HttpError as e:
            logger.error(f"Error getting event from Google Calendar: {str(e)}")
            return None
    
    async def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing event
        """
        try:
            if not self.service:
                await self.authenticate()
            
            # Get existing event
            event = await self.get_event(event_id)
            if not event:
                return None
            
            # Update event fields
            if event_data.get('title'):
                event['summary'] = event_data['title']
            if event_data.get('description'):
                event['description'] = event_data['description']
            if event_data.get('start_time'):
                event['start']['dateTime'] = event_data['start_time']
            if event_data.get('end_time'):
                event['end']['dateTime'] = event_data['end_time']
            if event_data.get('location'):
                event['location'] = event_data['location']
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Updated event in Google Calendar: {event_id}")
            return updated_event
            
        except HttpError as e:
            logger.error(f"Error updating event in Google Calendar: {str(e)}")
            return None
    
    async def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from Google Calendar
        """
        try:
            if not self.service:
                await self.authenticate()
            
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Deleted event from Google Calendar: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Error deleting event from Google Calendar: {str(e)}")
            return False
    
    async def get_busy_times(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """
        Get busy times for a specific time range
        """
        try:
            if not self.service:
                await self.authenticate()
            
            body = {
                "timeMin": start_time,
                "timeMax": end_time,
                "timeZone": "UTC",
                "items": [{"id": self.calendar_id}]
            }
            
            freebusy = self.service.freebusy().query(body=body).execute()
            busy_times = freebusy.get('calendars', {}).get(self.calendar_id, {}).get('busy', [])
            
            logger.info(f"Retrieved {len(busy_times)} busy periods")
            return busy_times
            
        except HttpError as e:
            logger.error(f"Error getting busy times from Google Calendar: {str(e)}")
            return []
    
    async def find_available_slots(self, date: str, duration_minutes: int = 60, 
                                  start_hour: int = 9, end_hour: int = 17) -> List[Dict[str, Any]]:
        """
        Find available time slots for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            duration_minutes: Duration of the appointment in minutes
            start_hour: Start hour for availability check (24-hour format)
            end_hour: End hour for availability check (24-hour format)
        """
        try:
            # Create start and end times for the day
            start_time = datetime.strptime(f"{date} {start_hour:02d}:00:00", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(f"{date} {end_hour:02d}:00:00", "%Y-%m-%d %H:%M:%S")
            
            # Get busy times for the day
            busy_times = await self.get_busy_times(
                start_time.isoformat() + "Z",
                end_time.isoformat() + "Z"
            )
            
            # Convert busy times to datetime objects
            busy_periods = []
            for busy in busy_times:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                busy_periods.append((busy_start, busy_end))
            
            # Find available slots
            available_slots = []
            current_time = start_time
            
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any busy period
                is_available = True
                for busy_start, busy_end in busy_periods:
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'duration': duration_minutes
                    })
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            logger.info(f"Found {len(available_slots)} available slots for {date}")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error finding available slots: {str(e)}")
            return []
    
    async def book_appointment_from_phone_call(self, appointment: Appointment, customer: Customer) -> Optional[str]:
        """
        Book appointment from phone call assistant
        
        Returns:
            Event ID if successful, None otherwise
        """
        try:
            # Prepare event data
            event_data = {
                'title': f"{appointment.service_type} - {customer.name}",
                'description': f"Phone call appointment for {appointment.service_type}\n\n"
                              f"Customer: {customer.name}\n"
                              f"Phone: {customer.phone}\n"
                              f"Email: {customer.email}\n"
                              f"Notes: {appointment.notes or 'None'}",
                'start_time': appointment.start_time.isoformat(),
                'end_time': appointment.end_time.isoformat(),
                'attendee_email': customer.email,
                'timezone': 'UTC'
            }
            
            # Create event
            event = await self.create_event(event_data)
            
            if event:
                return event.get('id')
            
            return None
            
        except Exception as e:
            logger.error(f"Error booking appointment from phone call: {str(e)}")
            return None
    
    async def get_upcoming_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get upcoming events from calendar
        """
        try:
            if not self.service:
                await self.authenticate()
            
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} upcoming events")
            return events
            
        except HttpError as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            return []
    
    async def check_availability(self, start_time: str, end_time: str) -> bool:
        """
        Check if a specific time slot is available
        """
        try:
            busy_times = await self.get_busy_times(start_time, end_time)
            
            # If there are no busy times, the slot is available
            if not busy_times:
                return True
            
            # Check if the requested time conflicts with any busy period
            request_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            request_end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            for busy in busy_times:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                
                if (request_start < busy_end and request_end > busy_start):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return False

# Utility function to get Google Calendar client instance
async def get_google_calendar_client() -> GoogleCalendarClient:
    """Get configured Google Calendar client"""
    client = GoogleCalendarClient()
    await client.authenticate()
    return client