from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List


class ActivityLogResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    action: str
    entity: str
    entity_id: Optional[int]
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    # Map database name 'metadata_json' to Pydantic 'metadata' key if needed, or simply map via alias/custom resolver
    # Let's map it cleanly:
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Handle renaming database 'metadata_json' to Pydantic 'metadata'
        data = super().model_validate(obj, **kwargs)
        if hasattr(obj, "metadata_json"):
            data.metadata = obj.metadata_json
        return data

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class ActivityLogListResponse(BaseModel):
    logs: List[ActivityLogResponse]

    model_config = {
        "from_attributes": True
    }
