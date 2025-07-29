import uvicorn
from app.main import app
from app.config import settings
from app.core.logging import get_logger

# 获取主启动脚本的logger
logger = get_logger()

if __name__ == "__main__":
    logger.info("🚀 启动Chat2Dashboard后端服务")
    logger.info(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    
    try:
        uvicorn.run(
            app, 
            host=settings.HOST, 
            port=settings.PORT, 
            log_level=settings.LOG_LEVEL
        )
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        raise