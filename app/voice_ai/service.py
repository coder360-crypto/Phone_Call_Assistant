# app/voice_ai/service.py
from app.utils.config_loader import get_voice_ai_config
from .vapi import VapiClient
from .retell import RetellClient
from .twilio import TwilioClient

def get_voice_ai_service(provider: str):
    """Get the voice AI service client based on the provider."""
    config = get_voice_ai_config()
    
    if provider == "vapi":
        return VapiClient(api_key=config["vapi"]["api_key"])
    elif provider == "retell":
        return RetellClient(api_key=config["retell"]["api_key"])
    elif provider == "twilio":
        return TwilioClient(
            account_sid=config["twilio"]["account_sid"],
            auth_token=config["twilio"]["auth_token"]
        )
    else:
        raise ValueError(f"Unsupported voice AI provider: {provider}") 