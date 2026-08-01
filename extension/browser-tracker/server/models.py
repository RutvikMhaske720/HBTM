from pydantic import BaseModel
from typing import Any, Dict, Optional

class EventPayload(BaseModel):
    type: str
    timestamp: str
    data: Dict[str, Any]
