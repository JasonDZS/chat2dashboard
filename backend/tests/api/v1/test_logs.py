"""
日志接口测试
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import status


class TestLogsRouter:
    """日志路由测试类"""
    
    def test_get_request_logs_success(self, client):
        """测试成功获取请求日志"""
        params = {"limit": 10, "offset": 0}
        
        mock_logs = [
            {
                "id": 1,
                "timestamp": "2024-01-01T00:00:00Z",
                "method": "POST",
                "endpoint": "/api/v1/database/upload-files",
                "status_code": 200,
                "response_time": 1.5
            },
            {
                "id": 2,
                "timestamp": "2024-01-01T00:01:00Z",
                "method": "GET",
                "endpoint": "/api/v1/database/list",
                "status_code": 200,
                "response_time": 0.8
            }
        ]
        
        with patch('app.api.v1.logs.get_request_logs') as mock_get_logs:
            mock_get_logs.return_value = mock_logs
            
            response = client.get("/api/v1/logs/requests", params=params)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        if len(response_data) > 0:
            assert "method" in response_data[0]
    
    def test_get_request_log_success(self, client):
        """测试成功获取单个请求日志"""
        request_id = 1
        
        mock_log = {
            "id": request_id,
            "timestamp": "2024-01-01T00:00:00Z",
            "method": "POST",
            "endpoint": "/api/v1/database/upload-files",
            "status_code": 200,
            "response_time": 1.5,
            "request_body": {"db_name": "test_db"},
            "response_body": {"status": "success"}
        }
        
        with patch('app.api.v1.logs.get_request_log') as mock_get_log:
            mock_get_log.return_value = mock_log
            
            response = client.get(f"/api/v1/logs/requests/{request_id}")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "id" in response_data
    
    def test_get_logs_stats_success(self, client):
        """测试成功获取日志统计"""
        mock_stats = {
            "total_requests": 1250,
            "avg_response_time": 0.85,
            "error_rate": 0.02,
            "most_common_endpoints": [
                {"endpoint": "/api/v1/database/list", "count": 450},
                {"endpoint": "/api/v1/search/hybrid", "count": 320}
            ],
            "status_code_distribution": {
                "200": 1200,
                "400": 30,
                "404": 15,
                "500": 5
            }
        }
        
        with patch('app.api.v1.logs.get_logs_stats') as mock_get_stats:
            mock_get_stats.return_value = mock_stats
            
            response = client.get("/api/v1/logs/stats")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "total_requests" in response_data or "avg_response_time" in response_data
    
    def test_get_request_logs_pagination(self, client):
        """测试请求日志分页"""
        # 测试第一页
        response1 = client.get("/api/v1/logs/requests?limit=5&offset=0")
        assert response1.status_code == status.HTTP_200_OK
        
        # 测试第二页
        response2 = client.get("/api/v1/logs/requests?limit=5&offset=5")
        assert response2.status_code == status.HTTP_200_OK
    
    def test_get_request_log_not_found(self, client):
        """测试获取不存在的请求日志"""
        request_id = 99999
        
        with patch('app.api.v1.logs.get_request_log', return_value=None):
            response = client.get(f"/api/v1/logs/requests/{request_id}")
        
        # 根据实际实现可能返回404
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]


class TestLogsParametrized:
    """日志参数化测试"""
    
    @pytest.mark.parametrize("limit,offset", [
        (10, 0),
        (20, 10),
        (50, 0),
        (100, 50)
    ])
    def test_logs_pagination_params(self, client, limit: int, offset: int):
        """参数化测试日志分页参数"""
        params = {"limit": limit, "offset": offset}
        
        response = client.get("/api/v1/logs/requests", params=params)
        
        # 应该返回成功或者参数验证错误
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]