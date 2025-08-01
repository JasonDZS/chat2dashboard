import uvicorn
from app.main import app
from app.config import settings
from app.core.logging import get_logger

# 获取主启动脚本的logger
logger = get_logger()

if __name__ == "__main__":
    logger.info("🚀 Start Chat2Dashboard Backend Service")
    logger.info(f"Server: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    
    try:
        uvicorn.run(
            app, 
            host=settings.HOST, 
            port=settings.PORT, 
            log_level=settings.LOG_LEVEL
        )
    except Exception as e:
        logger.error(f"Start server failed: {str(e)}")
        raise