import datetime
import psutil
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...models.responses import HealthResponse, StatusResponse, SystemStatus

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.datetime.now().isoformat(),
        service="Data Visualization Agent"
    )

@router.get("/status", response_model=StatusResponse)
async def system_status():
    """System status with resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = SystemStatus(
            cpu_percent=cpu_percent,
            memory={
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            disk={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        )
        
        return StatusResponse(
            status="healthy",
            timestamp=datetime.datetime.now().isoformat(),
            service="Data Visualization Agent",
            system=system_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))