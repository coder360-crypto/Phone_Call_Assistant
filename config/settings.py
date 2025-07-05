# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class AppSettings(BaseSettings):
    """Application settings configuration"""
    
    # Application
    app_name: str = "Phone Call Assistant"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Voice AI Platforms
    voice_ai_platform: str = "vapi"
    vapi_api_key: Optional[str] = None
    vapi_webhook_secret: Optional[str] = None
    
    retell_api_key: Optional[str] = None
    retell_webhook_secret: Optional[str] = None
    
    # Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Google Calendar
    google_calendar_credentials_path: Optional[str] = None
    google_calendar_id: Optional[str] = None
    
    # Scheduling Platform
    scheduling_platform: str = "google_calendar"
    
    # Cal.com
    calcom_api_key: Optional[str] = None
    calcom_base_url: str = "https://api.cal.com"
    
    # Automation
    automation_platform: str = "makecom"
    makecom_webhook_url: Optional[str] = None
    zapier_webhook_url: Optional[str] = None
    
    # Business Information
    business_name: str = "Your Business Name"
    business_phone: Optional[str] = None
    business_email: Optional[str] = None
    business_address: Optional[str] = None
    business_hours: str = "Monday-Friday 9 AM to 6 PM"
    
    # Services Configuration
    default_appointment_duration: int = 60  # minutes
    booking_advance_time: int = 24  # hours
    cancellation_policy: str = "24-hour notice required"
    
    # Timezone
    timezone: str = "UTC"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "app.log"
    
    # Security
    secret_key: str = "your-secret-key"
    cors_origins: list = ["*"]
    allowed_hosts: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = AppSettings()