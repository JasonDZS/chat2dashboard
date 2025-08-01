from ..core.sql_generator import create_sql_generator
from ..core.logging import get_logger

logger = get_logger()

class SQLService:
    def create_sql_generator(self, db_name: str):
        """Create SQL generator for a database"""
        logger.info(f"创建SQL生成器: {db_name}")
        try:
            generator = create_sql_generator(db_name)
            logger.debug(f"SQL生成器创建成功: {db_name}")
            return generator
        except Exception as e:
            logger.error(f"创建SQL生成器失败: {db_name}, 错误: {str(e)}")
            raise