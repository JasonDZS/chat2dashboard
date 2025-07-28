from fastapi import APIRouter

from .database import router as database_router
from .visualization import router as visualization_router
from .schema import router as schema_router
from .logs import router as logs_router
from .system import router as system_router
from .knowledge_base import router as knowledge_base_router
from .document import router as document_router
from .search import router as search_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(database_router)
api_router.include_router(visualization_router)
api_router.include_router(schema_router)
api_router.include_router(logs_router)
api_router.include_router(system_router)
api_router.include_router(knowledge_base_router)
api_router.include_router(document_router)
api_router.include_router(search_router)