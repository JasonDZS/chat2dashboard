import sqlite3
import json
import datetime
from typing import Optional, Dict, Any
from pathlib import Path

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