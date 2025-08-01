"""
日志系统使用示例
"""
from .logging import get_logger

# 获取当前文件的logger（自动使用文件名作为logger名称）
logger = get_logger()

def example_function():
    """示例函数，展示如何使用日志"""
    logger.info("这是一条信息日志")
    logger.debug("这是一条调试日志")
    logger.warning("这是一条警告日志")
    
    try:
        # 模拟一些操作
        result = 10 / 2
        logger.info(f"计算结果: {result}")
    except Exception as e:
        logger.error(f"计算失败: {str(e)}")
        raise

def example_with_custom_logger():
    """使用自定义名称的logger"""
    custom_logger = get_logger("custom_module")
    custom_logger.info("这是来自自定义模块的日志")

if __name__ == "__main__":
    # 运行示例
    logger.info("开始执行日志示例")
    example_function()
    example_with_custom_logger()
    logger.info("日志示例执行完成")
