"""
知识图谱模块

本模块提供完整的知识图谱构建、存储和查询功能，包括：
- 实体和关系的数据结构
- 从文本和数据库抽取实体和关系
- 知识图谱的构建和管理
- 多种存储后端支持 (JSON, Neo4j)
- 图嵌入和相似度计算

主要组件：
- types: 实体类型和关系类型定义
- entities: 实体数据结构和操作
- relations: 关系数据结构和操作  
- graph: 知识图谱核心数据结构
- extractors: 实体和关系抽取器
- builders: 图谱构建器
- storage: 存储后端
- embeddings: 图嵌入处理

使用示例：
    from backend.app.core.graph import (
        KnowledgeGraph, 
        StandardGraphBuilder,
        JsonStorage
    )
    
    # 创建图构建器
    builder = StandardGraphBuilder()
    
    # 构建图谱
    graph = builder.build_graph(
        texts=["知识图谱是一种结构化的知识表示方法"],
        graph_name="demo_graph"  
    )
    
    # 保存图谱
    storage = JsonStorage("./graphs")
    storage.connect()
    storage.save_graph(graph)
"""

# 核心数据结构
from .types import EntityType, RelationType
from .entities import Entity
from .relations import Relation
from .graph import KnowledgeGraph

# 抽取器
from .extractors import (
    BaseEntityExtractor, TextEntityExtractor, DatabaseEntityExtractor,
    BaseRelationExtractor, TextRelationExtractor, DatabaseRelationExtractor
)

# 构建器
from .builders import (
    BaseKnowledgeGraphBuilder, StandardGraphBuilder, MultiSourceGraphBuilder, LightRAGGraphBuilder
)

# 存储
from .storage import GraphStorage, Neo4jStorage, JsonStorage

# 嵌入
from .embeddings import GraphEmbedding, Node2VecEmbedding, TransEEmbedding

__version__ = "1.0.0"

__all__ = [
    # 核心类型和数据结构
    'EntityType',
    'RelationType', 
    'Entity',
    'Relation',
    'KnowledgeGraph',
    
    # 抽取器
    'BaseEntityExtractor',
    'TextEntityExtractor', 
    'DatabaseEntityExtractor',
    'BaseRelationExtractor',
    'TextRelationExtractor',
    'DatabaseRelationExtractor',
    
    # 构建器
    'BaseKnowledgeGraphBuilder',
    'StandardGraphBuilder',
    'MultiSourceGraphBuilder',
    'LightRAGGraphBuilder',
    
    # 存储
    'GraphStorage',
    'Neo4jStorage',
    'JsonStorage',
    
    # 嵌入
    'GraphEmbedding',
    'Node2VecEmbedding', 
    'TransEEmbedding'
]


def create_standard_graph_builder():
    """
    创建标准图构建器的便捷函数
    
    Returns:
        StandardGraphBuilder: 配置好的标准图构建器
    """
    return StandardGraphBuilder()


def create_lightrag_graph_builder(working_dir: str = "lightrag_storage"):
    """
    创建LightRAG图构建器的便捷函数
    
    Args:
        working_dir: LightRAG工作目录
        
    Returns:
        LightRAGGraphBuilder: 配置好的LightRAG图构建器
    """
    return LightRAGGraphBuilder(working_dir)


def create_json_storage(storage_dir: str = "graphs"):
    """
    创建JSON存储的便捷函数
    
    Args:
        storage_dir: 存储目录路径
        
    Returns:
        JsonStorage: 配置好的JSON存储实例
    """
    storage = JsonStorage(storage_dir)
    storage.connect()
    return storage


def create_neo4j_storage(uri: str, username: str, password: str, database: str = "neo4j"):
    """
    创建Neo4j存储的便捷函数
    
    Args:
        uri: Neo4j数据库URI
        username: 用户名
        password: 密码  
        database: 数据库名称
        
    Returns:
        Neo4jStorage: 配置好的Neo4j存储实例，如果连接失败返回None
    """
    storage = Neo4jStorage(uri, username, password, database)
    if storage.connect():
        return storage
    return None


def quick_build_graph(texts: list = None, database_schema: dict = None, 
                     graph_name: str = "quick_graph"):
    """
    快速构建知识图谱的便捷函数
    
    Args:
        texts: 文本列表
        database_schema: 数据库模式
        graph_name: 图谱名称
        
    Returns:
        KnowledgeGraph: 构建的知识图谱
    """
    builder = create_standard_graph_builder()
    return builder.build_graph(
        texts=texts,
        database_schema=database_schema, 
        graph_name=graph_name
    )