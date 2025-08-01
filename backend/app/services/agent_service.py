from functools import lru_cache
from ..core.agent import get_dbagent, DBAgent
from ..core.logging import get_logger

logger = get_logger()

class AgentService:
    def get_agent(self, db_name: str) -> DBAgent:
        """Get database agent instance"""
        logger.info(f"获取数据库代理实例: {db_name}")
        try:
            agent = get_dbagent(db_name)
            logger.debug(f"成功获取数据库代理: {db_name}")
            return agent
        except Exception as e:
            logger.error(f"获取数据库代理失败: {db_name}, 错误: {str(e)}")
            raise

def clear_agent_cache():
    """Clear the agent cache to force retraining"""
    logger.info("清理代理缓存")
    try:
        get_dbagent.cache_clear()
        logger.debug("代理缓存清理成功")
    except Exception as e:
        logger.error(f"清理代理缓存失败: {str(e)}")
        raise