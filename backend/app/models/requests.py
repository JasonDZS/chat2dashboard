from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class VisualizationRequest(BaseModel):
    query: str
    db_name: str
    chart_type: Optional[str] = None

class SchemaUpdateRequest(BaseModel):
    schema_data: Dict[str, Any]

class SQLTrainingRequest(BaseModel):
    question: str
    sql: str

class GenerateSQLRequest(BaseModel):
    num_questions: int = 10


# 文档处理相关请求模型

class DocumentProcessConfig(BaseModel):
    """文档处理配置"""
    extract_tables: bool = True
    extract_images: bool = True
    extract_links: bool = True
    chunk_size: int = Field(default=512, ge=100, le=2048)
    chunk_overlap: int = Field(default=50, ge=0, le=200)
    chunk_strategy: str = Field(default="semantic", pattern="^(semantic|fixed|paragraph)$")
    enable_ocr: bool = False
    language: str = "zh"
    preserve_formatting: bool = True


class DocumentProcessRequest(BaseModel):
    """单文档处理请求"""
    config: Optional[DocumentProcessConfig] = None
    kb_id: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class BatchProcessRequest(BaseModel):
    """批量文档处理请求"""
    file_ids: List[str] = Field(..., min_items=1)
    config: Optional[DocumentProcessConfig] = None
    kb_id: Optional[str] = None
    tags: List[str] = []
    parallel_workers: int = Field(default=4, ge=1, le=10)


class SearchType(str, Enum):
    """搜索类型枚举"""
    KEYWORD = "keyword"
    SEMANTIC = "semantic" 
    HYBRID = "hybrid"


class DocumentSearchRequest(BaseModel):
    """文档搜索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    search_type: SearchType = SearchType.HYBRID
    top_k: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    include_context: bool = True
    highlight: bool = True


# 知识库相关请求模型

class KnowledgeBaseConfig(BaseModel):
    """知识库配置"""
    enable_kg: bool = True  # 是否启用知识图谱
    enable_vector: bool = True  # 是否启用向量检索
    chunk_size: int = Field(default=512, ge=100, le=2048)
    chunk_overlap: int = Field(default=50, ge=0, le=200)
    embedding_model: str = "sentence-bert"
    kg_model: str = "relation-extraction-v1"
    index_type: str = "hnsw"  # 向量索引类型
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class KnowledgeBaseCreateRequest(BaseModel):
    """知识库创建请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    datasource_id: str = Field(..., min_length=1)
    config: Optional[KnowledgeBaseConfig] = None
    tags: List[str] = []
    auto_build: bool = True


class BuildConfigRequest(BaseModel):
    """知识库构建配置请求"""
    rebuild_all: bool = False  # 是否重新构建全部
    update_embeddings: bool = True  # 是否更新嵌入向量
    update_kg: bool = True  # 是否更新知识图谱
    chunk_size: Optional[int] = Field(None, ge=100, le=2048)
    batch_size: int = Field(default=32, ge=1, le=100)
    max_workers: int = Field(default=4, ge=1, le=10)


class KnowledgeBaseUpdateRequest(BaseModel):
    """知识库更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config: Optional[KnowledgeBaseConfig] = None
    tags: Optional[List[str]] = None
    incremental_update: bool = True  # 是否增量更新
    data_sources: Optional[List[str]] = None  # 指定更新的数据源


class KnowledgeBaseSearchRequest(BaseModel):
    """知识库检索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    search_type: SearchType = SearchType.HYBRID
    top_k: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    enable_rerank: bool = True  # 是否启用重排序
    include_metadata: bool = True
    highlight: bool = True
    expand_context: bool = False  # 是否扩展上下文


# 搜索相关请求模型

class FusionStrategy(str, Enum):
    """融合策略枚举"""
    RRF = "rrf"  # Reciprocal Rank Fusion
    WEIGHTED = "weighted"
    MAXSCORE = "maxscore"
    VOTING = "voting"


class HybridSearchRequest(BaseModel):
    """混合检索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    kb_id: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    fusion_strategy: FusionStrategy = FusionStrategy.RRF
    weights: Optional[Dict[str, float]] = None  # 各检索策略权重
    enable_rerank: bool = True
    include_facets: bool = True
    include_suggestions: bool = True


class VectorSearchRequest(BaseModel):
    """向量检索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    kb_id: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    embedding_model: str = "sentence-bert"
    similarity_metric: str = Field(default="cosine", pattern="^(cosine|euclidean|dot_product)$")
    include_metadata: bool = True


class KeywordSearchRequest(BaseModel):
    """关键词检索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    kb_id: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    operator: str = Field(default="AND", pattern="^(AND|OR)$")
    fuzzy: bool = False
    proximity_distance: int = Field(default=0, ge=0, le=10)
    boost_fields: Optional[Dict[str, float]] = None


class GraphSearchRequest(BaseModel):
    """图检索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    kb_id: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)
    max_hops: int = Field(default=2, ge=1, le=5)
    entity_types: Optional[List[str]] = None
    relation_types: Optional[List[str]] = None
    reasoning_depth: int = Field(default=1, ge=1, le=3)


class QueryExpansionStrategy(str, Enum):
    """查询扩展策略枚举"""
    SYNONYM = "synonym"
    CONTEXTUAL = "contextual"
    HISTORICAL = "historical"
    SEMANTIC = "semantic"


class QueryExpansionRequest(BaseModel):
    """查询扩展请求"""
    original_query: str = Field(..., min_length=1, max_length=500)
    kb_id: str = Field(..., min_length=1)
    strategy: QueryExpansionStrategy = QueryExpansionStrategy.SEMANTIC
    max_expansions: int = Field(default=5, ge=1, le=20)
    include_synonyms: bool = True
    include_related: bool = True
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)