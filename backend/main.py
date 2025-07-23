from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psutil
import datetime
import sqlite3
import os
from typing import List
from src.nlp_processor import process_natural_language
from src.html_generator import generate_html_page

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
    
    db_path = f"databases/{db_name}.db"
    os.makedirs("databases", exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    created_tables = []
    
    try:
        for file in files:
            # Read xlsx file
            df = pd.read_excel(file.file)
            
            # Generate table name from filename
            table_name = os.path.splitext(file.filename)[0].replace(" ", "_").replace("-", "_")
            
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
    return created_tables, db_path

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate_visualization(request: Request, query: str = Form(...)):
    try:
        processed_data = process_natural_language(query)
        html_content = generate_html_page(processed_data)
        return HTMLResponse(content=html_content)
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
        db_path = f"databases/{db_name}.db"
        
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