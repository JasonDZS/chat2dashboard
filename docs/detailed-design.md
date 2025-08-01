# Chat2Dashboard 详细设计文档

## 1. 系统架构设计

### 1.1 整体架构

Chat2Dashboard 采用分层架构设计，包含以下核心层次：

- **表示层 (Presentation Layer)**: Web前端界面和API接口
- **业务逻辑层 (Business Logic Layer)**: 知识库构建、数据处理、智能查询等核心业务
- **数据访问层 (Data Access Layer)**: 数据库操作、文件存储、向量数据库操作
- **基础设施层 (Infrastructure Layer)**: 配置管理、日志记录、安全认证

### 1.2 微服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端服务       │    │   API网关        │    │   认证服务       │
│   (Vue.js)      │    │   (FastAPI)     │    │   (OAuth2)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                                 │                                 │
│ ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│ │   数据源服务     │    │   知识库服务     │    │   查询服务       │ │
│ │   (数据导入)     │    │   (向量化)      │    │   (智能查询)     │ │
│ └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                 │                                 │
└─────────────────────────────────┼─────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────┐
│ ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│ │   SQL数据库      │    │   向量数据库     │    │   图数据库       │ │
│ │  (PostgreSQL)   │    │   (ChromaDB)    │    │   (Neo4j)       │ │
│ └─────────────────┘    └─────────────────┘    └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 技术栈选择

**后端技术栈**:
- **框架**: FastAPI (Python 3.9+)
- **数据库**: PostgreSQL (主数据库), SQLite (文件导入)
- **向量数据库**: ChromaDB, Milvus, Weaviate, Qdrant
- **图数据库**: Neo4j (知识图谱存储)
- **消息队列**: Redis (异步任务处理)
- **缓存**: Redis (查询结果缓存)

**前端技术栈**:
- **框架**: Vue.js 3 + TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite

**AI/ML技术栈**:
- **大语言模型**: OpenAI GPT-4, Claude, 本地模型支持
- **嵌入模型**: OpenAI Embeddings, Sentence-BERT
- **知识图谱**: spaCy, Stanford NLP

## 2. 数据处理流程设计

### 2.1 数据源接入流程

#### 2.1.1 文件上传处理

```python
class FileUploadProcessor:
    """文件上传处理器"""
    
    def process_csv_file(self, file_path: str) -> DatabaseSchema:
        """处理CSV文件"""
        # 1. 文件验证和格式检查
        # 2. 数据类型自动推断
        # 3. 生成数据库模式
        # 4. 创建数据表
        # 5. 数据导入
        pass
    
    def process_excel_file(self, file_path: str) -> DatabaseSchema:
        """处理Excel文件"""
        # 支持多工作表处理
        pass
    
    def infer_column_types(self, df) -> Dict[str, str]:
        """自动推断列数据类型"""
        # 基于数据内容和统计特征推断类型
        pass
```

#### 2.1.2 数据库连接处理

```python
class DatabaseConnector:
    """数据库连接器"""
    
    def connect_mysql(self, config: MySQLConfig) -> Connection:
        """MySQL数据库连接"""
        pass
    
    def connect_postgresql(self, config: PostgreSQLConfig) -> Connection:
        """PostgreSQL数据库连接"""
        pass
    
    def extract_schema(self, connection: Connection) -> DatabaseSchema:
        """提取数据库模式信息"""
        # 1. 获取表结构
        # 2. 获取字段信息
        # 3. 获取索引信息
        # 4. 获取外键关系
        pass
```

### 2.2 数据预处理流程

```mermaid
graph TD
    A[原始数据] --> B[数据清洗]
    B --> C[数据类型转换]
    C --> D[缺失值处理]
    D --> E[异常值检测]
    E --> F[数据标准化]
    F --> G[数据质量评估]
    G --> H[生成数据报告]
```

#### 2.2.1 数据清洗模块

```python
class DataCleaner:
    """数据清洗器"""
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗主流程"""
        df = self.remove_duplicates(df)
        df = self.handle_missing_values(df)
        df = self.detect_outliers(df)
        df = self.standardize_formats(df)
        return df
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        # 1. 统计缺失值分布
        # 2. 根据字段类型选择填充策略
        # 3. 记录处理日志
        pass
```

