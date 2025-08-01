"""
知识库管理API接口
"""
import os
import xml.etree.ElementTree as ET
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, Form, UploadFile
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pathlib import Path

from ...models.requests import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest, 
    KnowledgeBaseSearchRequest,
    BuildConfigRequest
)
from ...models.responses import (
    KnowledgeBaseResponse,
    KnowledgeBaseBuildResponse,
    KnowledgeBaseSearchResponse,
    KnowledgeBaseMetrics,
    ErrorResponse
)
from ...core.exceptions import (
    KnowledgeBaseNotFoundError,
    DatabaseNotFoundError,
    BuildInProgressError
)
from ...core.kb_builder import kb_manager
from ...config import settings
from ...core.logging import get_logger
from ...core.graph.src.builders.lightrag_builder import LightRAGGraphBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.post("/create", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(request: KnowledgeBaseCreateRequest):
    """
    创建新的知识库
    
    Args:
        request: 知识库创建请求
        
    Returns:
        KnowledgeBaseResponse: 创建结果
    """
    try:
        kb_id = request.kb_id or str(uuid.uuid4())
        
        # 创建知识库目录结构
        kb_dir = f"{settings.DATABASES_DIR}/{kb_id}"
        if os.path.exists(kb_dir):
            logger.info(f"Knowledge base directory {kb_id} already exists, skipping folder creation")
        else:
            os.mkdir(kb_dir)
            docs_dir = f"{kb_dir}/docs"
            os.mkdir(docs_dir)
        
        # 保存知识库配置
        kb_config = {
            "id": kb_id,
            "name": request.name,
            "description": request.description,
            "datasource_id": request.datasource_id,
            "config": request.config.model_dump() if request.config else {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "initializing"
        }
        
        config_file = f"{kb_dir}/config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(kb_config, f, ensure_ascii=False, indent=2)
        
        # 保存初始构建状态
        build_status = {
            "status": "initializing",
            "progress": 0.0,
            "entities_count": 0,
            "relations_count": 0,
            "documents_count": 0,
            "build_time": 0.0,
            "last_updated": datetime.now().isoformat(),
            "error_message": None
        }
        
        build_status_file = f"{kb_dir}/build_status.json"
        with open(build_status_file, 'w', encoding='utf-8') as f:
            json.dump(build_status, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created knowledge base {kb_id} with name '{request.name}'")
        
        return KnowledgeBaseResponse(
            id=kb_id,
            name=request.name,
            description=request.description,
            datasource_id=request.datasource_id,
            status="initializing",
            config=request.config.model_dump() if request.config else {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to create knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kb_id}/build", response_model=KnowledgeBaseBuildResponse)
async def build_knowledge_base(
    kb_id: str, 
    background_tasks: BackgroundTasks,
    config: Optional[BuildConfigRequest] = None
):
    """
    构建知识库
    
    Args:
        kb_id: 知识库ID
        background_tasks: 后台任务
        config: 构建配置
        
    Returns:
        KnowledgeBaseBuildResponse: 构建响应
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 使用LightRAGGraphBuilder构建知识图谱
        def build_task():
            async def async_build():
                try:
                    # 创建LightRAG构建器
                    rag_storage_dir = kb_dir / "rag_storage"
                    builder = LightRAGGraphBuilder(str(rag_storage_dir))
                    
                    # 获取文档列表
                    docs_dir = kb_dir / "docs"
                    documents = []
                    if docs_dir.exists():
                        supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown', '.html'}
                        for file_path in docs_dir.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    documents.append(f.read())
                    
                    # 构建知识图谱
                    if documents:
                        graph = await builder.build_graph(texts=documents, graph_name=f"kb_{kb_id}")
                        logger.info(f"Built graph for {kb_id}: {len(graph.entities)} entities, {len(graph.relations)} relations")
                    
                    await builder.cleanup()
                    
                except Exception as e:
                    logger.error(f"Error in build task for {kb_id}: {e}")
                    raise
                    
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(async_build())
            finally:
                loop.close()
        
        # 启动后台任务
        background_tasks.add_task(build_task)
        task_id = str(uuid.uuid4())
        
        logger.info(f"Started build task {task_id} for knowledge base {kb_id}")
        
        return KnowledgeBaseBuildResponse(
            kb_id=kb_id,
            task_id=task_id,
            status="building",
            message="Knowledge base build started",
            progress=0.0,
            started_at=datetime.now()
        )
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BuildInProgressError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start build task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{kb_id}/build/status")
async def get_build_status(kb_id: str):
    """
    获取知识库构建状态
    
    Args:
        kb_id: 知识库ID
        
    Returns:
        Dict: 构建状态信息
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 获取构建状态
        build_status = kb_manager.get_build_status(kb_id)
        
        return JSONResponse(content={
            "kb_id": kb_id,
            "status": build_status.get("status", "unknown"),
            "progress": build_status.get("progress", 0.0),
            "entities_count": build_status.get("entities_count", 0),
            "relations_count": build_status.get("relations_count", 0),
            "documents_count": build_status.get("documents_count", 0),
            "build_time": build_status.get("build_time", 0.0),
            "last_updated": build_status.get("last_updated"),
            "error_message": build_status.get("error_message")
        })
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get build status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kb_id}/update")
async def update_knowledge_base(
    kb_id: str, 
    request: KnowledgeBaseUpdateRequest,
    background_tasks: BackgroundTasks
):
    """
    增量更新知识库
    
    Args:
        kb_id: 知识库ID
        request: 更新请求
        background_tasks: 后台任务
        
    Returns:
        Dict: 更新结果
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 获取新文档列表
        docs_dir = kb_dir / "docs"
        new_documents = []
        if docs_dir.exists():
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown', '.html'}
            for file_path in docs_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    new_documents.append(str(file_path))
        
        # 启动更新任务
        task_id = kb_manager.start_update_task(kb_id, new_documents)
        
        logger.info(f"Started update task {task_id} for knowledge base {kb_id}")
        
        return JSONResponse(content={
            "kb_id": kb_id,
            "task_id": task_id,
            "status": "updating",
            "message": "Knowledge base update started",
            "documents_to_process": len(new_documents),
            "started_at": datetime.now().isoformat()
        })
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BuildInProgressError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start update task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kb_id}/search", response_model=KnowledgeBaseSearchResponse)
async def search_knowledge_base(kb_id: str, request: KnowledgeBaseSearchRequest):
    """
    知识库检索
    
    Args:
        kb_id: 知识库ID
        request: 检索请求
        
    Returns:
        KnowledgeBaseSearchResponse: 检索结果
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 检查GraphML文件是否存在
        rag_storage_dir = kb_dir / "rag_storage"
        graphml_file = rag_storage_dir / "graph_chunk_entity_relation.graphml"
        if not graphml_file.exists():
            raise HTTPException(
                status_code=400, 
                detail="Knowledge base is not ready. Please build the knowledge base first."
            )
        
        # 使用LightRAGGraphBuilder执行搜索
        builder = LightRAGGraphBuilder(str(rag_storage_dir))
        try:
            search_result = await builder.search_graph(
                query=request.query,
                search_type=request.search_type
            )
            
            # 格式化搜索结果
            results = []
            if search_result.get("result"):
                results.append({
                    "id": str(uuid.uuid4()),
                    "content": search_result["result"],
                    "title": f"搜索结果: {request.query}",
                    "source": "lightrag",
                    "score": 1.0,
                    "metadata": {"search_type": request.search_type},
                    "snippet": search_result["result"][:200] + "..." if len(search_result["result"]) > 200 else search_result["result"],
                    "highlight": [request.query],
                    "confidence": 0.95
                })
            
            return KnowledgeBaseSearchResponse(
                query=request.query,
                results=results,
                total_count=len(results),
                search_time=0.0,
                kb_id=kb_id,
                search_type=request.search_type
            )
        finally:
            await builder.cleanup()
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Knowledge base search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: str):
    """
    获取知识库详细信息
    
    Args:
        kb_id: 知识库ID
        
    Returns:
        KnowledgeBaseResponse: 知识库信息
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 读取配置文件
        config_file = kb_dir / "config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                import json
                kb_config = json.load(f)
        else:
            kb_config = {
                "id": kb_id,
                "name": "Unknown",
                "description": "",
                "datasource_id": "unknown",
                "config": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "unknown"
            }
        
        # 获取构建状态
        build_status = kb_manager.get_build_status(kb_id)
        
        return KnowledgeBaseResponse(
            id=kb_id,
            name=kb_config.get("name", "Unknown"),
            description=kb_config.get("description", ""),
            datasource_id=kb_config.get("datasource_id", "unknown"),
            status=build_status.get("status", "unknown"),
            config=kb_config.get("config", {}),
            metrics=KnowledgeBaseMetrics(
                entities_count=build_status.get("entities_count", 0),
                relations_count=build_status.get("relations_count", 0),
                documents_count=build_status.get("documents_count", 0),
                build_time=build_status.get("build_time", 0.0)
            ),
            created_at=datetime.fromisoformat(kb_config.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(build_status.get("last_updated", datetime.now().isoformat()))
        )
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get knowledge base info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_knowledge_bases(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    获取知识库列表
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        status: 状态过滤
        
    Returns:
        Dict: 知识库列表
    """
    try:
        # 扫描知识库目录
        databases_dir = Path(settings.DATABASES_DIR)
        if not databases_dir.exists():
            return JSONResponse(content={
                "knowledge_bases": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset
            })
        
        knowledge_bases = []
        
        for kb_dir in databases_dir.iterdir():
            if kb_dir.is_dir() and (kb_dir / "config.json").exists():
                try:
                    # 读取配置
                    with open(kb_dir / "config.json", 'r', encoding='utf-8') as f:
                        import json
                        kb_config = json.load(f)
                    
                    # 获取构建状态
                    build_status = kb_manager.get_build_status(kb_dir.name)
                    
                    # 应用状态过滤
                    if status and build_status.get("status") != status:
                        continue
                    
                    knowledge_bases.append({
                        "id": kb_dir.name,
                        "name": kb_config.get("name", "Unknown"),
                        "description": kb_config.get("description", ""),
                        "status": build_status.get("status", "unknown"),
                        "created_at": kb_config.get("created_at"),
                        "metrics": {
                            "entities_count": build_status.get("entities_count", 0),
                            "relations_count": build_status.get("relations_count", 0),
                            "documents_count": build_status.get("documents_count", 0)
                        }
                    })
                except Exception as e:
                    logger.warning(f"Failed to load knowledge base {kb_dir.name}: {str(e)}")
                    continue
        
        # 分页处理
        total_count = len(knowledge_bases)
        knowledge_bases = knowledge_bases[offset:offset + limit]
        
        return JSONResponse(content={
            "knowledge_bases": knowledge_bases,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Failed to list knowledge bases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """
    删除知识库
    
    Args:
        kb_id: 知识库ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 删除知识库
        result = kb_manager.delete_knowledge_base(kb_id)
        
        logger.info(f"Knowledge base {kb_id} deleted successfully")
        return JSONResponse(content=result)
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kb_id}/validate")
async def validate_knowledge_base(kb_id: str):
    """
    验证知识库完整性
    
    Args:
        kb_id: 知识库ID
        
    Returns:
        Dict: 验证结果
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 执行验证
        validation_result = kb_manager.validate_knowledge_base(kb_id)
        
        return JSONResponse(content=validation_result)
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Knowledge base validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _parse_graphml_to_kg_json(graphml_file_path: str) -> Dict[str, Any]:
    """
    解析GraphML文件并转换为知识图谱JSON格式
    
    Args:
        graphml_file_path: GraphML文件路径
        
    Returns:
        Dict: 知识图谱JSON格式数据
    """
    try:
        # 解析GraphML文件
        tree = ET.parse(graphml_file_path)
        root = tree.getroot()
        
        # GraphML命名空间
        ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
        
        nodes = []
        links = []
        categories = {}
        category_counter = 0
        
        # 解析节点
        for node in root.findall('.//graphml:node', ns):
            node_id = node.get('id')
            node_data = {}
            
            # 提取节点属性
            for data in node.findall('graphml:data', ns):
                key = data.get('key')
                value = data.text
                if key and value:
                    # 根据GraphML的key定义映射属性名
                    if key == 'd0':
                        node_data['entity_id'] = value
                    elif key == 'd1':
                        node_data['entity_type'] = value
                    elif key == 'd2':
                        node_data['description'] = value
                    elif key == 'd3':
                        node_data['source_id'] = value
                    elif key == 'd4':
                        node_data['file_path'] = value
                    else:
                        node_data[key] = value
            
            # 根据实体类型确定分类
            entity_type = node_data.get('entity_type', 'Unknown')
            if entity_type not in categories:
                categories[entity_type] = category_counter
                category_counter += 1
            
            # 构建节点对象
            node_obj = {
                "id": node_id,
                "name": node_data.get('entity_id', node_id),
                "category": categories[entity_type]
            }
            
            # 添加可选属性
            if 'description' in node_data:
                node_obj["value"] = len(node_data['description'])  # 使用描述长度作为权重
                node_obj["symbolSize"] = min(50, max(10, len(node_data['description']) / 10))  # 根据描述长度设置节点大小
            else:
                node_obj["value"] = 10
                node_obj["symbolSize"] = 15
            
            nodes.append(node_obj)
        
        # 解析边/关系
        for edge in root.findall('.//graphml:edge', ns):
            source_id = edge.get('source')
            target_id = edge.get('target')
            
            if source_id and target_id:
                links.append({
                    "source": source_id,
                    "target": target_id
                })
        
        # 构建分类列表
        categories_list = []
        for category_name, category_index in sorted(categories.items(), key=lambda x: x[1]):
            categories_list.append({"name": category_name})
        
        # 返回知识图谱JSON格式
        return {
            "nodes": nodes,
            "links": links,
            "categories": categories_list
        }
        
    except ET.ParseError as e:
        logger.error(f"Failed to parse GraphML file {graphml_file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Invalid GraphML file format: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing GraphML file {graphml_file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process GraphML file: {str(e)}")


@router.get("/{kb_id}/graph")
async def get_knowledge_graph(kb_id: str):
    """
    获取知识库的知识图谱数据
    
    Args:
        kb_id: 知识库ID
        
    Returns:
        Dict: 知识图谱JSON格式数据
    """
    try:
        # 检查知识库是否存在
        kb_dir = Path(settings.DATABASES_DIR) / kb_id
        if not kb_dir.exists():
            raise KnowledgeBaseNotFoundError(f"Knowledge base {kb_id} not found")
        
        # 查找GraphML文件
        rag_storage_dir = kb_dir / "rag_storage"
        graphml_file = rag_storage_dir / "graph_chunk_entity_relation.graphml"
        if not graphml_file.exists():
            raise HTTPException(
                status_code=404, 
                detail="Knowledge graph file not found. Please rebuild the knowledge base."
            )
        
        # 使用LightRAGGraphBuilder获取图谱统计信息
        builder = LightRAGGraphBuilder(str(rag_storage_dir))
        try:
            stats = await builder.get_graph_statistics()
            
            # 解析GraphML文件并转换为知识图谱JSON格式
            kg_data = _parse_graphml_to_kg_json(str(graphml_file))
            
            logger.info(f"Successfully retrieved knowledge graph for {kb_id}: {len(kg_data['nodes'])} nodes, {len(kg_data['links'])} links")
            
            return JSONResponse(content={
                "kb_id": kb_id,
                "graph_data": kg_data,
                "metadata": {
                    "nodes_count": len(kg_data['nodes']),
                    "links_count": len(kg_data['links']),
                    "categories_count": len(kg_data['categories']),
                    "entities_count": stats.get("entities_count", 0),
                    "relations_count": stats.get("relations_count", 0),
                    "generated_at": datetime.now().isoformat(),
                    "status": stats.get("status", "ready")
                }
            })
        finally:
            await builder.cleanup()
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get knowledge graph for {kb_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 后台任务函数

async def _build_knowledge_base_task(kb_id: str, config: Optional[BuildConfigRequest]):
    """
    后台知识库构建任务
    
    Args:
        kb_id: 知识库ID
        config: 构建配置
    """
    # 这个函数已经被 kb_manager.start_build_task 替代
    # 保留为兼容性占位符
    pass


async def _update_knowledge_base_task(kb_id: str, request: KnowledgeBaseUpdateRequest):
    """
    后台知识库更新任务
    
    Args:
        kb_id: 知识库ID
        request: 更新请求
    """
    # 这个函数已经被 kb_manager.start_update_task 替代
    # 保留为兼容性占位符
    pass