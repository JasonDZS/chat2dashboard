import sqlite3
import json
import datetime
import logging
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path

class AppLogger:
    """
    通用应用日志类，支持显示调用脚本名称
    """
    _loggers = {}
    _configured = False
    
    @classmethod
    def configure(cls, log_level: str = "INFO", log_format: str = None):
        """配置全局日志设置"""
        if cls._configured:
            return
            
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        
        # 创建logs目录
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # 设置根logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # 清除已有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(logs_dir / "app.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str = None):
        """
        获取logger实例
        
        Args:
            name: logger名称，如果为None则自动获取调用者的文件名
        """
        if not cls._configured:
            cls.configure()
        
        if name is None:
            # 自动获取调用者的文件名
            frame = sys._getframe(1)
            filename = os.path.basename(frame.f_code.co_filename)
            name = os.path.splitext(filename)[0]
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]


# 便捷函数，直接获取当前文件的logger
def get_logger(name: str = None):
    """
    获取logger的便捷函数
    
    Usage:
        from app.core.logging import get_logger
        logger = get_logger()  # 自动使用当前文件名
        logger.info("这是一条日志")
        
        # 或者指定名称
        logger = get_logger("custom_name")
        logger.debug("调试信息")
    """
    if name is None:
        # 自动获取调用者的文件名
        frame = sys._getframe(1)
        filename = os.path.basename(frame.f_code.co_filename)
        name = os.path.splitext(filename)[0]
    
    return AppLogger.get_logger(name)


class RequestLogger:
    def __init__(self, db_path: str = "logs/requests.db"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generate_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                db_name TEXT NOT NULL,
                chart_type TEXT,
                response_status TEXT NOT NULL,
                generated_sql TEXT,
                response_data TEXT,
                error_message TEXT,
                execution_time_ms INTEGER,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_request(self, 
                   query: str, 
                   db_name: str, 
                   chart_type: Optional[str] = None,
                   response_status: str = "success",
                   generated_sql: Optional[str] = None,
                   response_data: Optional[Dict[str, Any]] = None,
                   error_message: Optional[str] = None,
                   execution_time_ms: Optional[int] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        response_data_json = json.dumps(response_data) if response_data else None
        
        cursor.execute('''
            INSERT INTO generate_requests 
            (timestamp, query, db_name, chart_type, response_status, 
             generated_sql, response_data, error_message, execution_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, query, db_name, chart_type, response_status,
              generated_sql, response_data_json, error_message, execution_time_ms, timestamp))
        
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return request_id
    
    def get_requests(self, limit: int = 100, offset: int = 0) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM generate_requests 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            record = dict(zip(columns, row))
            if record['response_data']:
                try:
                    record['response_data'] = json.loads(record['response_data'])
                except json.JSONDecodeError:
                    pass
            result.append(record)
        
        conn.close()
        return result
    
    def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM generate_requests WHERE id = ?', (request_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            record = dict(zip(columns, row))
            if record['response_data']:
                try:
                    record['response_data'] = json.loads(record['response_data'])
                except json.JSONDecodeError:
                    pass
            conn.close()
            return record
        
        conn.close()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM generate_requests')
        total_requests = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM generate_requests WHERE response_status = "success"')
        successful_requests = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM generate_requests WHERE response_status = "error"')
        failed_requests = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(execution_time_ms) FROM generate_requests WHERE execution_time_ms IS NOT NULL')
        avg_execution_time = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT db_name, COUNT(*) as count 
            FROM generate_requests 
            GROUP BY db_name 
            ORDER BY count DESC
        ''')
        db_usage = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "average_execution_time_ms": avg_execution_time,
            "database_usage": [{"db_name": row[0], "count": row[1]} for row in db_usage]
        }