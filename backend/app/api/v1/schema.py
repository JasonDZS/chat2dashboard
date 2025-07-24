import datetime
import json
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...config import settings
from ...core.exceptions import DatabaseNotFoundError, SchemaNotFoundError, InvalidIndexError, NoSQLTrainingDataError
from ...models.requests import SQLTrainingRequest, GenerateSQLRequest
from ...services.sql_service import SQLService

router = APIRouter(prefix="/schema", tags=["schema"])

@router.post("/{db_name}/sql")
async def add_sql_training_data(db_name: str, request: SQLTrainingRequest):
    """Add SQL training data to schema.json and retrain agent"""
    try:
        db_folder = os.path.join(settings.DATABASES_DIR, db_name)
        schema_path = os.path.join(db_folder, "schema.json")
        
        if not os.path.exists(db_folder):
            raise DatabaseNotFoundError(db_name)
        
        # Read existing schema
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
        else:
            schema_data = {
                "database_name": db_name,
                "tables": {},
                "sql": [],
                "created_at": datetime.datetime.now().isoformat()
            }
        
        # Add SQL training data
        if "sql" not in schema_data:
            schema_data["sql"] = []
        
        new_sql_item = {
            "question": request.question,
            "sql": request.sql,
            "added_at": datetime.datetime.now().isoformat()
        }
        
        schema_data["sql"].append(new_sql_item)
        schema_data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Write updated schema.json
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        # Clear agent cache to force retraining on next request
        from ...services.agent_service import clear_agent_cache
        clear_agent_cache()
        
        return JSONResponse(content={
            "message": "SQL training data added successfully and agent cache cleared",
            "database_name": db_name,
            "added_item": new_sql_item,
            "total_sql_items": len(schema_data["sql"])
        })
    
    except DatabaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{db_name}/sql/{index}")
async def delete_sql_training_data(db_name: str, index: int):
    """Delete SQL training data from schema.json by index and retrain agent"""
    try:
        db_folder = os.path.join(settings.DATABASES_DIR, db_name)
        schema_path = os.path.join(db_folder, "schema.json")
        
        if not os.path.exists(schema_path):
            raise SchemaNotFoundError(db_name)
        
        # Read existing schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # Check if sql array exists and index is valid
        if "sql" not in schema_data or not isinstance(schema_data["sql"], list):
            raise NoSQLTrainingDataError()
        
        if index < 0 or index >= len(schema_data["sql"]):
            raise InvalidIndexError(index, len(schema_data['sql'])-1)
        
        # Remove item at index
        deleted_item = schema_data["sql"].pop(index)
        schema_data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Write updated schema.json
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        # Clear agent cache to force retraining on next request
        from ...services.agent_service import clear_agent_cache
        clear_agent_cache()
        
        return JSONResponse(content={
            "message": "SQL training data deleted successfully and agent cache cleared",
            "database_name": db_name,
            "deleted_item": deleted_item,
            "remaining_sql_items": len(schema_data["sql"])
        })
    
    except (SchemaNotFoundError, NoSQLTrainingDataError, InvalidIndexError) as e:
        raise HTTPException(status_code=404 if isinstance(e, SchemaNotFoundError) else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{db_name}/generate-sql")
async def generate_sql_training_data(db_name: str, request: GenerateSQLRequest):
    """Generate SQL training data using AI and add to schema.json"""
    try:
        sql_service = SQLService()
        generator = sql_service.create_sql_generator(db_name)
        
        # Show current status
        current_count = generator.get_stored_sql_count()
        
        # Generate and validate SQL
        validated_records = generator.batch_generate_and_validate(request.num_questions)
        
        # Get final count
        final_count = generator.get_stored_sql_count()
        
        return JSONResponse(content={
            "message": f"Successfully generated and validated {len(validated_records)} SQL records",
            "database_name": db_name,
            "requested_questions": request.num_questions,
            "validated_records": len(validated_records),
            "previous_sql_count": current_count,
            "final_sql_count": final_count,
            "added_sql": validated_records
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))