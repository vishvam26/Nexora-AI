from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class MLTrainRequest(BaseModel):
    target_column: str
    feature_columns: List[str]
    algorithm: Optional[str] = "random_forest"


class MLPredictRequest(BaseModel):
    inputs: Dict[str, Any]
