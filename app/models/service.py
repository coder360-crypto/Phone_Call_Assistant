# app/models/service.py
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import timedelta

class Service(BaseModel):
    """Service data model"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    duration: timedelta  # Duration in minutes
    price: Decimal
    is_active: bool = True
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        if v <= timedelta(0):
            raise ValueError('Duration must be positive')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip()

class ServiceCreate(BaseModel):
    """Service creation model"""
    name: str
    description: Optional[str] = None
    duration: timedelta
    price: Decimal
    category: Optional[str] = None

class ServiceUpdate(BaseModel):
    """Service update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[timedelta] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None

class ServiceResponse(BaseModel):
    """Service response model for API"""
    id: str
    name: str
    description: Optional[str] = None
    duration_minutes: int
    price: float
    is_active: bool
    category: Optional[str] = None
    
    @validator('duration_minutes', pre=True)
    def convert_duration(cls, v):
        if isinstance(v, timedelta):
            return int(v.total_seconds() / 60)
        return v
    
    @validator('price', pre=True)
    def convert_price(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v