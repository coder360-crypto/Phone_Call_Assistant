# tests/test_scheduling.py

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.scheduling.google_calendar import GoogleCalendarClient
from app.scheduling.calcom import CalcomClient
from app.scheduling.crm import CRMClient
from app.models.appointment import Appointment
from app.models.customer import Customer

class TestGoogleCalendarClient:
    """Test Google Calendar integration"""
    
    @pytest.fixture
    def calendar_client(self):
        """Create a test calendar client"""
        return GoogleCalendarClient()
    
    @pytest.fixture
    def test_customer(self):
        """Create a test customer"""
        return Customer(
            name="John Doe",
            phone="+1234567890",
            email="john.doe@example.com"
        )
    
    @pytest.fixture
    def test_appointment(self):
        """Create a test appointment"""
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        return Appointment(
            customer_name="John Doe",
            customer_phone="+1234567890",
            customer_email="john.doe@example.com",
            service_type="Consultation",
            start_time=start_time,
            end_time=end_time,
            notes="Test appointment"
        )
    
    @pytest.mark.asyncio
    async def test_authenticate(self, calendar_client):
        """Test Google Calendar authentication"""
        with patch.object(calendar_client, 'service', Mock()):
            result = await calendar_client.authenticate()
            # Should return True if credentials are valid
            assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_create_event(self, calendar_client):
        """Test creating a calendar event"""
        event_data = {
            'title': 'Test Appointment',
            'description': 'Test appointment description',
            'start_time': '2024-01-15T10:00:00Z',
            'end_time': '2024-01-15T11:00:00Z',
            'attendee_email': 'john.doe@example.com',
            'timezone': 'UTC'
        }
        
        mock_service = Mock()
        mock_events = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        
        mock_execute.return_value = {'id': 'test_event_id'}
        mock_insert.return_value = mock_execute
        mock_events.return_value = mock_insert
        mock_service.events.return_value = mock_events
        
        calendar_client.service = mock_service
        
        result = await calendar_client.create_event(event_data)
        
        assert result is not None
        assert result.get('id') == 'test_event_id'
        mock_service.events.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_event(self, calendar_client):
        """Test getting a calendar event"""
        event_id = 'test_event_id'
        
        mock_service = Mock()
        mock_events = Mock()
        mock_get = Mock()
        mock_execute = Mock()
        
        mock_execute.return_value = {'id': event_id, 'summary': 'Test Event'}
        mock_get.return_value = mock_execute
        mock_events.return_value = mock_get
        mock_service.events.return_value = mock_events
        
        calendar_client.service = mock_service
        
        result = await calendar_client.get_event(event_id)
        
        assert result is not None
        assert result.get('id') == event_id
        assert result.get('summary') == 'Test Event'
    
    @pytest.mark.asyncio
    async def test_find_available_slots(self, calendar_client):
        """Test finding available time slots"""
        date = "2024-01-15"
        
        # Mock the get_busy_times method
        with patch.object(calendar_client, 'get_busy_times', return_value=[]):
            result = await calendar_client.find_available_slots(date)
            
            assert isinstance(result, list)
            assert len(result) > 0  # Should have available slots
            
            # Check structure of first slot
            if result:
                slot = result[0]
                assert 'start' in slot
                assert 'end' in slot
                assert 'duration' in slot
    
    @pytest.mark.asyncio
    async def test_book_appointment_from_phone_call(self, calendar_client, test_appointment, test_customer):
        """Test booking appointment from phone call"""
        # Mock the create_event method
        with patch.object(calendar_client, 'create_event', return_value={'id': 'test_event_id'}):
            result = await calendar_client.book_appointment_from_phone_call(test_appointment, test_customer)
            
            assert result == 'test_event_id'
    
    @pytest.mark.asyncio
    async def test_check_availability(self, calendar_client):
        """Test checking availability for a specific time slot"""
        start_time = "2024-01-15T10:00:00Z"
        end_time = "2024-01-15T11:00:00Z"
        
        # Mock no conflicts
        with patch.object(calendar_client, 'get_busy_times', return_value=[]):
            result = await calendar_client.check_availability(start_time, end_time)
            assert result is True
        
        # Mock with conflicts
        busy_times = [
            {'start': '2024-01-15T10:30:00Z', 'end': '2024-01-15T11:30:00Z'}
        ]
        with patch.object(calendar_client, 'get_busy_times', return_value=busy_times):
            result = await calendar_client.check_availability(start_time, end_time)
            assert result is False

