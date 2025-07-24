from typing import List, Dict, Any, Optional
from ..core.logging import RequestLogger

class LoggingService:
    def __init__(self):
        self.logger = RequestLogger()
    
    def log_request(
        self,
        query: str,
        db_name: str,
        chart_type: str,
        response_status: str,
        generated_sql: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time_ms: int = 0
    ):
        """Log a request"""
        self.logger.log_request(
            query=query,
            db_name=db_name,
            chart_type=chart_type,
            response_status=response_status,
            generated_sql=generated_sql,
            response_data=response_data,
            error_message=error_message,
            execution_time_ms=execution_time_ms
        )
    
    def get_requests(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get request logs with pagination"""
        return self.logger.get_requests(limit=limit, offset=offset)
    
    def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific request log by ID"""
        return self.logger.get_request_by_id(request_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return self.logger.get_stats()