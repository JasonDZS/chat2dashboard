"""
知识库管理API接口
"""
import os
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
        kb_id = str(uuid.uuid4())
        
        # 创建知识库目录结构
        kb_dir = f"{settings.DATABASES_DIR}/{kb_id}"
        os.mkdir(kb_dir) if not os.path.exists(kb_dir) else None
        docs_dir = f"{kb_dir}/docs"
        os.mkdir(docs_dir) if not os.path.exists(docs_dir) else None
        
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
        
        # 启动构建任务
        config_dict = config.model_dump() if config else None
        task_id = await kb_manager.start_build_task(kb_id, config_dict)
        
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
        build_status = await kb_manager.get_build_status(kb_id)
        
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
        task_id = await kb_manager.start_update_task(kb_id, new_documents)
        
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
        
        # 检查知识库是否已构建
        build_status = await kb_manager.get_build_status(kb_id)
        if build_status.get("status") != "ready":
            raise HTTPException(
                status_code=400, 
                detail=f"Knowledge base is not ready. Current status: {build_status.get('status')}"
            )
        
        # 执行搜索
        search_result = await kb_manager.search_knowledge_base(
            kb_id=kb_id,
            query=request.query,
            search_type=request.search_type,
            top_k=request.top_k
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
            search_time=search_result.get("search_time", 0.0),
            kb_id=kb_id,
            search_type=request.search_type
        )
        
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
        build_status = await kb_manager.get_build_status(kb_id)
        
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
                    build_status = await kb_manager.get_build_status(kb_dir.name)
                    
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
        result = await kb_manager.delete_knowledge_base(kb_id)
        
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
        validation_result = await kb_manager.validate_knowledge_base(kb_id)
        
        return JSONResponse(content=validation_result)
        
    except KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Knowledge base validation failed: {str(e)}")
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