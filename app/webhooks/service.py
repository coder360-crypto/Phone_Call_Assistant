# app/webhooks/service.py
from .vapi_webhook import VapiWebhookHandler
from .retell_webhook import RetellWebhookHandler
# Assuming a TwilioWebhookHandler exists
# from .twilio_webhook import TwilioWebhookHandler 

def get_webhook_handler(provider: str):
    """Get the webhook handler based on the provider."""
    if provider == "vapi":
        return VapiWebhookHandler()
    elif provider == "retell":
        return RetellWebhookHandler()
    # elif provider == "twilio":
    #     return TwilioWebhookHandler()
    else:
        raise ValueError(f"Unsupported webhook provider: {provider}") 