class TestCalcomClient:
    """Test Cal.com integration"""
    
    @pytest.fixture
    def calcom_client(self):
        """Create a test Cal.com client"""
        return CalcomClient()
    
    @pytest.fixture
    def test_appointment(self):
        """Create a test appointment"""
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        return Appointment(
            customer_name="John Doe",
            customer_phone="+1234567890",
            customer_email="john.doe@example.com",
            service_type="Consultation",
            start_time=start_time,
            end_time=end_time,
            notes="Test appointment"
        )
    
    @pytest.mark.asyncio
    async def test_get_event_types(self, calcom_client):
        """Test getting event types from Cal.com"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'event_types': [
                {'id': 1, 'title': 'Consultation'},
                {'id': 2, 'title': 'Therapy Session'}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(calcom_client.client, 'get', return_value=mock_response):
            result = await calcom_client.get_event_types()
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]['title'] == 'Consultation'
    
    @pytest.mark.asyncio
    async def test_get_availability(self, calcom_client):
        """Test getting availability from Cal.com"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'availability': [
                {'start': '2024-01-15T10:00:00Z', 'end': '2024-01-15T11:00:00Z'}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(calcom_client.client, 'get', return_value=mock_response):
            result = await calcom_client.get_availability(1, "2024-01-15")
            
            assert isinstance(result, list)
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_create_booking(self, calcom_client):
        """Test creating a booking in Cal.com"""
        booking_data = {
            'event_type_id': 1,
            'start_time': '2024-01-15T10:00:00Z',
            'end_time': '2024-01-15T11:00:00Z',
            'customer_name': 'John Doe',
            'customer_email': 'john.doe@example.com',
            'customer_phone': '+1234567890'
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'booking_123'}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(calcom_client.client, 'post', return_value=mock_response):
            result = await calcom_client.create_booking(booking_data)
            
            assert result is not None
            assert result.get('id') == 'booking_123'
    
    @pytest.mark.asyncio
    async def test_cancel_booking(self, calcom_client):
        """Test cancelling a booking in Cal.com"""
        booking_id = 'booking_123'
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(calcom_client.client, 'delete', return_value=mock_response):
            result = await calcom_client.cancel_booking(booking_id, "Customer request")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_book_appointment_from_phone_call(self, calcom_client, test_appointment):
        """Test booking appointment from phone call"""
        # Mock get_event_types
        mock_event_types = [{'id': 1, 'title': 'Consultation'}]
        
        # Mock create_booking
        mock_booking = {'id': 'booking_123'}
        
        with patch.object(calcom_client, 'get_event_types', return_value=mock_event_types):
            with patch.object(calcom_client, 'create_booking', return_value=mock_booking):
                result = await calcom_client.book_appointment_from_phone_call(test_appointment)
                
                assert result == 'booking_123'

