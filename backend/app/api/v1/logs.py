from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...services.logging_service import LoggingService
from ...core.exceptions import RequestNotFoundError
from ...models.responses import LogsResponse

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/requests", response_model=LogsResponse)
async def get_request_logs(limit: int = 100, offset: int = 0):
    """Get paginated request logs"""
    try:
        logging_service = LoggingService()
        logs = logging_service.get_requests(limit=limit, offset=offset)
        return LogsResponse(
            logs=logs,
            limit=limit,
            offset=offset,
            count=len(logs)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/{request_id}")
async def get_request_log(request_id: int):
    """Get specific request log by ID"""
    try:
        logging_service = LoggingService()
        log = logging_service.get_request_by_id(request_id)
        if log:
            return JSONResponse(content=log)
        else:
            raise RequestNotFoundError(request_id)
    except RequestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_logs_stats():
    """Get logging statistics"""
    try:
        logging_service = LoggingService()
        stats = logging_service.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))