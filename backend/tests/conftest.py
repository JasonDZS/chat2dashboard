"""
pytest配置文件和测试fixtures
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import requests
import tempfile
import os
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch

from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """创建一个session级别的事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """同步测试客户端 - 使用真实HTTP请求"""
    import requests
    
    class HttpTestClient:
        def __init__(self, base_url="http://0.0.0.0:8000"):
            self.base_url = base_url
            
        def post(self, path: str, files=None, data=None, json=None):
            """发送真实的HTTP POST请求"""
            url = self.base_url + path
            
            if files:
                # 处理文件上传 - 使用列表格式处理多文件
                files_list = []
                for field_name, file_data in files:
                    filename, file_content, content_type = file_data
                    if hasattr(file_content, 'getvalue'):
                        content = file_content.getvalue()
                    else:
                        content = file_content
                    
                    # 每个文件作为独立的元组添加到列表中
                    files_list.append((field_name, (filename, content, content_type)))
                
                response = requests.post(url, files=files_list, data=data)
            elif json:
                response = requests.post(url, json=json)
            else:
                response = requests.post(url, data=data)
            
            return response
            
        def get(self, path: str, params=None):
            """发送真实的HTTP GET请求"""
            url = self.base_url + path
            return requests.get(url, params=params)
            
        def put(self, path: str, json=None, data=None):
            """发送真实的HTTP PUT请求"""
            url = self.base_url + path
            if json:
                return requests.put(url, json=json)
            else:
                return requests.put(url, data=data)
                
        def delete(self, path: str):
            """发送真实的HTTP DELETE请求"""
            url = self.base_url + path
            return requests.delete(url)
    
    return HttpTestClient()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端 - 使用真实HTTP请求"""
    async with AsyncClient(base_url="http://0.0.0.0:8000") as test_client:
        yield test_client


@pytest.fixture
def temp_dir():
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_database_manager():
    """模拟数据库管理器"""
    with patch('app.core.database.DatabaseManager') as mock:
        mock.create_database_from_files.return_value = (["test_table"], "/tmp/test.db")
        mock.get_database_schema.return_value = {
            "database_name": "test_db",
            "tables": [
                {
                    "name": "test_table",
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "name", "type": "TEXT"}
                    ]
                }
            ]
        }
        mock.list_databases.return_value = [
            {
                "name": "test_db",
                "path": "/tmp/test.db",
                "created_at": "2024-01-01T00:00:00"
            }
        ]
        yield mock


@pytest.fixture
def mock_knowledge_base():
    """模拟知识库"""
    return {
        "id": "test-kb-id",
        "name": "测试知识库",
        "description": "测试用知识库",
        "datasource_id": "test-datasource",
        "status": "ready",
        "config": {
            "enable_kg": True,
            "enable_vector": True,
            "chunk_size": 512
        },
        "metrics": {
            "entities_count": 100,
            "relations_count": 50,
            "documents_count": 10
        }
    }


@pytest.fixture
def mock_document():
    """模拟文档"""
    return {
        "id": "test-doc-id",
        "filename": "test.pdf",
        "file_type": "pdf",
        "file_size": 1024000,
        "status": "processed",
        "metadata": {
            "title": "测试文档",
            "author": "测试作者",
            "page_count": 10
        }
    }


@pytest.fixture
def mock_search_results():
    """模拟搜索结果"""
    return [
        {
            "id": "result-1",
            "content": "搜索结果内容1",
            "title": "结果标题1",
            "source": "document",
            "score": 0.95,
            "metadata": {"type": "text"},
            "snippet": "搜索结果摘要1"
        },
        {
            "id": "result-2", 
            "content": "搜索结果内容2",
            "title": "结果标题2",
            "source": "database",
            "score": 0.88,
            "metadata": {"type": "table"},
            "snippet": "搜索结果摘要2"
        }
    ]


@pytest.fixture
def sample_upload_file():
    """样本上传文件"""
    import io
    file_content = b"sample file content"
    return ("test.csv", io.BytesIO(file_content), "text/csv")


@pytest.fixture
def sample_pdf_file():
    """样本PDF文件"""
    import io
    # 模拟PDF文件内容
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    return ("test.pdf", io.BytesIO(pdf_content), "application/pdf")


@pytest.fixture(autouse=True)
def mock_settings():
    """模拟配置设置"""
    with patch.object(settings, 'DATABASES_DIR', '/tmp/test_databases'):
        with patch.object(settings, 'CORS_ORIGINS', ['*']):
            yield settings


@pytest.fixture
def mock_background_tasks():
    """模拟后台任务"""
    mock_tasks = Mock()
    mock_tasks.add_task = Mock()
    return mock_tasks


class MockAsyncContextManager:
    """模拟异步上下文管理器"""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_file_operations():
    """模拟文件操作"""
    with patch('builtins.open', create=True) as mock_open:
        with patch('os.makedirs') as mock_makedirs:
            with patch('os.path.exists', return_value=True) as mock_exists:
                yield {
                    'open': mock_open,
                    'makedirs': mock_makedirs,
                    'exists': mock_exists
                }


# 测试数据类
class TestData:
    """测试数据常量"""
    
    VALID_KB_CREATE_REQUEST = {
        "name": "测试知识库",
        "description": "这是一个测试知识库",
        "datasource_id": "test-datasource-id",
        "config": {
            "enable_kg": True,
            "enable_vector": True,
            "chunk_size": 512,
            "embedding_model": "sentence-bert"
        }
    }
    
    VALID_SEARCH_REQUEST = {
        "query": "测试查询",
        "search_type": "hybrid",
        "top_k": 10,
        "threshold": 0.5
    }
    
    VALID_DOCUMENT_PROCESS_REQUEST = {
        "config": {
            "extract_tables": True,
            "extract_images": True,
            "chunk_size": 512,
            "chunk_overlap": 50
        }
    }
    
    SAMPLE_DATABASE_SCHEMA = {
        "database_name": "test_db",
        "tables": [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True},
                    {"name": "name", "type": "TEXT", "nullable": False},
                    {"name": "email", "type": "TEXT", "nullable": True}
                ]
            },
            {
                "name": "orders",
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True},
                    {"name": "user_id", "type": "INTEGER", "foreign_key": "users.id"},
                    {"name": "amount", "type": "REAL", "nullable": False}
                ]
            }
        ]
    }


@pytest.fixture
def test_data():
    """提供测试数据"""
    return TestData


@pytest.fixture(scope="session", autouse=True)
def check_backend_service():
    """检查后端服务是否可用"""
    import time
    import requests
    
    max_retries = 10
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.get("http://0.0.0.0:8000/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ 后端服务已启动 (http://0.0.0.0:8000)")
                return
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"等待后端服务启动... ({i+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                raise Exception(
                    "后端服务未启动或不可访问。请确保运行: python main.py"
                )