### 2.3 数据质量评估

```python
class DataQualityAssessor:
    """数据质量评估器"""
    
    def assess_quality(self, df: pd.DataFrame) -> QualityReport:
        """评估数据质量"""
        return QualityReport(
            completeness=self.calculate_completeness(df),
            accuracy=self.calculate_accuracy(df),
            consistency=self.calculate_consistency(df),
            validity=self.calculate_validity(df)
        )
```

## 3. 知识库构建设计

### 3.1 文档处理流程

#### 3.1.1 文档解析器

```python
class DocumentProcessor:
    """文档处理器"""
    
    def process_document(self, file_path: str, file_type: str) -> Document:
        """处理文档文件"""
        if file_type == 'pdf':
            return self.process_pdf(file_path)
        elif file_type == 'docx':
            return self.process_docx(file_path)
        elif file_type == 'md':
            return self.process_markdown(file_path)
        elif file_type == 'txt':
            return self.process_text(file_path)
    
    def extract_text_structure(self, content: str) -> StructuredText:
        """提取文本结构"""
        # 1. 段落分割
        # 2. 标题识别
        # 3. 表格提取
        # 4. 图表识别
        pass
```

#### 3.1.2 文本分块策略

```python
class TextChunker:
    """文本分块器"""
    
    def chunk_by_sentence(self, text: str, max_length: int = 512) -> List[str]:
        """按句子分块"""
        pass
    
    def chunk_by_paragraph(self, text: str, max_length: int = 1024) -> List[str]:
        """按段落分块"""
        pass
    
    def chunk_by_semantic(self, text: str, model: str = "sentence-bert") -> List[str]:
        """语义分块"""
        # 使用嵌入模型进行语义相似度分块
        pass
```

### 3.2 知识图谱构建

#### 3.2.1 实体识别与抽取

```python
class EntityExtractor:
    """实体抽取器"""
    
    def extract_entities(self, text: str) -> List[Entity]:
        """从文本中抽取实体"""
        # 1. 命名实体识别 (NER)
        # 2. 关键词提取
        # 3. 概念抽取
        # 4. 实体消歧
        pass
    
    def extract_database_entities(self, schema: DatabaseSchema) -> List[Entity]:
        """从数据库模式中抽取实体"""
        # 1. 表名作为实体
        # 2. 字段名作为属性
        # 3. 外键关系作为关系
        pass
```

#### 3.2.2 关系抽取与建模

```python
class RelationExtractor:
    """关系抽取器"""
    
    def extract_relations(self, entities: List[Entity], text: str) -> List[Relation]:
        """抽取实体间关系"""
        # 1. 句法依存分析
        # 2. 语义角色标注
        # 3. 关系模式匹配
        # 4. 深度学习关系分类
        pass
    
    def build_knowledge_graph(self, entities: List[Entity], relations: List[Relation]) -> KnowledgeGraph:
        """构建知识图谱"""
        pass
```

### 3.3 向量化与索引

#### 3.3.1 多模态向量化

```python
class VectorEncoder:
    """向量编码器"""
    
    def encode_text(self, text: str, model: str = "sentence-bert") -> np.ndarray:
        """文本向量化"""
        pass
    
    def encode_table_schema(self, schema: TableSchema) -> np.ndarray:
        """表模式向量化"""
        # 结合表名、字段名、数据类型等信息
        pass
    
    def encode_entity(self, entity: Entity) -> np.ndarray:
        """实体向量化"""
        # 结合实体名称、类型、上下文信息
        pass
    
    def encode_relation(self, relation: Relation) -> np.ndarray:
        """关系向量化"""
        # 结合关系类型、头尾实体信息
        pass
```

#### 3.3.2 向量数据库索引

```python
class VectorIndexManager:
    """向量索引管理器"""
    
    def create_text_index(self, texts: List[str], vectors: List[np.ndarray]):
        """创建文本向量索引"""
        pass
    
    def create_schema_index(self, schemas: List[TableSchema], vectors: List[np.ndarray]):
        """创建数据库模式索引"""
        pass
    
    def create_graph_index(self, entities: List[Entity], relations: List[Relation]):
        """创建知识图谱索引"""
        pass
```

