"""
JSON文件存储实现
"""
import json
import os
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .base_storage import GraphStorage
from ..entities import Entity
from ..relations import Relation
from ..graph import KnowledgeGraph
from ..types import RelationType

logger = logging.getLogger(__name__)


class JsonStorage(GraphStorage):
    """JSON文件存储"""
    
    def __init__(self, storage_dir: str = "graphs"):
        super().__init__()
        self.storage_dir = storage_dir
        self.graphs_file = os.path.join(storage_dir, "graphs.json")
        self.ensure_storage_dir()
    
    def ensure_storage_dir(self):
        """确保存储目录存在"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info(f"Created storage directory: {self.storage_dir}")
    
    def connect(self) -> bool:
        """连接到文件系统"""
        try:
            self.ensure_storage_dir()
            self.is_connected = True
            logger.info(f"Connected to JSON storage at {self.storage_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to JSON storage: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.is_connected = False
        logger.info("Disconnected from JSON storage")
    
    def save_graph(self, graph: KnowledgeGraph) -> bool:
        """保存知识图谱"""
        if not self.is_connected:
            logger.error("Not connected to storage")
            return False
        
        try:
            # 保存图谱数据到单独文件
            graph_file = os.path.join(self.storage_dir, f"{graph.id}.json")
            graph_data = graph.to_dict()
            
            with open(graph_file, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            
            # 更新图谱索引
            self._update_graph_index(graph)
            
            logger.info(f"Graph {graph.id} saved to {graph_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving graph to JSON: {e}")
            return False
    
    def load_graph(self, graph_id: str) -> Optional[KnowledgeGraph]:
        """加载知识图谱"""
        if not self.is_connected:
            logger.error("Not connected to storage")
            return None
        
        try:
            graph_file = os.path.join(self.storage_dir, f"{graph_id}.json")
            
            if not os.path.exists(graph_file):
                logger.warning(f"Graph file not found: {graph_file}")
                return None
            
            with open(graph_file, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            graph = KnowledgeGraph.from_dict(graph_data)
            logger.info(f"Graph {graph_id} loaded from {graph_file}")
            return graph
        
        except Exception as e:
            logger.error(f"Error loading graph from JSON: {e}")
            return None
    
    def delete_graph(self, graph_id: str) -> bool:
        """删除知识图谱"""
        if not self.is_connected:
            logger.error("Not connected to storage")
            return False
        
        try:
            graph_file = os.path.join(self.storage_dir, f"{graph_id}.json")
            
            if os.path.exists(graph_file):
                os.remove(graph_file)
                logger.info(f"Graph file deleted: {graph_file}")
            
            # 从索引中移除
            self._remove_from_graph_index(graph_id)
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting graph: {e}")
            return False
    
    def list_graphs(self) -> List[Dict[str, Any]]:
        """列出所有图谱"""
        if not self.is_connected:
            logger.error("Not connected to storage")
            return []
        
        try:
            if not os.path.exists(self.graphs_file):
                return []
            
            with open(self.graphs_file, 'r', encoding='utf-8') as f:
                graphs_index = json.load(f)
            
            return graphs_index.get('graphs', [])
        
        except Exception as e:
            logger.error(f"Error listing graphs: {e}")
            return []
    
    def query_entities(self, conditions: Dict[str, Any]) -> List[Entity]:
        """查询实体"""
        if not self.is_connected:
            logger.error("Not connected to storage")
            return []
        
        try:
            graph_id = conditions.get('graph_id')
            if not graph_id:
                logger.error("graph_id is required for entity query")
                return []
            
            graph = self.load_graph(graph_id)
            if not graph:
                return []
            
            entities = list(graph.entities.values())
            
            # 应用过滤条件
            if 'entity_type' in conditions:
                entity_type = conditions['entity_type']
                entities = [e for e in entities if e.entity_type.value == entity_type]
            
            if 'name' in conditions:
                name_filter = conditions['name'].lower()
                entities = [e for e in entities if name_filter in e.name.lower()]
            
            if 'min_confidence' in conditions:
                min_confidence = conditions['min_confidence']
                entities = [e for e in entities if e.confidence >= min_confidence]
            
            # 限制返回数量
            limit = conditions.get('limit', 100)
            return entities[:limit]
        
        except Exception as e:
            logger.error(f"Error querying entities: {e}")
            return []
    
    def query_relations(self, 
                       head_entity: str = None, 
                       tail_entity: str = None,
                       relation_type: RelationType = None,
                       graph_id: str = None) -> List[Relation]:
        """查询关系"""
        if not self.is_connected:
            logger.error("Not connected to storage")
            return []
        
        try:
            if not graph_id:
                logger.error("graph_id is required for relation query")
                return []
            
            graph = self.load_graph(graph_id)
            if not graph:
                return []
            
            relations = list(graph.relations.values())
            
            # 应用过滤条件
            if head_entity:
                relations = [r for r in relations if r.head_entity.id == head_entity]
            
            if tail_entity:
                relations = [r for r in relations if r.tail_entity.id == tail_entity]
            
            if relation_type:
                relations = [r for r in relations if r.relation_type == relation_type]
            
            return relations
        
        except Exception as e:
            logger.error(f"Error querying relations: {e}")
            return []
    
    def add_entity(self, graph_id: str, entity: Entity) -> bool:
        """添加实体"""
        try:
            graph = self.load_graph(graph_id)
            if not graph:
                logger.error(f"Graph {graph_id} not found")
                return False
            
            graph.add_entity(entity)
            return self.save_graph(graph)
        
        except Exception as e:
            logger.error(f"Error adding entity: {e}")
            return False
    
    def add_relation(self, graph_id: str, relation: Relation) -> bool:
        """添加关系"""
        try:
            graph = self.load_graph(graph_id)
            if not graph:
                logger.error(f"Graph {graph_id} not found")
                return False
            
            graph.add_relation(relation)
            return self.save_graph(graph)
        
        except Exception as e:
            logger.error(f"Error adding relation: {e}")
            return False
    
    def update_entity(self, graph_id: str, entity: Entity) -> bool:
        """更新实体"""
        try:
            graph = self.load_graph(graph_id)
            if not graph:
                logger.error(f"Graph {graph_id} not found")
                return False
            
            if entity.id in graph.entities:
                graph.entities[entity.id] = entity
                graph.updated_at = datetime.now()
                return self.save_graph(graph)
            else:
                return self.add_entity(graph_id, entity)
        
        except Exception as e:
            logger.error(f"Error updating entity: {e}")
            return False
    
    def update_relation(self, graph_id: str, relation: Relation) -> bool:
        """更新关系"""
        try:
            graph = self.load_graph(graph_id)
            if not graph:
                logger.error(f"Graph {graph_id} not found")
                return False
            
            if relation.id in graph.relations:
                graph.relations[relation.id] = relation
                graph.updated_at = datetime.now()
                return self.save_graph(graph)
            else:
                return self.add_relation(graph_id, relation)
        
        except Exception as e:
            logger.error(f"Error updating relation: {e}")
            return False
    
    def remove_entity(self, graph_id: str, entity_id: str) -> bool:
        """删除实体"""
        try:
            graph = self.load_graph(graph_id)
            if not graph:
                logger.error(f"Graph {graph_id} not found")
                return False
            
            success = graph.remove_entity(entity_id)
            if success:
                return self.save_graph(graph)
            return False
        
        except Exception as e:
            logger.error(f"Error removing entity: {e}")
            return False
    
    def remove_relation(self, graph_id: str, relation_id: str) -> bool:
        """删除关系"""
        try:
            graph = self.load_graph(graph_id)
            if not graph:
                logger.error(f"Graph {graph_id} not found")
                return False
            
            success = graph.remove_relation(relation_id)
            if success:
                return self.save_graph(graph)
            return False
        
        except Exception as e:
            logger.error(f"Error removing relation: {e}")
            return False
    
    def _update_graph_index(self, graph: KnowledgeGraph):
        """更新图谱索引"""
        try:
            graphs_index = {'graphs': []}
            
            if os.path.exists(self.graphs_file):
                with open(self.graphs_file, 'r', encoding='utf-8') as f:
                    graphs_index = json.load(f)
            
            # 移除已存在的图谱记录
            graphs_list = graphs_index.get('graphs', [])
            graphs_list = [g for g in graphs_list if g.get('id') != graph.id]
            
            # 添加新记录
            graph_info = {
                'id': graph.id,
                'name': graph.name,
                'created_at': graph.created_at.isoformat(),
                'updated_at': graph.updated_at.isoformat(),
                'entity_count': len(graph.entities),
                'relation_count': len(graph.relations)
            }
            graphs_list.append(graph_info)
            
            # 按更新时间排序
            graphs_list.sort(key=lambda x: x['updated_at'], reverse=True)
            
            graphs_index['graphs'] = graphs_list
            
            with open(self.graphs_file, 'w', encoding='utf-8') as f:
                json.dump(graphs_index, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Error updating graph index: {e}")
    
    def _remove_from_graph_index(self, graph_id: str):
        """从索引中移除图谱"""
        try:
            if not os.path.exists(self.graphs_file):
                return
            
            with open(self.graphs_file, 'r', encoding='utf-8') as f:
                graphs_index = json.load(f)
            
            graphs_list = graphs_index.get('graphs', [])
            graphs_list = [g for g in graphs_list if g.get('id') != graph_id]
            
            graphs_index['graphs'] = graphs_list
            
            with open(self.graphs_file, 'w', encoding='utf-8') as f:
                json.dump(graphs_index, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Error removing from graph index: {e}")
    
    def compact_storage(self):
        """压缩存储空间"""
        try:
            # 清理不存在的图谱索引
            graphs_list = self.list_graphs()
            valid_graphs = []
            
            for graph_info in graphs_list:
                graph_id = graph_info.get('id')
                graph_file = os.path.join(self.storage_dir, f"{graph_id}.json")
                
                if os.path.exists(graph_file):
                    valid_graphs.append(graph_info)
                else:
                    logger.info(f"Removing invalid graph index entry: {graph_id}")
            
            # 更新索引
            graphs_index = {'graphs': valid_graphs}
            with open(self.graphs_file, 'w', encoding='utf-8') as f:
                json.dump(graphs_index, f, ensure_ascii=False, indent=2)
            
            logger.info("Storage compaction completed")
        
        except Exception as e:
            logger.error(f"Error compacting storage: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        try:
            total_size = 0
            file_count = 0
            
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            graphs_count = len(self.list_graphs())
            
            return {
                'storage_dir': self.storage_dir,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'graphs_count': graphs_count,
                'is_connected': self.is_connected
            }
        
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {}