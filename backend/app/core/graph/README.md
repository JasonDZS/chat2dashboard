# 知识图谱模块

本模块提供了完整的知识图谱构建、存储和查询功能，支持多种构建器和存储后端。

## 📋 目录结构

```
backend/app/core/graph/
├── __init__.py                    # 模块入口和便捷函数
├── types.py                       # 类型定义和枚举
├── entities.py                    # 实体数据结构
├── relations.py                   # 关系数据结构
├── graph.py                       # 知识图谱核心结构
├── utils.py                       # 工具函数
├── extractors/                    # 抽取器模块
│   ├── __init__.py
│   ├── entity_extractor.py        # 实体抽取器
│   └── relation_extractor.py      # 关系抽取器
├── builders/                      # 构建器模块
│   ├── __init__.py
│   ├── graph_builder.py           # 标准图谱构建器
│   └── lightrag_builder.py        # LightRAG构建器
├── storage/                       # 存储模块
│   ├── __init__.py
│   ├── base_storage.py            # 存储基类
│   ├── neo4j_storage.py           # Neo4j存储
│   └── json_storage.py            # JSON文件存储
├── embeddings/                    # 嵌入模块
│   ├── __init__.py
│   └── graph_embedding.py         # 图嵌入算法
└── examples/                      # 使用示例
    ├── __init__.py
    └── lightrag_example.py        # LightRAG使用示例
```

## 🚀 快速开始

### 基本使用

```python
from backend.app.core.graph import (
    create_standard_graph_builder,
    create_lightrag_graph_builder,
    create_json_storage
)

# 创建标准图构建器
builder = create_standard_graph_builder()
graph = builder.build_graph(
    texts=["知识图谱是一种结构化的知识表示方法"],
    graph_name="demo_graph"
)

# 使用JSON存储保存图谱
storage = create_json_storage("./graphs")
storage.save_graph(graph)
```

### LightRAG构建器使用

```python
from backend.app.core.graph import create_lightrag_graph_builder

# 创建LightRAG构建器
builder = create_lightrag_graph_builder("./lightrag_storage")

# 构建知识图谱
documents = [
    "北京是中华人民共和国的首都，位于华北地区。",
    "清华大学是中国著名的高等学府，位于北京市海淀区。"
]

graph = builder.build_graph(texts=documents, graph_name="示例图谱")

# 搜索知识图谱
result = builder.search_graph("北京有什么特点？", search_type="hybrid")
print(result["result"])

# 添加新文档
new_docs = ["上海是中华人民共和国的直辖市。"]
updated_graph = builder.add_documents(new_docs)
```

## 📚 构建器类型

### 1. StandardGraphBuilder（标准构建器）

- **特点**: 基于规则和模式的实体关系抽取
- **适用**: 结构化数据、特定领域文本
- **优势**: 可控性高、可定制性强

```python
builder = StandardGraphBuilder()
graph = builder.build_graph(
    texts=["文本内容"],
    database_schema={"tables": [...]}  # 支持数据库模式
)
```

### 2. LightRAGGraphBuilder（LightRAG构建器）

- **特点**: 基于LightRAG框架的智能图谱构建
- **适用**: 大规模文档、复杂文本理解
- **优势**: 自动化程度高、质量好

```python
builder = LightRAGGraphBuilder("./storage_dir")

# 构建图谱
graph = builder.build_graph(texts=documents)

# 智能搜索
result = builder.search_graph(
    query="查询内容", 
    search_type="hybrid"  # naive, local, global, hybrid
)

# 增量更新
updated_graph = builder.add_documents(new_documents)

# 导出GraphML格式
builder.export_to_graphml(graph, "output.graphml")
```

### 3. MultiSourceGraphBuilder（多源构建器）

- **特点**: 支持多种数据源的图谱合并
- **适用**: 复杂数据集成场景
- **优势**: 数据源权重控制、冲突处理

```python
builder = MultiSourceGraphBuilder()
sources = [
    {"type": "text", "data": ["文本1", "文本2"], "weight": 1.0},
    {"type": "database", "data": database_schema, "weight": 0.8}
]
graph = builder.build_graph_from_multiple_sources(sources)
```

## 💾 存储后端

### 1. JsonStorage（JSON文件存储）

```python
storage = JsonStorage("./graphs")
storage.connect()

# 保存和加载
storage.save_graph(graph)
loaded_graph = storage.load_graph(graph_id)

# 查询
entities = storage.query_entities({"entity_type": "person"})
relations = storage.query_relations(head_entity="entity_id")
```

### 2. Neo4jStorage（Neo4j图数据库）

```python
storage = Neo4jStorage(
    uri="bolt://localhost:7687",
    username="neo4j", 
    password="password"
)

if storage.connect():
    storage.save_graph(graph)
    
    # 执行Cypher查询
    results = storage.execute_cypher(
        "MATCH (n:Entity) RETURN n LIMIT 10"
    )
```

## 🎯 LightRAG构建器详细说明

### 核心特性

