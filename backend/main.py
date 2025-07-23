from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psutil
import datetime
import sqlite3
import os
import json
from typing import List
from src.dbagent.agents.base import get_dbagent
from src.dbagent.html_generator.generator import HTMLGenerator
from src.utils import infer_chart_type_from_query

try:
    import pandas as pd
    import openpyxl
    XLSX_SUPPORT = True
except ImportError as e:
    XLSX_SUPPORT = False
    IMPORT_ERROR = str(e)

app = FastAPI(title="Data Visualization Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

def create_database_from_xlsx(files: List[UploadFile], db_name: str):
    """Create SQLite database from xlsx files"""
    if not XLSX_SUPPORT:
        raise ImportError(f"Excel support not available: {IMPORT_ERROR}")
    
    # Create database folder structure
    db_folder = f"databases/{db_name}"
    os.makedirs(db_folder, exist_ok=True)
    
    db_path = f"{db_folder}/{db_name}.db"
    
    conn = sqlite3.connect(db_path)
    created_tables = []
    table_creation_sql = {}
    
    try:
        for file in files:
            # Read xlsx file
            df = pd.read_excel(file.file)
            
            # Generate table name from filename
            table_name = os.path.splitext(file.filename)[0].replace(" ", "_").replace("-", "_")
            
            # Generate CREATE TABLE SQL statement
            columns_sql = []
            for col in df.columns:
                # Determine column type based on data
                sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if pd.api.types.is_numeric_dtype(df[col]):
                    if pd.api.types.is_integer_dtype(df[col]):
                        col_type = "INTEGER"
                    else:
                        col_type = "REAL"
                else:
                    col_type = "TEXT"
                columns_sql.append(f"    `{col}` {col_type}")
            
            create_sql = f"CREATE TABLE `{table_name}` (\n" + ",\n".join(columns_sql) + "\n);"
            table_creation_sql[table_name] = create_sql
            
            # Create table in database
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            created_tables.append({
                "table_name": table_name,
                "filename": file.filename,
                "rows": len(df),
                "columns": list(df.columns)
            })
    
    except Exception as e:
        conn.close()
        raise e
    
    conn.close()
    
    # Create JSON file with table creation statements
    schema_file = f"{db_folder}/schema.json"
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump({
            "database_name": db_name,
            "tables": table_creation_sql,
            "created_at": datetime.datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    return created_tables, db_path

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate_visualization(
    request: Request, 
    query: str = Form(...), 
    db_name: str = Form(...),
    chart_type: str = Form(default=None)
):
    try:
        # Get database agent instance
        agent = get_dbagent(db_name)
        
        # 如果没有指定图表类型，从问题中推断
        if chart_type is None:
            chart_type = infer_chart_type_from_query(query)
        
        # Convert query result to ProcessedData format
        processed_data = agent.to_processed_data(query, chart_type)
        
        # Generate HTML using the new HTMLGenerator
        generator = HTMLGenerator()
        response = generator.generate_html_page(processed_data)
        
        return HTMLResponse(content=response.html_content)
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", status_code=500)

@app.post("/upload-xlsx")
async def upload_xlsx_files(
    files: List[UploadFile] = File(...),
    db_name: str = Form(...)
):
    """Upload xlsx files and create database"""
    try:
        # Check if xlsx support is available
        if not XLSX_SUPPORT:
            return JSONResponse(
                content={"error": f"Excel support not available: {IMPORT_ERROR}"},
                status_code=500
            )
        
        # Validate file types
        for file in files:
            if not file.filename.endswith('.xlsx'):
                return JSONResponse(
                    content={"error": f"File {file.filename} is not an xlsx file"},
                    status_code=400
                )
        
        # Create database from xlsx files
        created_tables, db_path = create_database_from_xlsx(files, db_name)
        
        return JSONResponse(content={
            "message": "Database created successfully",
            "database_name": db_name,
            "database_path": db_path,
            "tables": created_tables,
            "total_files": len(files)
        })
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/health")
async def health_check():
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "Data Visualization Agent"
    })

@app.get("/schema/{db_name}")
async def get_database_schema(db_name: str):
    """Get database schema by database name"""
    try:
        db_path = f"databases/{db_name}/{db_name}.db"
        
        # Check if database exists
        if not os.path.exists(db_path):
            return JSONResponse(
                content={"error": f"Database '{db_name}' not found"},
                status_code=404
            )
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema = {
            "database_name": db_name,
            "database_path": db_path,
            "tables": []
        }
        
        # Get schema for each table
        for table in tables:
            table_name = table[0]
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            table_schema = {
                "table_name": table_name,
                "row_count": row_count,
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
            }
            
            schema["tables"].append(table_schema)
        
        conn.close()
        
        return JSONResponse(content=schema)
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/schema-json/{db_name}")
async def get_schema_json(db_name: str):
    """Get schema.json file content for a specific database"""
    try:
        schema_path = f"databases/{db_name}/schema.json"
        
        # Check if schema file exists
        if not os.path.exists(schema_path):
            return JSONResponse(
                content={"error": f"Schema file for database '{db_name}' not found"},
                status_code=404
            )
        
        # Read and return schema.json content
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        return JSONResponse(content=schema_data)
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.put("/schema-json/{db_name}")
async def update_schema_json(db_name: str, schema_data: dict):
    """Update schema.json file for a specific database and retrain agent"""
    try:
        db_folder = f"databases/{db_name}"
        schema_path = f"{db_folder}/schema.json"
        
        # Check if database folder exists
        if not os.path.exists(db_folder):
            return JSONResponse(
                content={"error": f"Database folder '{db_name}' not found"},
                status_code=404
            )
        
        # Update timestamp
        schema_data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Write updated schema.json
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        # Clear agent cache to force retraining on next request
        get_dbagent.cache_clear()
        
        return JSONResponse(content={
            "message": "Schema updated successfully and agent cache cleared",
            "database_name": db_name,
            "updated_at": schema_data["updated_at"]
        })
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/schema-json/{db_name}/sql")
async def add_sql_training_data(db_name: str, training_data: dict):
    """Add SQL training data to schema.json and retrain agent"""
    try:
        db_folder = f"databases/{db_name}"
        schema_path = f"{db_folder}/schema.json"
        
        # Check if database folder exists
        if not os.path.exists(db_folder):
            return JSONResponse(
                content={"error": f"Database folder '{db_name}' not found"},
                status_code=404
            )
        
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
            "question": training_data.get("question", ""),
            "sql": training_data.get("sql", ""),
            "added_at": datetime.datetime.now().isoformat()
        }
        
        schema_data["sql"].append(new_sql_item)
        schema_data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Write updated schema.json
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        # Clear agent cache to force retraining on next request
        get_dbagent.cache_clear()
        
        return JSONResponse(content={
            "message": "SQL training data added successfully and agent cache cleared",
            "database_name": db_name,
            "added_item": new_sql_item,
            "total_sql_items": len(schema_data["sql"])
        })
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.delete("/schema-json/{db_name}/sql/{index}")
async def delete_sql_training_data(db_name: str, index: int):
    """Delete SQL training data from schema.json by index and retrain agent"""
    try:
        db_folder = f"databases/{db_name}"
        schema_path = f"{db_folder}/schema.json"
        
        # Check if schema file exists
        if not os.path.exists(schema_path):
            return JSONResponse(
                content={"error": f"Schema file for database '{db_name}' not found"},
                status_code=404
            )
        
        # Read existing schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # Check if sql array exists and index is valid
        if "sql" not in schema_data or not isinstance(schema_data["sql"], list):
            return JSONResponse(
                content={"error": "No SQL training data found"},
                status_code=404
            )
        
        if index < 0 or index >= len(schema_data["sql"]):
            return JSONResponse(
                content={"error": f"Invalid index {index}. Valid range: 0-{len(schema_data['sql'])-1}"},
                status_code=400
            )
        
        # Remove item at index
        deleted_item = schema_data["sql"].pop(index)
        schema_data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Write updated schema.json
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        # Clear agent cache to force retraining on next request
        get_dbagent.cache_clear()
        
        return JSONResponse(content={
            "message": "SQL training data deleted successfully and agent cache cleared",
            "database_name": db_name,
            "deleted_item": deleted_item,
            "remaining_sql_items": len(schema_data["sql"])
        })
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/databases")
async def list_databases():
    """List all available databases"""
    try:
        databases_dir = "databases"
        
        if not os.path.exists(databases_dir):
            return JSONResponse(content=[])
        
        databases = []
        for item in os.listdir(databases_dir):
            db_path = os.path.join(databases_dir, item)
            if os.path.isdir(db_path):
                db_file = os.path.join(db_path, f"{item}.db")
                schema_file = os.path.join(db_path, "schema.json")
                
                if os.path.exists(db_file):
                    database_info = {
                        "name": item,
                        "path": db_file,
                        "has_schema": os.path.exists(schema_file)
                    }
                    
                    # Try to get additional info from schema.json
                    if os.path.exists(schema_file):
                        try:
                            with open(schema_file, 'r', encoding='utf-8') as f:
                                schema_data = json.load(f)
                                database_info["created_at"] = schema_data.get("created_at")
                                database_info["table_count"] = len(schema_data.get("tables", {}))
                        except Exception:
                            pass
                    
                    databases.append(database_info)
        
        return JSONResponse(content=databases)
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/status")
async def system_status():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "Data Visualization Agent",
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)