"""
文档处理API接口
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, Form, UploadFile
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import os
import json
from pathlib import Path

from ...models.requests import (
    DocumentProcessRequest,
    BatchProcessRequest,
    DocumentSearchRequest
)
from ...models.responses import (
    DocumentProcessResponse,
    BatchProcessResponse,
    DocumentSearchResponse,
    ErrorResponse
)
from ...core.exceptions import (
    DocumentNotFoundError,
    UnsupportedFileTypeError,
    ProcessingInProgressError
)
from ...core.dbagent.document_processor import DocumentProcessorFactory, ProcessedDocument
from ...config import settings
from ...core.logging import get_logger

router = APIRouter(prefix="/document", tags=["document"])
logger = get_logger(__name__)

@router.post("/upload", response_model=DocumentProcessResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    kb_id: str = Form(...),
    process_immediately: bool = Form(True),
    background_tasks: BackgroundTasks = None
):
    """
    上传文档文件
    
    Args:
        files: 上传的文件列表
        kb_id: 目标知识库ID
        process_immediately: 是否立即处理
        background_tasks: 后台任务
        
    Returns:
        DocumentProcessResponse: 处理响应
    """
    logger.info(f"Received upload request for {len(files)} files to knowledge base {kb_id}")
    try:
        # 1. 验证文件类型和大小
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown', '.html', '.csv', '.xlsx', '.json', '.jpg', '.jpeg', '.png'}
        max_file_size = 100 * 1024 * 1024  # 100MB
        uploaded_files = []
        
        # 创建文档存储目录
        documents_dir = Path(settings.DATABASES_DIR) / kb_id / "docs"
        documents_dir.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            logger.info(f"Processing file: {file.filename}, size: {file.size} bytes")
            filename_lower = file.filename.lower()
            if not any(filename_lower.endswith(ext) for ext in supported_extensions):
                raise UnsupportedFileTypeError(f"File type not supported: {file.filename}")
            
            if file.size > max_file_size:
                raise HTTPException(status_code=413, detail=f"File too large: {file.filename}")
            
            # 2. 保存文件到文档目录
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix
            saved_filename = f"{file_id}{file_ext}"
            file_path = documents_dir / saved_filename
            
            # 保存文件内容
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 3. 创建文档处理记录
            doc_record = {
                "id": file_id,
                "filename": file.filename,
                "original_filename": file.filename,
                "file_path": str(file_path),
                "file_size": file.size,
                "file_type": file_ext.lstrip('.'),
                "status": "uploaded",
                "kb_id": kb_id,
                "upload_time": datetime.now().isoformat(),
                "metadata": {},
                "processing_results": {}
            }
            
            # 保存文档记录到JSON文件
            record_file = documents_dir / f"{file_id}_record.json"
            with open(record_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(doc_record, f, indent=2, ensure_ascii=False)
            
            uploaded_files.append({
                "id": file_id,
                "filename": file.filename,
                "size": file.size,
                "status": "uploaded"
            })
        
        task_id = str(uuid.uuid4())

        # if process_immediately and background_tasks:
        #     # 添加后台处理任务
        #     background_tasks.add_task(_process_documents_task, uploaded_files, kb_id)
        #
        return DocumentProcessResponse(
            task_id=task_id,
            status="uploaded" if not process_immediately else "processing",
            uploaded_files=uploaded_files,
            total_files=len(uploaded_files),
            kb_id=kb_id,
            created_at=datetime.now()
        )
        
    except UnsupportedFileTypeError as e:
        logger.error(f"Unsupported file type: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/{file_id}")
async def process_document(
    file_id: str,
    request: DocumentProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    处理单个文档
    
    Args:
        file_id: 文档ID
        request: 处理请求
        background_tasks: 后台任务
        
    Returns:
        Dict: 处理结果
    """
    try:
        # TODO: 实现单文档处理
        # 1. 验证文档存在性
        # 2. 选择合适的处理器
        # 3. 创建处理任务
        # 4. 返回任务信息
        
        task_id = str(uuid.uuid4())
        
        # 添加后台处理任务
        background_tasks.add_task(_process_single_document_task, file_id, request)
        
        return JSONResponse(content={
            "file_id": file_id,
            "task_id": task_id,
            "status": "processing",
            "config": request.config.dict() if request.config else {},
            "started_at": datetime.now().isoformat()
        })
        
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProcessingInProgressError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-process", response_model=BatchProcessResponse)
async def batch_process_documents(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    批量处理文档
    
    Args:
        request: 批量处理请求
        background_tasks: 后台任务
        
    Returns:
        BatchProcessResponse: 批量处理响应
    """
    try:
        # TODO: 实现批量处理
        # 1. 验证所有文档存在性
        # 2. 创建批量处理任务
        # 3. 并发处理文档
        # 4. 返回批量任务信息
        
        batch_id = str(uuid.uuid4())
        
        # 添加批量处理任务
        background_tasks.add_task(_batch_process_documents_task, request.file_ids, request.config)
        
        return BatchProcessResponse(
            batch_id=batch_id,
            status="processing",
            total_files=len(request.file_ids),
            processed_files=0,
            failed_files=0,
            config=request.config.dict() if request.config else {},
            started_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process/{task_id}/status")
async def get_process_status(task_id: str):
    """
    获取处理任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 任务状态信息
    """
    # 查询任务状态 - 这里 task_id 实际上是一个文档ID或批量任务ID
    documents_dir = Path(settings.DATABASES_DIR) / "documents"

    # 尝试查找单个文档记录
    record_file = documents_dir / f"{task_id}_record.json"
    if record_file.exists():
        with open(record_file, 'r', encoding='utf-8') as f:
            doc_record = json.loads(f.read())

        status = doc_record.get("status", "unknown")
        progress = 100.0 if status == "processed" else 50.0 if status == "processing" else 0.0

        return JSONResponse(content={
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "processed_files": 1 if status == "processed" else 0,
            "total_files": 1,
            "failed_files": 1 if status == "failed" else 0,
            "current_file": doc_record.get("filename") if status == "processing" else None,
            "started_at": doc_record.get("upload_time"),
            "completed_at": doc_record.get("process_time"),
            "processing_time": 0.0,  # TODO: 计算实际处理时间
            "results": doc_record.get("processing_results", {}),
            "errors": [doc_record.get("error")] if doc_record.get("error") else []
        })
        
    # 如果没有找到记录，返回默认状态
    return JSONResponse(content={
        "task_id": task_id,
        "status": "not_found",
        "progress": 0.0,
        "processed_files": 0,
        "total_files": 0,
        "failed_files": 0,
        "current_file": None,
        "started_at": None,
        "completed_at": None,
        "processing_time": 0.0,
        "results": {},
        "errors": ["Task not found"]
    })

@router.get("/{file_id}")
async def get_document_info(file_id: str):
    """
    获取文档详细信息
    
    Args:
        file_id: 文档ID
        
    Returns:
        Dict: 文档信息
    """
    try:
        # 查询文档记录
        documents_dir = Path(settings.DATABASES_DIR) / "documents"
        record_file = documents_dir / f"{file_id}_record.json"
        
        if not record_file.exists():
            raise DocumentNotFoundError(f"Document {file_id} not found")
        
        with open(record_file, 'r', encoding='utf-8') as f:
            doc_record = json.loads(f.read())
        
        return JSONResponse(content=doc_record)
        
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/content")
async def get_document_content(
    file_id: str,
    include_metadata: bool = True,
    include_structure: bool = False,
    format: str = "json"
):
    """
    获取文档内容
    
    Args:
        file_id: 文档ID
        include_metadata: 是否包含元数据
        include_structure: 是否包含结构信息
        format: 返回格式 (json, text, html)
        
    Returns:
        Dict: 文档内容
    """
    try:
        # 查询文档记录和内容
        documents_dir = Path(settings.DATABASES_DIR) / "documents"
        record_file = documents_dir / f"{file_id}_record.json"
        content_file = documents_dir / f"{file_id}_content.json"
        
        if not record_file.exists():
            raise DocumentNotFoundError(f"Document {file_id} not found")
        
        with open(record_file, 'r', encoding='utf-8') as f:
            doc_record = json.loads(f.read())
        
        response_data = {
            "file_id": file_id,
            "content": "",
            "format": format
        }
        
        # 加载文档内容
        if content_file.exists():
            with open(content_file, 'r', encoding='utf-8') as f:
                content_data = json.loads(f.read())
                response_data["content"] = content_data.get("content", "")
                
                if include_structure:
                    response_data["structure"] = content_data.get("structure", {})
                    response_data["tables"] = content_data.get("tables", [])
                    response_data["images"] = content_data.get("images", [])
                    response_data["links"] = content_data.get("links", [])
        
        if include_metadata:
            response_data["metadata"] = doc_record.get("metadata", {})
        
        return JSONResponse(content=response_data)
        
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/chunks")
async def get_document_chunks(
    file_id: str,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
    page: int = 1,
    limit: int = 20
):
    """
    获取文档分块结果
    
    Args:
        file_id: 文档ID
        chunk_size: 分块大小 (重新分块)
        overlap: 重叠大小 (重新分块)
        page: 页码
        limit: 每页数量
        
    Returns:
        Dict: 文档分块结果
    """
    try:
        # TODO: 实现文档分块获取
        # 1. 查询已有分块结果
        # 2. 可选：根据参数重新分块
        # 3. 分页返回分块数据
        
        # 模拟分块数据
        chunks = [
            {
                "id": str(uuid.uuid4()),
                "index": i,
                "content": f"这是第{i+1}个文档块的内容...",
                "start_char": i * 500,
                "end_char": (i + 1) * 500,
                "page_number": (i // 2) + 1,
                "metadata": {
                    "chunk_type": "paragraph",
                    "word_count": 150
                }
            }
            for i in range((page - 1) * limit, min(page * limit, 24))
        ]
        
        return JSONResponse(content={
            "file_id": file_id,
            "chunks": chunks,
            "total_chunks": 24,
            "page": page,
            "limit": limit,
            "chunk_config": {
                "chunk_size": chunk_size or 512,
                "overlap": overlap or 50,
                "strategy": "semantic"
            }
        })
        
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{file_id}/search", response_model=DocumentSearchResponse)
async def search_document(file_id: str, request: DocumentSearchRequest):
    """
    文档内搜索
    
    Args:
        file_id: 文档ID
        request: 搜索请求
        
    Returns:
        DocumentSearchResponse: 搜索结果
    """
    try:
        # TODO: 实现文档内搜索
        # 1. 在文档内容中搜索
        # 2. 支持关键词和语义搜索
        # 3. 返回匹配片段和位置
        
        # 模拟搜索结果
        results = [
            {
                "chunk_id": str(uuid.uuid4()),
                "content": f"包含查询词'{request.query}'的文档片段内容...",
                "score": 0.9,
                "page_number": 1,
                "position": {"start_char": 100, "end_char": 200},
                "highlight": [request.query],
                "context": "...上下文内容..."
            }
        ]
        
        return DocumentSearchResponse(
            file_id=file_id,
            query=request.query,
            results=results,
            total_matches=len(results),
            search_time=0.05
        )
        
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    file_type: Optional[str] = None,
    kb_id: Optional[str] = None
):
    """
    获取文档列表
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        status: 状态过滤
        file_type: 文件类型过滤
        kb_id: 知识库ID过滤
        
    Returns:
        Dict: 文档列表
    """
    try:
        # 查询文档列表
        documents_dir = Path(settings.DATABASES_DIR) / "documents"
        if not documents_dir.exists():
            return JSONResponse(content={
                "documents": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "filters": {
                    "status": status,
                    "file_type": file_type,
                    "kb_id": kb_id
                }
            })
        
        documents = []
        record_files = list(documents_dir.glob("*_record.json"))
        
        for record_file in record_files:
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    doc_record = json.loads(f.read())
                
                # 应用过滤条件
                if status and doc_record.get("status") != status:
                    continue
                if file_type and doc_record.get("file_type") != file_type:
                    continue
                if kb_id and doc_record.get("kb_id") != kb_id:
                    continue
                
                documents.append(doc_record)
            except (json.JSONDecodeError, Exception):
                continue
        
        # 分页处理
        total_count = len(documents)
        documents = documents[offset:offset + limit]
        
        return JSONResponse(content={
            "documents": documents,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "filters": {
                "status": status,
                "file_type": file_type,
                "kb_id": kb_id
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}")
async def delete_document(file_id: str):
    """
    删除文档
    
    Args:
        file_id: 文档ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        # 实现文档删除
        documents_dir = Path(settings.DATABASES_DIR) / "documents"
        record_file = documents_dir / f"{file_id}_record.json"
        content_file = documents_dir / f"{file_id}_content.json"
        
        if not record_file.exists():
            raise DocumentNotFoundError(f"Document {file_id} not found")
        
        # 加载文档记录获取文件路径
        with open(record_file, 'r', encoding='utf-8') as f:
            doc_record = json.loads(f.read())
        
        file_path = Path(doc_record.get("file_path", ""))
        
        # 删除相关文件
        files_to_delete = [record_file, content_file, file_path]
        for file_to_delete in files_to_delete:
            if file_to_delete.exists():
                file_to_delete.unlink()
        
        return JSONResponse(content={
            "message": f"Document {file_id} deleted successfully",
            "file_id": file_id,
            "deleted_at": datetime.now().isoformat()
        })
        
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 后台任务函数

async def _process_documents_task(uploaded_files: List[Dict], kb_id: Optional[str]):
    """
    后台文档处理任务
    
    Args:
        uploaded_files: 上传的文件列表
        kb_id: 目标知识库ID
    """
    documents_dir = Path(settings.DATABASES_DIR) / "documents"
    factory = DocumentProcessorFactory()
    
    for file_info in uploaded_files:
        file_id = file_info["id"]
        try:
            # 更新处理状态
            await _update_document_status(file_id, "processing")
            
            # 加载文档记录
            record_file = documents_dir / f"{file_id}_record.json"
            with open(record_file, 'r', encoding='utf-8') as f:
                doc_record = json.loads(f.read())
            
            file_path = doc_record["file_path"]
            
            # 获取对应的文档处理器
            processor = factory.get_processor(file_path)
            if processor:
                # 处理文档
                processed_doc = processor.process(file_path)
                
                # 更新文档记录
                doc_record["status"] = "processed"
                doc_record["process_time"] = datetime.now().isoformat()
                doc_record["metadata"] = {
                    "title": processed_doc.metadata.title or "",
                    "author": processed_doc.metadata.author or "",
                    "page_count": processed_doc.metadata.page_count,
                    "word_count": processed_doc.metadata.word_count,
                    "language": processed_doc.metadata.language,
                    "encoding": processed_doc.metadata.encoding
                }
                doc_record["processing_results"] = {
                    "text_length": len(processed_doc.content),
                    "chunks_count": 0,  # TODO: 实现分块逻辑
                    "tables_count": len(processed_doc.tables),
                    "images_count": len(processed_doc.images),
                    "links_count": len(processed_doc.links)
                }
                
                # 保存处理结果到文件
                content_file = documents_dir / f"{file_id}_content.json"
                content_data = {
                    "content": processed_doc.content,
                    "structure": processed_doc.structure,
                    "tables": processed_doc.tables,
                    "images": processed_doc.images,
                    "links": processed_doc.links,
                    "processed_at": datetime.now().isoformat()
                }
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(content_data, indent=2, ensure_ascii=False))
            else:
                doc_record["status"] = "failed"
                doc_record["error"] = "No suitable processor found"
            
            # 保存更新后的记录
            with open(record_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(doc_record, indent=2, ensure_ascii=False))
                
        except Exception as e:
            await _update_document_status(file_id, "failed", str(e))


async def _process_single_document_task(file_id: str, request: DocumentProcessRequest):
    """
    后台单文档处理任务
    
    Args:
        file_id: 文档ID
        request: 处理请求
    """
    await _process_documents_task([{"id": file_id}], None)


async def _batch_process_documents_task(file_ids: List[str], config: Optional[Dict]):
    """
    后台批量处理任务
    
    Args:
        file_ids: 文档ID列表
        config: 处理配置
    """
    file_list = [{"id": file_id} for file_id in file_ids]
    await _process_documents_task(file_list, None)


async def _update_document_status(file_id: str, status: str, error: Optional[str] = None):
    """
    更新文档处理状态
    
    Args:
        file_id: 文档ID
        status: 新状态
        error: 错误信息
    """
    documents_dir = Path(settings.DATABASES_DIR) / "documents"
    record_file = documents_dir / f"{file_id}_record.json"
    
    if record_file.exists():
        with open(record_file, 'r', encoding='utf-8') as f:
            doc_record = json.loads(f.read())
        
        doc_record["status"] = status
        if error:
            doc_record["error"] = error
            
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(doc_record, indent=2, ensure_ascii=False))
