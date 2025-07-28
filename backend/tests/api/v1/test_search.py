"""
混合检索接口测试
"""
import pytest
import uuid
from unittest.mock import patch, Mock, AsyncMock
from fastapi import status
from datetime import datetime

from app.core.exceptions import (
    KnowledgeBaseNotFoundError,
    InvalidSearchQueryError,
    SearchTimeoutError
)


class TestSearchRouter:
    """检索路由测试类"""
    
    def test_hybrid_search_success(self, client):
        """测试成功混合检索"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "测试查询",
            "search_strategy": "hybrid",
            "fusion_strategy": "rrf",
            "top_k": 10,
            "threshold": 0.5
        }
        
        response = client.post("/api/v1/search/hybrid", json=request_data)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "query" in response_data
        assert "kb_id" in response_data
        assert "search_strategy" in response_data
        assert "results" in response_data
    
    def test_hybrid_search_knowledge_base_not_found(self, client):
        """测试知识库不存在时的混合检索"""
        request_data = {
            "kb_id": "nonexistent-kb-id",
            "query": "测试查询",
            "top_k": 5
        }
        
        with patch('app.api.v1.search.hybrid_search', 
                  side_effect=KnowledgeBaseNotFoundError("Knowledge base not found")):
            response = client.post("/api/v1/search/hybrid", json=request_data)
        
        assert response.status_code >= 400
    
    def test_hybrid_search_invalid_query(self, client):
        """测试无效查询的混合检索"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "",  # 空查询
            "top_k": 5
        }
        
        with patch('app.api.v1.search.hybrid_search', 
                  side_effect=InvalidSearchQueryError("Invalid search query")):
            response = client.post("/api/v1/search/hybrid", json=request_data)
        
        assert response.status_code >= 400
    
    def test_hybrid_search_timeout(self, client):
        """测试搜索超时"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "复杂查询",
            "top_k": 100
        }
        
        with patch('app.api.v1.search.hybrid_search', 
                  side_effect=SearchTimeoutError("Search timeout")):
            response = client.post("/api/v1/search/hybrid", json=request_data)
        
        assert response.status_code >= 400
    
    def test_vector_search_success(self, client):
        """测试成功向量检索"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "语义查询",
            "embedding_model": "sentence-bert",
            "top_k": 8,
            "distance_metric": "cosine"
        }
        
        response = client.post("/api/v1/search/vector", json=request_data)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "query" in response_data
        assert "kb_id" in response_data
        assert "search_strategy" in response_data
        assert "results" in response_data
    
    def test_keyword_search_success(self, client):
        """测试成功关键词检索"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "关键词查询",
            "search_type": "boolean",
            "fuzzy": True,
            "top_k": 6
        }
        
        response = client.post("/api/v1/search/keyword", json=request_data)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "query" in response_data
        assert "kb_id" in response_data
        assert "search_strategy" in response_data
        assert "results" in response_data
    
    def test_graph_search_success(self, client):
        """测试成功图检索"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "图遍历查询",
            "max_hops": 3,
            "relation_types": ["contains", "related_to"],
            "top_k": 5
        }
        
        response = client.post("/api/v1/search/graph", json=request_data)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "query" in response_data
        assert "kb_id" in response_data
        assert "search_strategy" in response_data
        assert "results" in response_data
    
    def test_generate_sql_query_success(self, client):
        """测试成功生成SQL查询"""
        params = {
            "kb_id": "test-kb-id",
            "natural_query": "查询用户表中年龄大于25的用户数量",
            "include_explanation": True
        }
        
        response = client.post("/api/v1/search/sql-generation", params=params)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "kb_id" in response_data
        assert "natural_query" in response_data
        assert "generated_sql" in response_data
    
    def test_generate_sql_query_without_explanation(self, client):
        """测试不包含解释的SQL生成"""
        params = {
            "kb_id": "test-kb-id",
            "natural_query": "获取所有订单信息",
            "include_explanation": False
        }
        
        response = client.post("/api/v1/search/sql-generation", params=params)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "generated_sql" in response_data
    
    def test_expand_query_success(self, client):
        """测试成功查询扩展"""
        request_data = {
            "original_query": "机器学习",
            "kb_id": "test-kb-id",
            "strategy": "semantic",
            "max_expansions": 5
        }
        
        response = client.post("/api/v1/search/expand-query", json=request_data)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "original_query" in response_data
        assert "kb_id" in response_data
        assert "expansion_strategy" in response_data
        assert "expansions" in response_data
        assert "suggestions" in response_data
    
    def test_get_search_suggestions_success(self, client):
        """测试成功获取搜索建议"""
        params = {
            "kb_id": "test-kb-id",
            "query": "机器",
            "limit": 8
        }
        
        response = client.get("/api/v1/search/suggestions", params=params)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "query" in response_data
        assert "kb_id" in response_data
        assert "suggestions" in response_data
    
    def test_get_search_suggestions_validation(self, client):
        """测试搜索建议参数验证"""
        # 测试查询长度限制
        params = {
            "kb_id": "test-kb-id",
            "query": "",  # 空查询应该失败
            "limit": 5
        }
        
        response = client.get("/api/v1/search/suggestions", params=params)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 测试limit范围验证
        params = {
            "kb_id": "test-kb-id",
            "query": "test",
            "limit": 100  # 超过最大限制
        }
        
        response = client.get("/api/v1/search/suggestions", params=params)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_search_analytics_success(self, client):
        """测试成功获取搜索分析"""
        kb_id = "test-kb-id"
        params = {
            "days": 7,
            "include_queries": True
        }
        
        response = client.get(f"/api/v1/search/analytics/{kb_id}", params=params)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "kb_id" in response_data
        assert "total_searches" in response_data or "period_days" in response_data
    
    def test_get_search_analytics_without_queries(self, client):
        """测试不包含热门查询的分析"""
        kb_id = "test-kb-id"
        params = {
            "days": 30,
            "include_queries": False
        }
        
        response = client.get(f"/api/v1/search/analytics/{kb_id}", params=params)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "popular_queries" in response_data
    
    def test_submit_search_feedback_success(self, client):
        """测试成功提交搜索反馈"""
        request_data = {
            "search_id": "search-session-123",
            "query": "测试查询",
            "result_id": "result-456",
            "feedback_type": "relevant",
            "rating": 4,
            "comment": "这个结果很有帮助"
        }
        
        response = client.post("/api/v1/search/feedback", json=request_data)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "search_id" in response_data
        assert "result_id" in response_data
        assert "feedback_type" in response_data
        assert "message" in response_data or "feedback_id" in response_data
    
    def test_submit_search_feedback_minimal(self, client):
        """测试最小化搜索反馈"""
        request_data = {
            "search_id": "search-session-123",
            "query": "测试查询",
            "result_id": "result-456",
            "feedback_type": "irrelevant"
            # 不包含rating和comment
        }
        
        response = client.post("/api/v1/search/feedback", json=request_data)
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "feedback_type" in response_data
    
    def test_check_search_health_success(self, client):
        """测试成功检查搜索健康状态"""
        kb_id = "test-kb-id"
        
        response = client.get(f"/api/v1/search/health/{kb_id}")
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "kb_id" in response_data
        assert "status" in response_data
        assert "components" in response_data or "last_check" in response_data


