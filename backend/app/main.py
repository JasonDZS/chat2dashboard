from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .config import settings, init_logging
from .api.v1.routes import api_router

# 初始化日志配置
init_logging()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Include API routes
app.include_router(api_router)

# Templates
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

# Legacy routes for backward compatibility
@app.post("/generate", response_class=HTMLResponse)
async def generate_visualization_legacy(
    request: Request, 
    query: str = Form(...), 
    db_name: str = Form(...),
    chart_type: str = Form(default=None)
):
    """Legacy route - redirects to new API"""
    from .api.v1.visualization import generate_visualization
    return await generate_visualization(request, query, db_name, chart_type)

@app.post("/upload-files")
async def upload_data_files_legacy(
    files: List[UploadFile] = File(...),
    db_name: str = Form(...)
):
    """Legacy route - redirects to new API"""
    from .api.v1.database import upload_data_files
    return await upload_data_files(files, db_name)

@app.get("/health")
async def health_check_legacy():
    """Legacy route - redirects to new API"""
    from .api.v1.system import health_check
    return await health_check()

@app.get("/schema/{db_name}")
async def get_database_schema_legacy(db_name: str):
    """Legacy route - redirects to new API"""
    from .api.v1.database import get_database_schema
    return await get_database_schema(db_name)

@app.get("/schema-json/{db_name}")
async def get_schema_json_legacy(db_name: str):
    """Legacy route - redirects to new API"""
    from .api.v1.database import get_schema_json
    return await get_schema_json(db_name)

@app.put("/schema-json/{db_name}")
async def update_schema_json_legacy(db_name: str, schema_data: dict):
    """Legacy route - redirects to new API"""
    from .api.v1.database import update_schema_json
    from .models.requests import SchemaUpdateRequest
    return await update_schema_json(db_name, SchemaUpdateRequest(schema_data=schema_data))

@app.post("/schema-json/{db_name}/sql")
async def add_sql_training_data_legacy(db_name: str, training_data: dict):
    """Legacy route - redirects to new API"""
    from .api.v1.schema import add_sql_training_data
    from .models.requests import SQLTrainingRequest
    return await add_sql_training_data(
        db_name, 
        SQLTrainingRequest(
            question=training_data.get("question", ""),
            sql=training_data.get("sql", "")
        )
    )

@app.delete("/schema-json/{db_name}/sql/{index}")
async def delete_sql_training_data_legacy(db_name: str, index: int):
    """Legacy route - redirects to new API"""
    from .api.v1.schema import delete_sql_training_data
    return await delete_sql_training_data(db_name, index)

@app.get("/databases")
async def list_databases_legacy():
    """Legacy route - redirects to new API"""
    from .api.v1.database import list_databases
    return await list_databases()

@app.get("/logs/requests")
async def get_request_logs_legacy(limit: int = 100, offset: int = 0):
    """Legacy route - redirects to new API"""
    from .api.v1.logs import get_request_logs
    return await get_request_logs(limit, offset)

@app.get("/logs/requests/{request_id}")
async def get_request_log_legacy(request_id: int):
    """Legacy route - redirects to new API"""
    from .api.v1.logs import get_request_log
    return await get_request_log(request_id)

@app.get("/logs/stats")
async def get_logs_stats_legacy():
    """Legacy route - redirects to new API"""
    from .api.v1.logs import get_logs_stats
    return await get_logs_stats()

@app.get("/status")
async def system_status_legacy():
    """Legacy route - redirects to new API"""
    from .api.v1.system import system_status
    return await system_status()

@app.post("/generate-sql/{db_name}")
async def generate_sql_training_data_legacy(db_name: str, num_questions: int = 10):
    """Legacy route - redirects to new API"""
    from .api.v1.schema import generate_sql_training_data
    from .models.requests import GenerateSQLRequest
    return await generate_sql_training_data(db_name, GenerateSQLRequest(num_questions=num_questions))