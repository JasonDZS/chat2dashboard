from pydantic import BaseModel
from typing import Optional, Dict, Any

class VisualizationRequest(BaseModel):
    query: str
    db_name: str
    chart_type: Optional[str] = None

class SchemaUpdateRequest(BaseModel):
    schema_data: Dict[str, Any]

class SQLTrainingRequest(BaseModel):
    question: str
    sql: str

class GenerateSQLRequest(BaseModel):
    num_questions: int = 10