1. **自动实体关系抽取**: 基于LLM的智能抽取
2. **GraphML格式支持**: 与现有系统完全兼容
3. **多种搜索模式**: naive、local、global、hybrid
4. **增量更新**: 支持动态添加文档
5. **统计分析**: 实时图谱统计信息

### GraphML文件结构

LightRAG生成的GraphML文件包含：

**节点属性**:
- `d0`: entity_id（实体ID）
- `d1`: entity_type（实体类型）
- `d2`: description（描述）
- `d3`: source_id（源ID）
- `d4`: file_path（文件路径）
- `d5`: created_at（创建时间）

**边属性**:
- `d6`: weight（权重）
- `d7`: description（关系描述）
- `d8`: keywords（关键词）
- `d9`: source_id（源ID）
- `d10`: file_path（文件路径）
- `d11`: created_at（创建时间）

### 搜索模式说明

- **naive**: 基础向量检索
- **local**: 局部图谱搜索，适合具体问题
- **global**: 全局图谱搜索，适合概览性问题  
- **hybrid**: 混合搜索，综合多种方法

### 与现有API集成

LightRAG构建器与 `knowledge_base.py` API完全兼容：

```python
# API中的GraphML解析函数可直接使用
def _parse_graphml_to_kg_json(graphml_file_path: str) -> Dict[str, Any]:
    # 解析LightRAG生成的GraphML文件
    # 返回前端可视化所需的JSON格式
```

## 🛠 工具函数

```python
from backend.app.core.graph.utils import (
    export_graph_to_cytoscape,
    export_graph_to_d3,
    find_shortest_path,
    calculate_graph_metrics,
    merge_similar_entities,
    validate_graph_consistency
)

# 导出为可视化格式
cytoscape_data = export_graph_to_cytoscape(graph)
d3_data = export_graph_to_d3(graph)

# 图分析
metrics = calculate_graph_metrics(graph)
path = find_shortest_path(graph, "entity1", "entity2")
```

## 📊 图嵌入算法

```python
from backend.app.core.graph.embeddings import (
    Node2VecEmbedding,
    TransEEmbedding
)

# Node2Vec嵌入
node2vec = Node2VecEmbedding(embedding_dim=128)
node2vec.train(graph)
similarity = node2vec.compute_entity_similarity("entity1", "entity2")

# TransE嵌入
transe = TransEEmbedding(embedding_dim=128)
transe.train(graph)
entity_emb = transe.get_entity_embedding("entity_id")
```

## 🔧 配置说明

### LightRAG配置

```python
builder = LightRAGGraphBuilder(
    working_dir="./lightrag_storage"  # 工作目录
)

# 需要实现的函数
def custom_llm_func(prompt, system_prompt=None, **kwargs):
    # 调用你的LLM服务
    return llm_response

def custom_embedding_func(texts):
    # 调用你的嵌入服务
    return embeddings

builder._llm_model_func = custom_llm_func
builder._embedding_func = custom_embedding_func
```

### 存储配置

```python
# JSON存储配置
json_storage = JsonStorage(
    storage_dir="./graphs"  # 存储目录
)

# Neo4j存储配置
neo4j_storage = Neo4jStorage(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password",
    database="neo4j"
)
```

## 📖 完整示例

查看 `examples/lightrag_example.py` 获取完整的使用示例，包括：

- 基本图谱构建
- 多种搜索模式
- 增量更新
- GraphML导出
- 统计信息获取
- 高级用法

## 🤝 扩展开发

### 自定义构建器

```python
class CustomGraphBuilder(BaseKnowledgeGraphBuilder):
    def build_graph(self, **kwargs):
        # 实现你的图谱构建逻辑
        pass
    
    def update_graph(self, graph, **kwargs):
        # 实现增量更新逻辑
        pass
```

### 自定义存储

```python
class CustomStorage(GraphStorage):
    def save_graph(self, graph):
        # 实现保存逻辑
        pass
    
    def load_graph(self, graph_id):
        # 实现加载逻辑
        pass
```

## 📝 注意事项

1. **依赖要求**: LightRAG构建器需要安装 `lightrag` 包
2. **LLM配置**: 需要配置实际的LLM和嵌入服务
3. **内存使用**: 大规模图谱可能需要较多内存
4. **并发安全**: 多线程环境下注意线程安全
5. **错误处理**: 建议添加适当的异常处理

## 🔍 故障排除

### 常见问题

1. **LightRAG未安装**: `pip install lightrag`
2. **GraphML文件未生成**: 检查LLM和嵌入函数配置
3. **搜索无结果**: 确认图谱已正确构建
4. **内存不足**: 考虑分批处理大文档

### 调试技巧

- 启用详细日志: `logging.getLogger("backend.app.core.graph").setLevel(logging.DEBUG)`
- 检查GraphML文件: 确认 `working_dir/graph_chunk_entity_relation.graphml` 存在
- 验证图谱统计: 使用 `get_graph_statistics()` 检查构建结果