"""
可视化接口测试
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import status


class TestVisualizationRouter:
    """可视化路由测试类"""
    
    def test_generate_visualization_success(self, client):
        """测试成功生成可视化"""
        request_data = {
            "query": "显示用户年龄分布",
            "db_name": "test_db",
            "chart_type": "bar"
        }
        
        with patch('app.api.v1.visualization.generate_visualization') as mock_generate:
            mock_generate.return_value = {
                "chart_data": {"labels": ["20-30", "30-40", "40-50"], "values": [10, 15, 8]},
                "chart_type": "bar",
                "sql_query": "SELECT age_group, COUNT(*) FROM users GROUP BY age_group",
                "success": True
            }
            
            response = client.post("/api/v1/visualization/generate", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "success" in response_data or "chart_data" in response_data
    
    def test_generate_visualization_invalid_db(self, client):
        """测试无效数据库的可视化生成"""
        request_data = {
            "query": "显示数据",
            "db_name": "nonexistent_db",
            "chart_type": "line"
        }
        
        response = client.post("/api/v1/visualization/generate", json=request_data)
        
        # 根据实际实现可能返回400或404
        assert response.status_code >= 400


class TestVisualizationParametrized:
    """可视化参数化测试"""
    
    @pytest.mark.parametrize("chart_type", ["bar", "line", "pie", "scatter", "table"])
    def test_chart_types(self, client, chart_type: str):
        """参数化测试不同图表类型"""
        request_data = {
            "query": f"生成{chart_type}图表",
            "db_name": "test_db",
            "chart_type": chart_type
        }
        
        with patch('app.api.v1.visualization.generate_visualization') as mock_generate:
            mock_generate.return_value = {
                "chart_type": chart_type,
                "success": True
            }
            
            response = client.post("/api/v1/visualization/generate", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "chart_type" in response_data or "success" in response_data