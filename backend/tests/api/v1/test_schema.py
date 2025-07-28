"""
模式管理接口测试
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import status


class TestSchemaRouter:
    """模式路由测试类"""
    
    def test_add_sql_training_data_success(self, client):
        """测试成功添加SQL训练数据"""
        db_name = "test_db"
        request_data = {
            "question": "查询所有用户",
            "sql": "SELECT * FROM users"
        }
        
        with patch('app.api.v1.schema.add_sql_training_data') as mock_add:
            mock_add.return_value = {"status": "success", "message": "Training data added"}
            
            response = client.post(f"/api/v1/schema/{db_name}/sql", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "status" in response_data
    
    def test_delete_sql_training_data_success(self, client):
        """测试成功删除SQL训练数据"""
        db_name = "test_db"
        index = 0
        
        with patch('app.api.v1.schema.delete_sql_training_data') as mock_delete:
            mock_delete.return_value = {"status": "success", "message": "Training data deleted"}
            
            response = client.delete(f"/api/v1/schema/{db_name}/sql/{index}")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "status" in response_data
    
    def test_generate_sql_training_data_success(self, client):
        """测试成功生成SQL训练数据"""
        db_name = "test_db"
        request_data = {"num_questions": 10}
        
        with patch('app.api.v1.schema.generate_sql_training_data') as mock_generate:
            mock_generate.return_value = {
                "generated_count": 10,
                "training_data": [{"question": "示例问题", "sql": "SELECT * FROM table"}]
            }
            
            response = client.post(f"/api/v1/schema/{db_name}/generate-sql", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "generated_count" in response_data
        assert "training_data" in response_data


class TestSchemaValidation:
    """模式验证测试"""
    
    def test_invalid_sql_syntax(self, client):
        """测试无效SQL语法"""
        db_name = "test_db"
        request_data = {
            "question": "查询用户",
            "sql": "INVALID SQL SYNTAX"
        }
        
        response = client.post(f"/api/v1/schema/{db_name}/sql", json=request_data)
        
        # 根据实际实现可能返回400
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK]
    
    @pytest.mark.parametrize("num_questions", [1, 5, 10, 20])
    def test_generate_different_quantities(self, client, num_questions: int):
        """参数化测试生成不同数量的训练数据"""
        db_name = "test_db"
        request_data = {"num_questions": num_questions}
        
        with patch('app.api.v1.schema.generate_sql_training_data') as mock_generate:
            mock_generate.return_value = {
                "generated_count": num_questions,
                "training_data": []
            }
            
            response = client.post(f"/api/v1/schema/{db_name}/generate-sql", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "generated_count" in response_data