### 3.4 混合检索系统

#### 3.4.1 检索策略

```python
class HybridRetriever:
    """混合检索器"""
    
    def retrieve(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """混合检索"""
        # 1. 向量相似度检索
        vector_results = self.vector_search(query, top_k)
        
        # 2. 知识图谱检索
        graph_results = self.graph_search(query, top_k)
        
        # 3. 全文检索
        text_results = self.text_search(query, top_k)
        
        # 4. 结果融合与重排序
        return self.merge_and_rerank(vector_results, graph_results, text_results)
    
    def vector_search(self, query: str, top_k: int) -> List[VectorResult]:
        """向量检索"""
        pass
    
    def graph_search(self, query: str, top_k: int) -> List[GraphResult]:
        """图检索"""
        # 基于实体和关系的图遍历搜索
        pass
    
    def merge_and_rerank(self, *results) -> List[RetrievalResult]:
        """结果融合与重排序"""
        # 使用学习排序算法融合多种检索结果
        pass
```

## 4. API设计

### 4.1 RESTful API规范

#### 4.1.1 数据源管理 API

```python
# 数据源上传
POST /api/v1/datasources/upload
Content-Type: multipart/form-data
{
    "file": <file_data>,
    "source_type": "csv|xlsx|database",
    "description": "数据源描述"
}

# 数据库连接配置
POST /api/v1/datasources/database
{
    "db_type": "mysql|postgresql|sqlite",
    "host": "localhost",
    "port": 3306,
    "database": "test_db",
    "username": "user",
    "password": "password"
}

# 获取数据源列表
GET /api/v1/datasources
Response: {
    "datasources": [
        {
            "id": "uuid",
            "name": "数据源名称",
            "type": "csv|xlsx|database",
            "status": "processing|ready|error",
            "created_at": "2024-01-01T00:00:00Z",
            "schema_info": {...}
        }
    ]
}
```

#### 4.1.2 知识库管理 API

```python
# 构建知识库
POST /api/v1/knowledge-base/build
{
    "datasource_id": "uuid",
    "config": {
        "enable_kg": true,
        "enable_vector": true,
        "chunk_size": 512,
        "embedding_model": "sentence-bert"
    }
}

# 查询知识库状态
GET /api/v1/knowledge-base/{kb_id}/status
Response: {
    "status": "building|ready|error",
    "progress": 85,
    "entities_count": 1024,
    "relations_count": 512,
    "documents_count": 128
}

# 知识库检索
POST /api/v1/knowledge-base/{kb_id}/search
{
    "query": "查询内容",
    "search_type": "vector|graph|hybrid",
    "top_k": 10
}
```

#### 4.1.3 智能查询 API

```python
# 自然语言查询
POST /api/v1/query/natural
{
    "question": "用户的自然语言问题",
    "datasource_id": "uuid",
    "context": {...}
}

# SQL查询生成
POST /api/v1/query/sql-generation
{
    "question": "用户的自然语言问题",
    "schema_id": "uuid"
}
Response: {
    "sql": "SELECT * FROM table WHERE ...",
    "explanation": "查询解释",
    "confidence": 0.95
}

# 查询结果可视化
POST /api/v1/query/visualize
{
    "sql": "SELECT * FROM table WHERE ...",
    "chart_type": "bar|line|pie|table"
}
```

### 4.2 WebSocket API

```python
# 实时进度更新
WebSocket /ws/progress/{task_id}
{
    "type": "progress_update",
    "task_id": "uuid",
    "progress": 65,
    "message": "正在处理文档..."
}

# 实时查询结果
WebSocket /ws/query/{session_id}
{
    "type": "query_result",
    "result": {...},
    "streaming": true
}
```

### 4.3 错误处理规范

