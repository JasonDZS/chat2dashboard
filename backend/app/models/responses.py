from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class TableInfo(BaseModel):
    table_name: str
    filename: str
    rows: int
    columns: List[str]

class DatabaseInfo(BaseModel):
    name: str
    path: str
    has_schema: bool
    created_at: Optional[str] = None
    table_count: Optional[int] = None

class UploadResponse(BaseModel):
    message: str
    database_name: str
    database_path: str
    tables: List[TableInfo]
    total_files: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str

class SystemStatus(BaseModel):
    cpu_percent: float
    memory: Dict[str, Any]
    disk: Dict[str, Any]

class StatusResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    system: SystemStatus

class ColumnInfo(BaseModel):
    name: str
    type: str
    not_null: bool
    default_value: Any
    primary_key: bool

class TableSchema(BaseModel):
    table_name: str
    row_count: int
    columns: List[ColumnInfo]

class DatabaseSchema(BaseModel):
    database_name: str
    database_path: str
    tables: List[TableSchema]

class LogsResponse(BaseModel):
    logs: List[Dict[str, Any]]
    limit: int
    offset: int
    count: int

class ErrorResponse(BaseModel):
    error: str