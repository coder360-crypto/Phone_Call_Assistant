from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class WebhookPayload(BaseModel):
    """
    Represents the incoming webhook payload.
    Using a generic structure as the payload can vary between providers.
    """
    event: str = Field(..., description="The type of event.")
    payload: Dict[str, Any] = Field(..., description="The event payload.")
    provider: Optional[str] = Field(None, description="The webhook provider (e.g., 'vapi', 'retell').") 