"""
知识库构建器模块
简化版本，主要用于构建状态管理和兼容性
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .exceptions import (
    KnowledgeBaseNotFoundError,
)
from ..config import settings
from .logging import get_logger

logger = get_logger(__name__)


class KnowledgeBaseBuilder:
    """知识库构建器 - 简化版本"""
    
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.kb_dir = Path(settings.DATABASES_DIR) / kb_id
        self.rag_storage_dir = self.kb_dir / "rag_storage"
        
        # 构建状态
        self.build_status = {
            "status": "initializing",
            "progress": 0.0,
            "entities_count": 0,
            "relations_count": 0,
            "documents_count": 0,
            "build_time": 0.0,
            "last_updated": datetime.now().isoformat(),
            "error_message": None
        }
    
    
    def _get_kb_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        从lightrag保存的graph_chunk_entity_relation.graphml文件中读取
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            graphml_file = self.rag_storage_dir / "graph_chunk_entity_relation.graphml"
            
            if not graphml_file.exists():
                return {"entities_count": 0, "relations_count": 0}
            
            # 简单的文本解析
            with open(graphml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                entities_count = content.count('<node ')
                relations_count = content.count('<edge ')
            
            return {
                "entities_count": entities_count,
                "relations_count": relations_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to get KB statistics: {str(e)}")
            return {"entities_count": 0, "relations_count": 0}
    
    def _save_build_status(self):
        """保存构建状态到文件"""
        status_file = self.kb_dir / "build_status.json"
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(self.build_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save build status: {str(e)}")
    
    def get_build_status(self) -> Dict[str, Any]:
        """
        获取构建状态
        
        Returns:
            Dict[str, Any]: 构建状态
        """
        status_file = self.kb_dir / "build_status.json"
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                    # 检查GraphML文件是否存在来确定状态
                    graphml_file = self.rag_storage_dir / "graph_chunk_entity_relation.graphml"
                    if graphml_file.exists() and status.get("status") != "error":
                        stats = self._get_kb_statistics()
                        status.update({
                            "status": "ready",
                            "entities_count": stats.get("entities_count", 0),
                            "relations_count": stats.get("relations_count", 0)
                        })
                    return status
            except Exception as e:
                logger.error(f"Failed to load build status: {str(e)}")
        
        return self.build_status
    
    def update_knowledge_base(self, new_documents) -> Dict[str, Any]:
        """
        增量更新知识库 - 已废弃，使用LightRAGGraphBuilder代替
        
        Args:
            new_documents: 新文档路径列表
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        logger.warning("update_knowledge_base is deprecated. Use LightRAGGraphBuilder instead.")
        return {"status": "deprecated", "message": "Use LightRAGGraphBuilder instead"}
    
    
    def validate_knowledge_base(self) -> Dict[str, Any]:
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
                "checks": {}
            }
            
            # 检查GraphML文件是否存在
            graphml_file = self.rag_storage_dir / "graph_chunk_entity_relation.graphml"
            if not graphml_file.exists():
                validation_result["valid"] = False
                validation_result["checks"]["graph_file"] = {
                    "status": "missing",
                    "message": "Knowledge graph file not found"
                }
            else:
                validation_result["checks"]["graph_file"] = {
                    "status": "valid",
                    "path": str(graphml_file)
                }
            
            # 检查构建状态
            build_status = self.get_build_status()
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
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Knowledge base validation failed: {str(e)}")
            return {
                "kb_id": self.kb_id,
                "valid": False,
                "validation_time": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def delete_knowledge_base(self) -> Dict[str, Any]:
        """
        删除知识库
        
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            import shutil
            
            if self.kb_dir.exists():
                # 删除 rag_storage/, config.json, build_status.json
                shutil.rmtree(self.kb_dir / "rag_storage", ignore_errors=True)
                (self.kb_dir / "config.json").unlink(missing_ok=True)
                (self.kb_dir / "build_status.json").unlink(missing_ok=True)

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
    """知识库管理器 - 简化版本"""
    
    def __init__(self):
        self.builders: Dict[str, KnowledgeBaseBuilder] = {}
    
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
    
    def start_update_task(self, kb_id: str, new_documents) -> str:
        """
        启动更新任务 - 已废弃
        
        Returns:
            str: 任务ID
        """
        logger.warning("start_update_task is deprecated. Use LightRAGGraphBuilder instead.")
        return "deprecated"
    
    def get_build_status(self, kb_id: str) -> Dict[str, Any]:
        """
        获取构建状态
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            Dict[str, Any]: 构建状态
        """
        builder = self.get_builder(kb_id)
        return builder.get_build_status()
    
    def validate_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """
        验证知识库
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        builder = self.get_builder(kb_id)
        return builder.validate_knowledge_base()
    
    def delete_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """
        删除知识库
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        builder = self.get_builder(kb_id)
        result = builder.delete_knowledge_base()
        
        # 清理管理器中的引用
        if kb_id in self.builders:
            del self.builders[kb_id]
        
        return result


# 全局知识库管理器实例
kb_manager = KnowledgeBaseManager()
