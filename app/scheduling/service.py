# app/scheduling/service.py
from app.utils.config_loader import get_scheduling_config
from .google_calendar import GoogleCalendarClient
from .calcom import CalcomClient
from .crm import CRMClient

def get_scheduling_service(provider: str):
    """Get the scheduling service client based on the provider."""
    config = get_scheduling_config()
    
    if provider == "google_calendar":
        return GoogleCalendarClient(
            credentials_path=config["google_calendar"]["credentials_path"],
            calendar_id=config["google_calendar"]["calendar_id"]
        )
    elif provider == "calcom":
        return CalcomClient(api_key=config["calcom"]["api_key"])
    elif provider == "crm":
        # Assuming CRMClient has a similar initialization
        return CRMClient()
    else:
        raise ValueError(f"Unsupported scheduling provider: {provider}") 