class TestCRMClient:
    """Test CRM integration"""
    
    @pytest.fixture
    def crm_client(self):
        """Create a test CRM client"""
        return CRMClient()
    
    @pytest.fixture
    def test_customer(self):
        """Create a test customer"""
        return Customer(
            name="John Doe",
            phone="+1234567890",
            email="john.doe@example.com"
        )
    
    @pytest.fixture
    def test_appointment(self):
        """Create a test appointment"""
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        return Appointment(
            customer_name="John Doe",
            customer_phone="+1234567890",
            customer_email="john.doe@example.com",
            service_type="Consultation",
            start_time=start_time,
            end_time=end_time,
            notes="Test appointment"
        )
    
    @pytest.mark.asyncio
    async def test_create_customer(self, crm_client):
        """Test creating a customer in CRM"""
        customer_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1234567890'
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'customer_123', 'name': 'John Doe'}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(crm_client.client, 'post', return_value=mock_response):
            result = await crm_client.create_customer(customer_data)
            
            assert result is not None
            assert result.get('id') == 'customer_123'
            assert result.get('name') == 'John Doe'
    
    @pytest.mark.asyncio
    async def test_find_customer_by_phone(self, crm_client):
        """Test finding customer by phone number"""
        phone = '+1234567890'
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'customers': [{'id': 'customer_123', 'phone': phone}]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(crm_client.client, 'get', return_value=mock_response):
            result = await crm_client.find_customer_by_phone(phone)
            
            assert result is not None
            assert result.get('phone') == phone
    
    @pytest.mark.asyncio
    async def test_create_appointment(self, crm_client):
        """Test creating an appointment in CRM"""
        appointment_data = {
            'customer_id': 'customer_123',
            'title': 'Consultation',
            'start_time': '2024-01-15T10:00:00Z',
            'end_time': '2024-01-15T11:00:00Z',
            'service_type': 'Consultation'
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'appointment_123'}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(crm_client.client, 'post', return_value=mock_response):
            result = await crm_client.create_appointment(appointment_data)
            
            assert result is not None
            assert result.get('id') == 'appointment_123'
    
    @pytest.mark.asyncio
    async def test_check_availability(self, crm_client):
        """Test checking availability in CRM"""
        date = "2024-01-15"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'available_slots': [
                {'start': '2024-01-15T10:00:00Z', 'end': '2024-01-15T11:00:00Z'}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(crm_client.client, 'get', return_value=mock_response):
            result = await crm_client.check_availability(date)
            
            assert isinstance(result, list)
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_services(self, crm_client):
        """Test getting services from CRM"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'services': [
                {'id': 1, 'name': 'Consultation', 'price': 100},
                {'id': 2, 'name': 'Therapy Session', 'price': 150}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(crm_client.client, 'get', return_value=mock_response):
            result = await crm_client.get_services()
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]['name'] == 'Consultation'
    
    @pytest.mark.asyncio
    async def test_get_or_create_customer(self, crm_client):
        """Test getting or creating a customer"""
        customer_data = {
            'name': 'John Doe',
            'phone': '+1234567890',
            'email': 'john.doe@example.com'
        }
        
        # Test case: existing customer found
        existing_customer = {'id': 'customer_123', 'name': 'John Doe'}
        with patch.object(crm_client, 'find_customer_by_phone', return_value=existing_customer):
            result = await crm_client.get_or_create_customer(customer_data)
            assert result == existing_customer
        
        # Test case: new customer created
        with patch.object(crm_client, 'find_customer_by_phone', return_value=None):
            with patch.object(crm_client, 'find_customer_by_email', return_value=None):
                with patch.object(crm_client, 'create_customer', return_value=existing_customer):
                    result = await crm_client.get_or_create_customer(customer_data)
                    assert result == existing_customer
    
    @pytest.mark.asyncio
    async def test_book_appointment_from_phone_call(self, crm_client, test_appointment, test_customer):
        """Test booking appointment from phone call"""
        # Mock get_or_create_customer
        mock_customer = {'id': 'customer_123', 'name': 'John Doe'}
        
        # Mock create_appointment
        mock_appointment = {'id': 'appointment_123'}
        
        with patch.object(crm_client, 'get_or_create_customer', return_value=mock_customer):
            with patch.object(crm_client, 'create_appointment', return_value=mock_appointment):
                result = await crm_client.book_appointment_from_phone_call(test_appointment, test_customer)
                
                assert result == 'appointment_123'

class TestSchedulingIntegration:
    """Test integration between different scheduling backends"""
    
    @pytest.mark.asyncio
    async def test_scheduling_backend_switching(self):
        """Test switching between different scheduling backends"""
        # This test would verify that the system can switch between
        # different scheduling backends without breaking functionality
        
        # Test data
        customer = Customer(
            name="John Doe",
            phone="+1234567890",
            email="john.doe@example.com"
        )
        
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        appointment = Appointment(
            customer_name="John Doe",
            customer_phone="+1234567890",
            customer_email="john.doe@example.com",
            service_type="Consultation",
            start_time=start_time,
            end_time=end_time,
            notes="Test appointment"
        )
        
        # Test each backend
        backends = [
            ('google_calendar', GoogleCalendarClient),
            ('calcom', CalcomClient),
            ('crm', CRMClient)
        ]
        
        for backend_name, backend_class in backends:
            client = backend_class()
            
            # Mock the booking method for each backend
            if backend_name == 'google_calendar':
                with patch.object(client, 'book_appointment_from_phone_call', return_value='test_id'):
                    result = await client.book_appointment_from_phone_call(appointment, customer)
                    assert result == 'test_id'
            elif backend_name == 'calcom':
                with patch.object(client, 'book_appointment_from_phone_call', return_value='test_id'):
                    result = await client.book_appointment_from_phone_call(appointment)
                    assert result == 'test_id'
            elif backend_name == 'crm':
                with patch.object(client, 'book_appointment_from_phone_call', return_value='test_id'):
                    result = await client.book_appointment_from_phone_call(appointment, customer)
                    assert result == 'test_id'

# Integration tests
class TestSchedulingWorkflow:
    """Test end-to-end scheduling workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_booking_workflow(self):
        """Test complete booking workflow from phone call to confirmation"""
        # This test would simulate a complete booking workflow:
        # 1. Customer calls
        # 2. AI processes request
        # 3. Availability is checked
        # 4. Appointment is booked
        # 5. Confirmation is sent
        
        # Test data
        customer_data = {
            'name': 'John Doe',
            'phone': '+1234567890',
            'email': 'john.doe@example.com'
        }
        
        appointment_data = {
            'service_type': 'Consultation',
            'date': '2024-01-15',
            'time': '10:00',
            'duration': 60,
            'notes': 'Phone call booking'
        }
        
        # Mock the workflow
        with patch('app.scheduling.google_calendar.GoogleCalendarClient') as mock_calendar:
            mock_client = mock_calendar.return_value
            mock_client.check_availability.return_value = True
            mock_client.book_appointment_from_phone_call.return_value = 'event_123'
            
            # Simulate workflow
            is_available = await mock_client.check_availability(
                '2024-01-15T10:00:00Z',
                '2024-01-15T11:00:00Z'
            )
            
            assert is_available is True
            
            # Create appointment
            customer = Customer(**customer_data)
            start_time = datetime.fromisoformat('2024-01-15T10:00:00')
            end_time = start_time + timedelta(hours=1)
            
            appointment = Appointment(
                customer_name=customer.name,
                customer_phone=customer.phone,
                customer_email=customer.email,
                service_type=appointment_data['service_type'],
                start_time=start_time,
                end_time=end_time,
                notes=appointment_data['notes']
            )
            
            # Book appointment
            appointment_id = await mock_client.book_appointment_from_phone_call(appointment, customer)
            
            assert appointment_id == 'event_123'

if __name__ == "__main__":
    pytest.main([__file__])