# app/utils/config_loader.py
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # General settings
    app_name: str = Field(default="Phone Call Assistant", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Voice AI settings
    vapi_api_key: Optional[str] = Field(default=None, env="VAPI_API_KEY")
    vapi_webhook_secret: Optional[str] = Field(default=None, env="VAPI_WEBHOOK_SECRET")
    
    retell_api_key: Optional[str] = Field(default=None, env="RETELL_API_KEY")
    retell_webhook_secret: Optional[str] = Field(default=None, env="RETELL_WEBHOOK_SECRET")
    
    # Twilio settings
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(default=None, env="TWILIO_PHONE_NUMBER")
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Google Calendar settings
    google_calendar_credentials_path: Optional[str] = Field(default=None, env="GOOGLE_CALENDAR_CREDENTIALS_PATH")
    google_calendar_id: Optional[str] = Field(default=None, env="GOOGLE_CALENDAR_ID")
    
    # Cal.com settings
    calcom_api_key: Optional[str] = Field(default=None, env="CALCOM_API_KEY")
    calcom_base_url: str = Field(default="https://api.cal.com", env="CALCOM_BASE_URL")
    
    # Make.com settings
    makecom_webhook_url: Optional[str] = Field(default=None, env="MAKECOM_WEBHOOK_URL")
    
    # Zapier settings
    zapier_webhook_url: Optional[str] = Field(default=None, env="ZAPIER_WEBHOOK_URL")
    
    # Database settings (if using database)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Business settings
    business_name: str = Field(default="Your Business", env="BUSINESS_NAME")
    business_phone: Optional[str] = Field(default=None, env="BUSINESS_PHONE")
    business_email: Optional[str] = Field(default=None, env="BUSINESS_EMAIL")
    
    # Timezone
    timezone: str = Field(default="UTC", env="TIMEZONE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

def load_env_file(file_path: str = ".env"):
    """Load environment variables from a specific file"""
    if os.path.exists(file_path):
        from dotenv import load_dotenv
        load_dotenv(file_path)
    else:
        print(f"Warning: Environment file {file_path} not found")

def get_voice_ai_config():
    """Get voice AI configuration"""
    settings = get_settings()
    return {
        "vapi": {
            "api_key": settings.vapi_api_key,
            "webhook_secret": settings.vapi_webhook_secret
        },
        "retell": {
            "api_key": settings.retell_api_key,
            "webhook_secret": settings.retell_webhook_secret
        },
        "twilio": {
            "account_sid": settings.twilio_account_sid,
            "auth_token": settings.twilio_auth_token,
            "phone_number": settings.twilio_phone_number
        },
        "openai": {
            "api_key": settings.openai_api_key
        }
    }

def get_scheduling_config():
    """Get scheduling configuration"""
    settings = get_settings()
    return {
        "google_calendar": {
            "credentials_path": settings.google_calendar_credentials_path,
            "calendar_id": settings.google_calendar_id
        },
        "calcom": {
            "api_key": settings.calcom_api_key,
            "base_url": settings.calcom_base_url
        }
    }

def get_automation_config():
    """Get automation configuration"""
    settings = get_settings()
    return {
        "makecom": {
            "webhook_url": settings.makecom_webhook_url
        },
        "zapier": {
            "webhook_url": settings.zapier_webhook_url
        }
    }