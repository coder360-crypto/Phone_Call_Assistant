# app/automation/service.py
from app.utils.config_loader import get_automation_config
from .makecom import MakecomClient
from .zapier import ZapierClient

def get_automation_service(provider: str):
    """Get the automation service client based on the provider."""
    config = get_automation_config()
    
    if provider == "makecom":
        return MakecomClient(webhook_url=config["makecom"]["webhook_url"])
    elif provider == "zapier":
        return ZapierClient(webhook_url=config["zapier"]["webhook_url"])
    else:
        raise ValueError(f"Unsupported automation provider: {provider}") 