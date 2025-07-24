from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from ...core.database import DatabaseManager
from ...core.exceptions import (
    DatabaseNotFoundError, 
    SchemaNotFoundError, 
    PandasNotAvailableError, 
    UnsupportedFileTypeError
)
from ...models.responses import UploadResponse, DatabaseSchema, ErrorResponse
from ...models.requests import SchemaUpdateRequest

router = APIRouter(prefix="/database", tags=["database"])

@router.post("/upload-files", response_model=UploadResponse)
async def upload_data_files(
    files: List[UploadFile] = File(...),
    db_name: str = Form(...)
):
    """Upload xlsx or csv files and create database"""
    try:
        # Validate file types
        for file in files:
            filename_lower = file.filename.lower()
            if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.csv')):
                raise UnsupportedFileTypeError(file.filename)
        
        # Create database from files
        created_tables, db_path = DatabaseManager.create_database_from_files(files, db_name)
        
        return UploadResponse(
            message="Database created successfully",
            database_name=db_name,
            database_path=db_path,
            tables=created_tables,
            total_files=len(files)
        )
    
    except (PandasNotAvailableError, UnsupportedFileTypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schema/{db_name}", response_model=DatabaseSchema)
async def get_database_schema(db_name: str):
    """Get database schema by database name"""
    try:
        return DatabaseManager.get_database_schema(db_name)
    except DatabaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schema-json/{db_name}")
async def get_schema_json(db_name: str):
    """Get schema.json file content for a specific database"""
    try:
        schema_data = DatabaseManager.get_schema_json(db_name)
        return JSONResponse(content=schema_data)
    except SchemaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/schema-json/{db_name}")
async def update_schema_json(db_name: str, request: SchemaUpdateRequest):
    """Update schema.json file for a specific database and retrain agent"""
    try:
        from ...services.agent_service import clear_agent_cache
        
        result = DatabaseManager.update_schema_json(db_name, request.schema_data)
        
        # Clear agent cache to force retraining on next request
        clear_agent_cache()
        
        return JSONResponse(content=result)
    except DatabaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_databases():
    """List all available databases"""
    try:
        databases = DatabaseManager.list_databases()
        return JSONResponse(content=[db.dict() for db in databases])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))