# app/models/appointment.py
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

class AppointmentStatus(str, Enum):
    """Appointment status enumeration"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class Appointment(BaseModel):
    """Appointment data model"""
    id: Optional[str] = None
    customer_id: str
    service_id: str
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    external_id: Optional[str] = None  # For external calendar/CRM systems
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('start_time')
    def validate_start_time(cls, v):
        if v < datetime.now():
            raise ValueError('Start time cannot be in the past')
        return v

class AppointmentCreate(BaseModel):
    """Appointment creation model"""
    customer_id: str
    service_id: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    """Appointment update model"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AvailabilitySlot(BaseModel):
    """Available time slot model"""
    start_time: datetime
    end_time: datetime
    is_available: bool = True