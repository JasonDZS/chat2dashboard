"""
知识库构建器模块
使用LightRAG构建向量数据库和知识图谱
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path
from datetime import datetime
import uuid

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.llm.openai import gpt_4o_mini_complete, gpt_4o_complete, openai_embed
    from lightrag.kg.shared_storage import initialize_pipeline_status
    from lightrag.utils import setup_logger
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False

from .dbagent.document_processor import DocumentProcessorFactory, ProcessedDocument
from .exceptions import (
    KnowledgeBaseNotFoundError,
    BuildInProgressError,
    DocumentNotFoundError
)
from ..config import settings
from .logging import get_logger

logger = get_logger(__name__)

# 设置LightRAG日志
if LIGHTRAG_AVAILABLE:
    setup_logger("lightrag", level="INFO")


class KnowledgeBaseBuilder:
    """知识库构建器"""
    
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.kb_dir = Path(settings.DATABASES_DIR) / kb_id
        self.docs_dir = self.kb_dir / "docs"
        self.rag_storage_dir = self.kb_dir / "rag_storage"
        self.rag_instance: Optional[Any] = None
        self.factory = DocumentProcessorFactory()
        
        # 创建必要的目录
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)
        self.rag_storage_dir.mkdir(exist_ok=True)
        
        # 构建状态
        self.build_status = {
            "status": "initializing",  # initializing, building, ready, error
            "progress": 0.0,
            "entities_count": 0,
            "relations_count": 0,
            "documents_count": 0,
            "build_time": 0.0,
            "last_updated": datetime.now().isoformat(),
            "error_message": None
        }
    
    async def initialize_rag(self):
        """
        初始化LightRAG实例
        
        Returns:
            LightRAG实例或None
        """
        if not LIGHTRAG_AVAILABLE:
            raise ImportError("LightRAG is not installed. Please install it first.")
        
        try:
            rag = LightRAG(
                working_dir=str(self.rag_storage_dir),
                embedding_func=openai_embed,
                llm_model_func=gpt_4o_mini_complete,
            )
            
            # 重要：两个初始化调用都是必需的！
            await rag.initialize_storages()  # 初始化存储后端
            await initialize_pipeline_status()  # 初始化处理管道
            
            logger.info(f"LightRAG initialized for knowledge base {self.kb_id}")
            return rag
            
        except Exception as e:
            logger.error(f"Failed to initialize LightRAG: {str(e)}")
            raise
    
    async def build_knowledge_base(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        构建知识库
        
        Args:
            config: 构建配置
            
        Returns:
            Dict[str, Any]: 构建结果
        """
        logger.info(f"Starting knowledge base build for {self.kb_id}")
        
        try:
            # 更新状态
            self.build_status.update({
                "status": "building",
                "progress": 0.0,
                "last_updated": datetime.now().isoformat()
            })
            await self._save_build_status()
            
            # 初始化RAG
            self.rag_instance = await self.initialize_rag()
            
            # 获取文档列表
            documents = await self._get_documents_to_process()
            total_docs = len(documents)
            
            if total_docs == 0:
                logger.warning(f"No documents found for knowledge base {self.kb_id}")
                self.build_status.update({
                    "status": "ready",
                    "progress": 100.0,
                    "documents_count": 0,
                    "last_updated": datetime.now().isoformat()
                })
                await self._save_build_status()
                return self.build_status
            
            logger.info(f"Found {total_docs} documents to process")
            
            # 处理文档并构建知识库
            processed_count = 0
            start_time = datetime.now()
            
            for i, doc_path in enumerate(documents):
                try:
                    # 处理单个文档
                    await self._process_single_document(doc_path)
                    processed_count += 1
                    
                    # 更新进度
                    progress = (processed_count / total_docs) * 100
                    self.build_status.update({
                        "progress": progress,
                        "documents_count": processed_count,
                        "last_updated": datetime.now().isoformat()
                    })
                    await self._save_build_status()
                    
                    logger.info(f"Processed document {i+1}/{total_docs}: {doc_path.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to process document {doc_path}: {str(e)}")
                    continue
            
            # 获取最终统计信息
            build_time = (datetime.now() - start_time).total_seconds()
            stats = await self._get_kb_statistics()
            
            # 更新最终状态
            self.build_status.update({
                "status": "ready",
                "progress": 100.0,
                "entities_count": stats.get("entities_count", 0),
                "relations_count": stats.get("relations_count", 0),
                "documents_count": processed_count,
                "build_time": build_time,
                "last_updated": datetime.now().isoformat(),
                "error_message": None
            })
            await self._save_build_status()
            
            logger.info(f"Knowledge base build completed for {self.kb_id}")
            return self.build_status
            
        except Exception as e:
            logger.error(f"Knowledge base build failed: {str(e)}")
            self.build_status.update({
                "status": "error",
                "error_message": str(e),
                "last_updated": datetime.now().isoformat()
            })
            await self._save_build_status()
            raise
        finally:
            if self.rag_instance:
                await self.rag_instance.finalize_storages()
    
    async def _get_documents_to_process(self) -> List[Path]:
        """
        获取需要处理的文档列表
        
        Returns:
            List[Path]: 文档路径列表
        """
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown', '.html'}
        documents = []
        
        if self.docs_dir.exists():
            for file_path in self.docs_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    documents.append(file_path)
        
        return sorted(documents)
    
    async def _process_single_document(self, doc_path: Path):
        """
        处理单个文档并添加到知识库
        
        Args:
            doc_path: 文档路径
        """
        try:
            # 使用文档处理器提取内容
            processor = self.factory.get_processor(str(doc_path))
            if not processor:
                logger.warning(f"No processor available for {doc_path}")
                return
            
            processed_doc = processor.process(str(doc_path))
            
            # 准备文档内容
            content = processed_doc.content
            if not content.strip():
                logger.warning(f"Document {doc_path.name} has no content")
                return
            
            # 添加元数据信息到内容
            metadata_text = f"""
文档标题: {processed_doc.metadata.title or doc_path.stem}
文件名: {processed_doc.metadata.file_name}
文档类型: {processed_doc.metadata.doc_type.value}
字数: {processed_doc.metadata.word_count}
创建时间: {processed_doc.metadata.created_time}

文档内容:
{content}
"""
            
            # 插入到LightRAG
            await self.rag_instance.ainsert(metadata_text)
            
            logger.debug(f"Inserted document {doc_path.name} into knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to process document {doc_path}: {str(e)}")
            raise
    
    async def _get_kb_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 这里需要根据LightRAG的实际API来获取统计信息
            # 目前返回模拟数据
            return {
                "entities_count": 0,  # 需要从LightRAG获取实际数据
                "relations_count": 0,  # 需要从LightRAG获取实际数据
            }
        except Exception as e:
            logger.error(f"Failed to get KB statistics: {str(e)}")
            return {"entities_count": 0, "relations_count": 0}
    
    async def _save_build_status(self):
        """保存构建状态到文件"""
        status_file = self.kb_dir / "build_status.json"
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(self.build_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save build status: {str(e)}")
    
    async def get_build_status(self) -> Dict[str, Any]:
        """
        获取构建状态
        
        Returns:
            Dict[str, Any]: 构建状态
        """
        status_file = self.kb_dir / "build_status.json"
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load build status: {str(e)}")
        
        return self.build_status
    
    async def update_knowledge_base(self, new_documents: List[str]) -> Dict[str, Any]:
        """
        增量更新知识库
        
        Args:
            new_documents: 新文档路径列表
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        logger.info(f"Starting incremental update for knowledge base {self.kb_id}")
        
        try:
            # 初始化RAG
            self.rag_instance = await self.initialize_rag()
            
            # 处理新文档
            processed_count = 0
            start_time = datetime.now()
            
            for doc_path_str in new_documents:
                doc_path = Path(doc_path_str)
                if doc_path.exists():
                    await self._process_single_document(doc_path)
                    processed_count += 1
            
            # 更新统计信息
            update_time = (datetime.now() - start_time).total_seconds()
            stats = await self._get_kb_statistics()
            
            # 更新构建状态
            current_status = await self.get_build_status()
            current_status.update({
                "documents_count": current_status.get("documents_count", 0) + processed_count,
                "entities_count": stats.get("entities_count", 0),
                "relations_count": stats.get("relations_count", 0),
                "last_updated": datetime.now().isoformat()
            })
            
            self.build_status = current_status
            await self._save_build_status()
            
            logger.info(f"Incremental update completed, processed {processed_count} documents")
            
            return {
                "status": "completed",
                "processed_documents": processed_count,
                "update_time": update_time,
                "total_documents": current_status["documents_count"]
            }
            
        except Exception as e:
            logger.error(f"Incremental update failed: {str(e)}")
            raise
        finally:
            if self.rag_instance:
                await self.rag_instance.finalize_storages()
    
    async def search_knowledge_base(
        self, 
        query: str, 
        search_type: str = "hybrid",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            query: 查询字符串
            search_type: 搜索类型 (hybrid, vector, graph)
            top_k: 返回结果数量
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        if not LIGHTRAG_AVAILABLE:
            raise ImportError("LightRAG is not installed")
        
        try:
            # 初始化RAG实例
            self.rag_instance = await self.initialize_rag()
            
            # 设置查询参数
            param = QueryParam(mode=search_type)
            
            # 执行查询
            start_time = datetime.now()
            result = await self.rag_instance.aquery(query, param=param)
            search_time = (datetime.now() - start_time).total_seconds()
            
            # 格式化结果
            return {
                "query": query,
                "result": result,
                "search_type": search_type,
                "search_time": search_time,
                "kb_id": self.kb_id
            }
            
        except Exception as e:
            logger.error(f"Knowledge base search failed: {str(e)}")
            raise
        finally:
            if self.rag_instance:
                await self.rag_instance.finalize_storages()
    
    async def validate_knowledge_base(self) -> Dict[str, Any]:
        """
        验证知识库完整性
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            validation_result = {
                "kb_id": self.kb_id,
                "valid": True,
                "validation_time": datetime.now().isoformat(),
                "checks": {},
                "performance_metrics": {}
            }
            
            # 检查目录结构
            if not self.rag_storage_dir.exists():
                validation_result["valid"] = False
                validation_result["checks"]["storage_directory"] = {
                    "status": "missing",
                    "message": "RAG storage directory not found"
                }
            else:
                validation_result["checks"]["storage_directory"] = {
                    "status": "valid",
                    "path": str(self.rag_storage_dir)
                }
            
            # 检查构建状态
            build_status = await self.get_build_status()
            if build_status.get("status") == "ready":
                validation_result["checks"]["build_status"] = {
                    "status": "valid",
                    "documents_count": build_status.get("documents_count", 0)
                }
            else:
                validation_result["valid"] = False
                validation_result["checks"]["build_status"] = {
                    "status": "invalid",
                    "current_status": build_status.get("status", "unknown")
                }
            
            # 性能指标
            if self.rag_storage_dir.exists():
                storage_size = sum(
                    f.stat().st_size 
                    for f in self.rag_storage_dir.rglob('*') 
                    if f.is_file()
                ) / (1024 * 1024)  # MB
                
                validation_result["performance_metrics"] = {
                    "storage_size_mb": round(storage_size, 2),
                    "documents_count": build_status.get("documents_count", 0),
                    "entities_count": build_status.get("entities_count", 0),
                    "relations_count": build_status.get("relations_count", 0)
                }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Knowledge base validation failed: {str(e)}")
            return {
                "kb_id": self.kb_id,
                "valid": False,
                "validation_time": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def delete_knowledge_base(self) -> Dict[str, Any]:
        """
        删除知识库
        
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            import shutil
            
            if self.kb_dir.exists():
                shutil.rmtree(self.kb_dir)
                logger.info(f"Knowledge base {self.kb_id} deleted successfully")
            
            return {
                "message": f"Knowledge base {self.kb_id} deleted successfully",
                "kb_id": self.kb_id,
                "deleted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge base {self.kb_id}: {str(e)}")
            raise


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self):
        self.builders: Dict[str, KnowledgeBaseBuilder] = {}
        self.build_tasks: Dict[str, asyncio.Task] = {}
    
    def get_builder(self, kb_id: str) -> KnowledgeBaseBuilder:
        """
        获取知识库构建器
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            KnowledgeBaseBuilder: 构建器实例
        """
        if kb_id not in self.builders:
            self.builders[kb_id] = KnowledgeBaseBuilder(kb_id)
        return self.builders[kb_id]
    
    async def start_build_task(self, kb_id: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        启动构建任务
        
        Args:
            kb_id: 知识库ID
            config: 构建配置
            
        Returns:
            str: 任务ID
        """
        if kb_id in self.build_tasks and not self.build_tasks[kb_id].done():
            raise BuildInProgressError(f"Knowledge base {kb_id} is already being built")
        
        builder = self.get_builder(kb_id)
        task = asyncio.create_task(builder.build_knowledge_base(config))
        self.build_tasks[kb_id] = task
        
        task_id = str(uuid.uuid4())
        logger.info(f"Started build task {task_id} for knowledge base {kb_id}")
        
        return task_id
    
    async def start_update_task(self, kb_id: str, new_documents: List[str]) -> str:
        """
        启动更新任务
        
        Args:
            kb_id: 知识库ID
            new_documents: 新文档列表
            
        Returns:
            str: 任务ID
        """
        if kb_id in self.build_tasks and not self.build_tasks[kb_id].done():
            raise BuildInProgressError(f"Knowledge base {kb_id} is busy")
        
        builder = self.get_builder(kb_id)
        task = asyncio.create_task(builder.update_knowledge_base(new_documents))
        self.build_tasks[kb_id] = task
        
        task_id = str(uuid.uuid4())
        logger.info(f"Started update task {task_id} for knowledge base {kb_id}")
        
        return task_id
    
    async def get_build_status(self, kb_id: str) -> Dict[str, Any]:
        """
        获取构建状态
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            Dict[str, Any]: 构建状态
        """
        builder = self.get_builder(kb_id)
        return await builder.get_build_status()
    
    async def search_knowledge_base(
        self, 
        kb_id: str, 
        query: str, 
        search_type: str = "hybrid",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            kb_id: 知识库ID
            query: 查询字符串
            search_type: 搜索类型
            top_k: 返回结果数量
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        builder = self.get_builder(kb_id)
        return await builder.search_knowledge_base(query, search_type, top_k)
    
    async def validate_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """
        验证知识库
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        builder = self.get_builder(kb_id)
        return await builder.validate_knowledge_base()
    
    async def delete_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """
        删除知识库
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        # 停止正在进行的任务
        if kb_id in self.build_tasks and not self.build_tasks[kb_id].done():
            self.build_tasks[kb_id].cancel()
            del self.build_tasks[kb_id]
        
        builder = self.get_builder(kb_id)
        result = await builder.delete_knowledge_base()
        
        # 清理管理器中的引用
        if kb_id in self.builders:
            del self.builders[kb_id]
        
        return result


# 全局知识库管理器实例
kb_manager = KnowledgeBaseManager()