```python
# 标准错误响应格式
{
    "error": {
        "code": "INVALID_FILE_FORMAT",
        "message": "不支持的文件格式",
        "details": {...},
        "timestamp": "2024-01-01T00:00:00Z",
        "request_id": "uuid"
    }
}

# 常见错误码
class ErrorCode:
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    KNOWLEDGE_BASE_NOT_FOUND = "KNOWLEDGE_BASE_NOT_FOUND"
    QUERY_PROCESSING_ERROR = "QUERY_PROCESSING_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
```

## 5. 安全设计

### 5.1 认证与授权

```python
# JWT Token认证
class AuthenticationService:
    def authenticate(self, username: str, password: str) -> TokenPair:
        """用户认证"""
        pass
    
    def refresh_token(self, refresh_token: str) -> str:
        """刷新访问令牌"""
        pass

# RBAC权限控制
class AuthorizationService:
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """检查用户权限"""
        pass
```

### 5.2 数据安全

```python
# 敏感数据加密
class DataEncryption:
    def encrypt_connection_config(self, config: dict) -> str:
        """加密数据库连接配置"""
        pass
    
    def encrypt_sensitive_fields(self, data: dict, sensitive_fields: List[str]) -> dict:
        """加密敏感字段"""
        pass
```

### 5.3 输入验证与防护

```python
# SQL注入防护
class SQLInjectionProtector:
    def validate_sql(self, sql: str) -> bool:
        """验证SQL安全性"""
        pass
    
    def sanitize_input(self, user_input: str) -> str:
        """清理用户输入"""
        pass
```

## 6. 性能优化设计

### 6.1 缓存策略

```python
# 多级缓存架构
class CacheManager:
    def __init__(self):
        self.memory_cache = {}  # 内存缓存
        self.redis_cache = RedisClient()  # Redis缓存
        self.disk_cache = DiskCache()  # 磁盘缓存
    
    def get_cached_query_result(self, query_hash: str):
        """获取缓存的查询结果"""
        pass
    
    def cache_embedding_vectors(self, text: str, vectors: np.ndarray):
        """缓存嵌入向量"""
        pass
```

### 6.2 异步处理

```python
# 异步任务处理
class AsyncTaskManager:
    def submit_knowledge_base_build(self, config: dict) -> str:
        """提交知识库构建任务"""
        pass
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        pass
```

### 6.3 数据库优化

```python
# 数据库连接池
class DatabasePool:
    def __init__(self, max_connections: int = 20):
        self.pool = create_pool(max_connections=max_connections)
    
    def get_connection(self):
        """获取数据库连接"""
        pass

# 查询优化
class QueryOptimizer:
    def optimize_sql(self, sql: str) -> str:
        """SQL查询优化"""
        pass
    
    def create_indexes(self, table_schema: TableSchema):
        """创建优化索引"""
        pass
```

## 7. 监控与日志

### 7.1 系统监控

```python
# 性能监控
class PerformanceMonitor:
    def track_api_response_time(self, endpoint: str, duration: float):
        """跟踪API响应时间"""
        pass
    
    def track_memory_usage(self):
        """跟踪内存使用"""
        pass
    
    def track_vector_db_performance(self, operation: str, duration: float):
        """跟踪向量数据库性能"""
        pass
```

### 7.2 日志系统

```python
# 结构化日志
class StructuredLogger:
    def log_user_query(self, user_id: str, query: str, result_count: int):
        """记录用户查询日志"""
        pass
    
    def log_knowledge_base_build(self, kb_id: str, status: str, metrics: dict):
        """记录知识库构建日志"""
        pass
    
    def log_error(self, error: Exception, context: dict):
        """记录错误日志"""
        pass
```

## 8. 部署架构

### 8.1 容器化部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  api-server:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/chat2dashboard
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - chromadb
  
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: chat2dashboard
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chromadb_data:/chroma/chroma
```

### 8.2 扩展性设计

```python
# 水平扩展支持
class LoadBalancer:
    def route_request(self, request_type: str) -> str:
        """请求路由到不同服务实例"""
        pass

# 数据分片
class DataSharding:
    def get_shard_key(self, data: dict) -> str:
        """获取分片键"""
        pass
    
    def route_to_shard(self, shard_key: str) -> str:
        """路由到对应分片"""
        pass
```

---

*本文档将根据系统开发进展持续更新和完善。*