# app/models/customer.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class Customer(BaseModel):
    """Customer data model"""
    id: Optional[str] = None
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove any non-numeric characters
        phone_clean = ''.join(filter(str.isdigit, v))
        if len(phone_clean) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class CustomerCreate(BaseModel):
    """Customer creation model"""
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: str

class CustomerUpdate(BaseModel):
    """Customer update model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None