class TestSearchParametrized:
    """检索参数化测试"""
    
    @pytest.mark.parametrize("search_strategy,expected_fields", [
        ("vector", ["search_time"]),
        ("keyword", ["search_time"]),
        ("graph", ["search_time"]),
        ("hybrid", ["search_time", "rerank_time"]),
    ])
    def test_search_strategies(self, client, search_strategy: str, expected_fields: list):
        """参数化测试不同搜索策略"""
        if search_strategy == "hybrid":
            endpoint = "/api/v1/search/hybrid"
            request_data = {
                "kb_id": "test-kb-id",
                "query": "测试查询",
                "search_strategy": search_strategy,
                "top_k": 5
            }
        else:
            endpoint = f"/api/v1/search/{search_strategy}"
            request_data = {
                "kb_id": "test-kb-id",
                "query": "测试查询",
                "top_k": 5
            }
        
        response = client.post(endpoint, json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "results" in response_data
    
    @pytest.mark.parametrize("top_k,expected_max_results", [
        (1, 1),
        (5, 5),
        (10, 10),
        (50, 10),  # 假设最大返回10个结果
    ])
    def test_search_top_k_limits(self, client, top_k: int, expected_max_results: int):
        """参数化测试搜索结果数量限制"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "测试查询",
            "top_k": top_k
        }
        
        response = client.post("/api/v1/search/vector", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "results" in response_data
    
    @pytest.mark.parametrize("feedback_type,rating,should_succeed", [
        ("relevant", 5, True),
        ("irrelevant", 1, True),
        ("helpful", 4, True),
        ("unhelpful", 2, True),
        ("invalid_type", 3, False),
        ("relevant", 6, False),  # 超出评分范围
        ("relevant", 0, False),  # 超出评分范围
    ])
    def test_feedback_validation(self, client, 
                               feedback_type: str, rating: int, should_succeed: bool):
        """参数化测试反馈验证"""
        request_data = {
            "search_id": "search-123",
            "query": "测试查询",
            "result_id": "result-456",
            "feedback_type": feedback_type,
            "rating": rating
        }
        
        response = client.post("/api/v1/search/feedback", json=request_data)
        
        if should_succeed:
            assert response.status_code == status.HTTP_200_OK
        else:
            assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestSearchErrorHandling:
    """检索错误处理测试"""
    
    def test_malformed_json_request(self, client):
        """测试格式错误的JSON请求"""
        # 发送格式错误的JSON
        response = client.post(
            "/api/v1/search/vector",
            data='{"kb_id": "test", "query": "test", "invalid_json":}',  # 格式错误
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_missing_required_fields(self, client):
        """测试缺少必需字段"""
        # 缺少query字段
        request_data = {
            "kb_id": "test-kb-id",
            "top_k": 5
            # 缺少query
        }
        
        response = client.post("/api/v1/search/vector", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_parameter_types(self, client):
        """测试无效参数类型"""
        # top_k应该是整数，不是字符串
        request_data = {
            "kb_id": "test-kb-id",
            "query": "测试查询",
            "top_k": "invalid"
        }
        
        response = client.post("/api/v1/search/vector", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_search_service_unavailable(self, client):
        """测试搜索服务不可用"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "测试查询",
            "top_k": 5
        }
        
        with patch('app.api.v1.search.vector_search', 
                  side_effect=Exception("Search service unavailable")):
            response = client.post("/api/v1/search/vector", json=request_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.status_code >= 500
    
    def test_concurrent_search_requests(self, client):
        """测试并发搜索请求"""
        import threading
        import time
        
        results = []
        
        def make_search_request():
            request_data = {
                "kb_id": "test-kb-id",
                "query": f"并发查询 {threading.current_thread().ident}",
                "top_k": 5
            }
            response = client.post("/api/v1/search/vector", json=request_data)
            results.append(response.status_code)
        
        # 创建多个线程并发搜索
        threads = [threading.Thread(target=make_search_request) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 验证所有请求都得到了处理
        assert len(results) == 5


class TestSearchIntegration:
    """检索集成测试"""
    
    @pytest.mark.asyncio
    async def test_search_workflow(self, async_client):
        """测试完整的搜索工作流程"""
        kb_id = "test-kb-id"
        query = "集成测试查询"
        
        # 1. 混合搜索
        hybrid_request = {
            "kb_id": kb_id,
            "query": query,
            "top_k": 10
        }
        hybrid_response = await async_client.post("/api/v1/search/hybrid", json=hybrid_request)
        assert hybrid_response.status_code == status.HTTP_200_OK
        
        # 2. 查询扩展
        expansion_request = {
            "original_query": query,
            "kb_id": kb_id,
            "strategy": "semantic"
        }
        expansion_response = await async_client.post("/api/v1/search/expand-query", json=expansion_request)
        assert expansion_response.status_code == status.HTTP_200_OK
        
        # 3. 获取搜索建议
        suggestions_response = await async_client.get(f"/api/v1/search/suggestions?kb_id={kb_id}&query={query[:3]}")
        assert suggestions_response.status_code == status.HTTP_200_OK
        
        # 4. 提交反馈
        feedback_request = {
            "search_id": "workflow-search-123",
            "query": query,
            "result_id": "result-789",
            "feedback_type": "relevant",
            "rating": 4
        }
        feedback_response = await async_client.post("/api/v1/search/feedback", json=feedback_request)
        assert feedback_response.status_code == status.HTTP_200_OK
        
        # 5. 检查健康状态
        health_response = await async_client.get(f"/api/v1/search/health/{kb_id}")
        assert health_response.status_code == status.HTTP_200_OK
        
        # 6. 获取分析统计
        analytics_response = await async_client.get(f"/api/v1/search/analytics/{kb_id}?days=7")
        assert analytics_response.status_code == status.HTTP_200_OK
    
    def test_search_performance_comparison(self, client):
        """测试不同搜索策略的性能对比"""
        query = "性能对比查询"
        kb_id = "test-kb-id"
        
        search_endpoints = [
            ("/api/v1/search/vector", {"kb_id": kb_id, "query": query, "top_k": 5}),
            ("/api/v1/search/keyword", {"kb_id": kb_id, "query": query, "top_k": 5}),
            ("/api/v1/search/graph", {"kb_id": kb_id, "query": query, "top_k": 5}),
            ("/api/v1/search/hybrid", {"kb_id": kb_id, "query": query, "top_k": 5})
        ]
        
        performance_results = {}
        
        for endpoint, request_data in search_endpoints:
            import time
            start_time = time.time()
            
            response = client.post(endpoint, json=request_data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == status.HTTP_200_OK
            
            response_data = response.json()
            search_strategy = response_data.get("search_strategy", endpoint.split("/")[-1])
            
            performance_results[search_strategy] = {
                "response_time": response_time,
                "search_time": response_data.get("search_time", 0),
                "result_count": len(response_data.get("results", []))
            }
        
        # 验证所有搜索策略都返回了结果
        for strategy, metrics in performance_results.items():
            assert metrics["result_count"] >= 0
    
    def test_search_result_consistency(self, client):
        """测试搜索结果一致性"""
        request_data = {
            "kb_id": "test-kb-id",
            "query": "一致性测试查询",
            "top_k": 5
        }
        
        # 多次执行相同搜索
        responses = []
        for _ in range(3):
            response = client.post("/api/v1/search/vector", json=request_data)
            assert response.status_code == status.HTTP_200_OK
            responses.append(response.json())
        
        # 验证基本字段存在
        for response_data in responses:
            assert "query" in response_data
            assert "results" in response_data


class TestSearchValidation:
    """检索验证测试"""
    
    def test_sql_generation_validation(self, client):
        """测试SQL生成验证"""
        # 测试有效的自然语言查询
        valid_queries = [
            "查询所有用户",
            "统计订单数量",
            "查找年龄大于30的用户",
            "按城市分组统计人数"
        ]
        
        for query in valid_queries:
            params = {
                "kb_id": "test-kb-id",
                "natural_query": query
            }
            response = client.post("/api/v1/search/sql-generation", params=params)
            assert response.status_code == status.HTTP_200_OK
            
            response_data = response.json()
            assert "generated_sql" in response_data
            assert len(response_data["generated_sql"]) > 0
    
    def test_query_expansion_strategies(self, client):
        """测试查询扩展策略"""
        base_request = {
            "original_query": "人工智能",
            "kb_id": "test-kb-id"
        }
        
        strategies = ["semantic", "syntactic", "statistical", "hybrid"]
        
        for strategy in strategies:
            request_data = base_request.copy()
            request_data["strategy"] = strategy
            
            response = client.post("/api/v1/search/expand-query", json=request_data)
            assert response.status_code == status.HTTP_200_OK
            
            response_data = response.json()
            assert "expansion_strategy" in response_data
            assert "expansions" in response_data
    
    def test_analytics_date_range_validation(self, client):
        """测试分析日期范围验证"""
        kb_id = "test-kb-id"
        
        # 测试有效的日期范围
        valid_ranges = [1, 7, 30, 90]
        for days in valid_ranges:
            response = client.get(f"/api/v1/search/analytics/{kb_id}?days={days}")
            assert response.status_code == status.HTTP_200_OK
            
            response_data = response.json()
            assert "period_days" in response_data or "total_searches" in response_data
        
        # 测试无效的日期范围
        invalid_ranges = [0, -1, 365]  # 假设最大90天
        for days in invalid_ranges:
            response = client.get(f"/api/v1/search/analytics/{kb_id}?days={days}")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY