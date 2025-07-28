from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class TableInfo(BaseModel):
    table_name: str
    filename: str
    rows: int
    columns: List[str]

class DatabaseInfo(BaseModel):
    name: str
    path: str
    has_schema: bool
    created_at: Optional[str] = None
    table_count: Optional[int] = None

class UploadResponse(BaseModel):
    message: str
    database_name: str
    database_path: str
    tables: List[TableInfo]
    total_files: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str

class SystemStatus(BaseModel):
    cpu_percent: float
    memory: Dict[str, Any]
    disk: Dict[str, Any]

class StatusResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    system: SystemStatus

class ColumnInfo(BaseModel):
    name: str
    type: str
    not_null: bool
    default_value: Any
    primary_key: bool

class TableSchema(BaseModel):
    table_name: str
    row_count: int
    columns: List[ColumnInfo]

class DatabaseSchema(BaseModel):
    database_name: str
    database_path: str
    tables: List[TableSchema]

class LogsResponse(BaseModel):
    logs: List[Dict[str, Any]]
    limit: int
    offset: int
    count: int

class ErrorResponse(BaseModel):
    error: str


# 文档处理相关响应模型

class UploadedFileInfo(BaseModel):
    """上传文件信息"""
    id: str
    filename: str
    size: int
    status: str
    file_type: Optional[str] = None
    upload_time: Optional[datetime] = None


class DocumentProcessResponse(BaseModel):
    """文档处理响应"""
    task_id: str
    status: str  # uploaded, processing, completed, failed
    uploaded_files: List[UploadedFileInfo]
    total_files: int
    kb_id: Optional[str] = None
    created_at: datetime
    message: Optional[str] = None


class ProcessingResults(BaseModel):
    """处理结果详情"""
    extracted_text_length: int
    detected_language: str
    extracted_tables: int
    extracted_images: int
    chunks_created: int


class BatchProcessResponse(BaseModel):
    """批量处理响应"""
    batch_id: str
    status: str  # processing, completed, failed, partial
    total_files: int
    processed_files: int
    failed_files: int
    config: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    results: Optional[ProcessingResults] = None
    errors: List[str] = []


class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    encoding: Optional[str] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None


class DocumentStructure(BaseModel):
    """文档结构信息"""
    headings: List[Dict[str, Any]] = []
    paragraphs: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    images: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []


class ChunkInfo(BaseModel):
    """文档块信息"""
    id: str
    index: int
    content: str
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = {}


class SearchResultItem(BaseModel):
    """搜索结果项"""
    chunk_id: str
    content: str
    score: float
    page_number: Optional[int] = None
    position: Optional[Dict[str, int]] = None
    highlight: List[str] = []
    context: Optional[str] = None


class DocumentSearchResponse(BaseModel):
    """文档搜索响应"""
    file_id: str
    query: str
    results: List[SearchResultItem]
    total_matches: int
    search_time: float
    search_type: Optional[str] = None


# 知识库相关响应模型

class KnowledgeBaseMetrics(BaseModel):
    """知识库统计指标"""
    entities_count: int = 0
    relations_count: int = 0
    documents_count: int = 0
    chunks_count: int = 0
    vector_count: int = 0
    build_time: Optional[float] = None
    index_size_mb: Optional[float] = None
    last_updated: Optional[datetime] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str
    name: str
    description: Optional[str] = None
    datasource_id: str
    status: str  # initializing, building, ready, error, updating
    config: Dict[str, Any] = {}
    tags: List[str] = []
    metrics: Optional[KnowledgeBaseMetrics] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class KnowledgeBaseBuildResponse(BaseModel):
    """知识库构建响应"""
    kb_id: str
    task_id: str
    status: str  # building, completed, failed
    message: str
    progress: float = 0.0
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    estimated_time_remaining: Optional[int] = None  # 秒
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class KnowledgeBaseSearchResult(BaseModel):
    """知识库检索结果项"""
    id: str
    content: str
    title: Optional[str] = None
    source: str  # document, kg_entity, kg_relation
    score: float
    metadata: Dict[str, Any] = {}
    snippet: Optional[str] = None
    highlight: List[str] = []
    confidence: float
    context: Optional[str] = None
    related_entities: List[str] = []


class KnowledgeBaseSearchResponse(BaseModel):
    """知识库检索响应"""
    query: str
    results: List[KnowledgeBaseSearchResult]
    total_count: int
    search_time: float
    kb_id: str
    search_type: str
    rerank_applied: bool = False
    query_expansion: Optional[str] = None


# 搜索相关响应模型

class EntityMention(BaseModel):
    """实体提及"""
    entity: str
    type: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: Optional[float] = None


class FacetValue(BaseModel):
    """分面值"""
    value: str
    count: int


class SearchResultItem(BaseModel):
    """搜索结果项"""
    id: str
    content: str
    title: Optional[str] = None
    source: str
    score: float
    metadata: Dict[str, Any] = {}
    snippet: Optional[str] = None
    highlight: List[str] = []
    entity_mentions: List[EntityMention] = []
    relation_paths: List[List[str]] = []
    confidence: Optional[float] = None
    context: Optional[str] = None


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    results: List[SearchResultItem]
    total_count: int
    search_time: float
    rerank_time: Optional[float] = None
    kb_id: str
    search_strategy: str
    fusion_method: Optional[str] = None
    explanation: Optional[str] = None
    facets: Optional[Dict[str, List[FacetValue]]] = None
    suggestions: List[str] = []
    query_expansion: Optional[str] = None


class QueryExpansion(BaseModel):
    """查询扩展"""
    type: str
    terms: List[str]
    confidence: float


class QuerySuggestion(BaseModel):
    """查询建议"""
    query: str
    score: float
    reason: str


class SearchSuggestionResponse(BaseModel):
    """搜索建议响应"""
    original_query: str
    expansions: List[QueryExpansion]
    suggestions: List[QuerySuggestion]
    kb_id: str
    expansion_strategy: str


class SearchTrend(BaseModel):
    """搜索趋势"""
    date: str
    count: int


class PopularQuery(BaseModel):
    """热门查询"""
    query: str
    count: int
    avg_score: float


class PerformanceMetrics(BaseModel):
    """性能指标"""
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float


class SearchAnalyticsResponse(BaseModel):
    """搜索分析响应"""
    kb_id: str
    period_days: int
    total_searches: int
    unique_users: int
    avg_response_time: float
    success_rate: float
    search_trends: List[SearchTrend]
    popular_queries: List[PopularQuery]
    search_strategies: Dict[str, float]
    performance_metrics: PerformanceMetrics