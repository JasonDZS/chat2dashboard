"""
知识图谱核心数据结构
"""
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .entities import Entity
from .relations import Relation
from .types import EntityType, RelationType


@dataclass
class KnowledgeGraph:
    """知识图谱类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    entities: Dict[str, Entity] = field(default_factory=dict)
    relations: Dict[str, Relation] = field(default_factory=dict)
    entity_index: Dict[str, Set[str]] = field(default_factory=dict)  # 按类型索引实体
    relation_index: Dict[str, Set[str]] = field(default_factory=dict)  # 按类型索引关系
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_entity(self, entity: Entity) -> bool:
        """添加实体"""
        if entity.id in self.entities:
            return False
        
        self.entities[entity.id] = entity
        self._index_entity(entity)
        self.updated_at = datetime.now()
        return True
    
    def add_relation(self, relation: Relation) -> bool:
        """添加关系"""
        if not relation.is_valid() or relation.id in self.relations:
            return False
        
        # 确保相关实体存在
        if (relation.head_entity.id not in self.entities or 
            relation.tail_entity.id not in self.entities):
            return False
        
        self.relations[relation.id] = relation
        self._index_relation(relation)
        self.updated_at = datetime.now()
        return True
    
    def remove_entity(self, entity_id: str) -> bool:
        """删除实体及其相关关系"""
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        
        # 删除相关关系
        relations_to_remove = []
        for relation in self.relations.values():
            if (relation.head_entity.id == entity_id or 
                relation.tail_entity.id == entity_id):
                relations_to_remove.append(relation.id)
        
        for relation_id in relations_to_remove:
            self.remove_relation(relation_id)
        
        # 删除实体
        del self.entities[entity_id]
        self._unindex_entity(entity)
        self.updated_at = datetime.now()
        return True
    
    def remove_relation(self, relation_id: str) -> bool:
        """删除关系"""
        if relation_id not in self.relations:
            return False
        
        relation = self.relations[relation_id]
        del self.relations[relation_id]
        self._unindex_relation(relation)
        self.updated_at = datetime.now()
        return True
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        return self.entities.get(entity_id)
    
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """获取关系"""
        return self.relations.get(relation_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """按类型获取实体"""
        entity_ids = self.entity_index.get(entity_type.value, set())
        return [self.entities[entity_id] for entity_id in entity_ids 
                if entity_id in self.entities]
    
    def get_relations_by_type(self, relation_type: RelationType) -> List[Relation]:
        """按类型获取关系"""
        relation_ids = self.relation_index.get(relation_type.value, set())
        return [self.relations[relation_id] for relation_id in relation_ids 
                if relation_id in self.relations]
    
    def get_entity_relations(self, entity_id: str, 
                           relation_type: Optional[RelationType] = None,
                           direction: str = 'both') -> List[Relation]:
        """获取实体的关系"""
        if entity_id not in self.entities:
            return []
        
        entity_relations = []
        for relation in self.relations.values():
            if relation_type and relation.relation_type != relation_type:
                continue
            
            if direction in ['out', 'both'] and relation.head_entity.id == entity_id:
                entity_relations.append(relation)
            elif direction in ['in', 'both'] and relation.tail_entity.id == entity_id:
                entity_relations.append(relation)
        
        return entity_relations
    
    def get_neighbors(self, entity_id: str, 
                     relation_type: Optional[RelationType] = None,
                     direction: str = 'both') -> List[Entity]:
        """获取邻居实体"""
        relations = self.get_entity_relations(entity_id, relation_type, direction)
        neighbors = []
        
        for relation in relations:
            if relation.head_entity.id == entity_id:
                neighbors.append(relation.tail_entity)
            elif relation.tail_entity.id == entity_id:
                neighbors.append(relation.head_entity)
        
        return neighbors
    
    def find_path(self, start_entity_id: str, end_entity_id: str, 
                  max_depth: int = 3) -> List[List[Relation]]:
        """查找实体间路径"""
        if (start_entity_id not in self.entities or 
            end_entity_id not in self.entities):
            return []
        
        paths = []
        visited = set()
        
        def dfs(current_id: str, target_id: str, path: List[Relation], depth: int):
            if depth > max_depth:
                return
            
            if current_id == target_id and path:
                paths.append(path.copy())
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            
            for relation in self.get_entity_relations(current_id, direction='out'):
                if relation.tail_entity.id not in visited:
                    path.append(relation)
                    dfs(relation.tail_entity.id, target_id, path, depth + 1)
                    path.pop()
            
            visited.remove(current_id)
        
        dfs(start_entity_id, end_entity_id, [], 0)
        return paths
    
    def merge_entity(self, target_entity: Entity, source_entity: Entity) -> bool:
        """合并实体"""
        if target_entity.id not in self.entities or source_entity.id not in self.entities:
            return False
        
        # 合并属性和别名
        target_entity.aliases.extend(source_entity.aliases)
        target_entity.aliases = list(set(target_entity.aliases))  # 去重
        target_entity.properties.update(source_entity.properties)
        
        # 更新关系中的实体引用
        for relation in self.relations.values():
            if relation.head_entity.id == source_entity.id:
                relation.head_entity = target_entity
            if relation.tail_entity.id == source_entity.id:
                relation.tail_entity = target_entity
        
        # 删除源实体
        self.remove_entity(source_entity.id)
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        entity_type_counts = {}
        for entity_type in EntityType:
            count = len(self.get_entities_by_type(entity_type))
            if count > 0:
                entity_type_counts[entity_type.value] = count
        
        relation_type_counts = {}
        for relation_type in RelationType:
            count = len(self.get_relations_by_type(relation_type))
            if count > 0:
                relation_type_counts[relation_type.value] = count
        
        return {
            'total_entities': len(self.entities),
            'total_relations': len(self.relations),
            'entity_types': entity_type_counts,
            'relation_types': relation_type_counts,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def _index_entity(self, entity: Entity):
        """索引实体"""
        entity_type = entity.entity_type.value
        if entity_type not in self.entity_index:
            self.entity_index[entity_type] = set()
        self.entity_index[entity_type].add(entity.id)
    
    def _unindex_entity(self, entity: Entity):
        """取消实体索引"""
        entity_type = entity.entity_type.value
        if entity_type in self.entity_index:
            self.entity_index[entity_type].discard(entity.id)
    
    def _index_relation(self, relation: Relation):
        """索引关系"""
        relation_type = relation.relation_type.value
        if relation_type not in self.relation_index:
            self.relation_index[relation_type] = set()
        self.relation_index[relation_type].add(relation.id)
    
    def _unindex_relation(self, relation: Relation):
        """取消关系索引"""
        relation_type = relation.relation_type.value
        if relation_type in self.relation_index:
            self.relation_index[relation_type].discard(relation.id)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'entities': {eid: entity.to_dict() for eid, entity in self.entities.items()},
            'relations': {rid: relation.to_dict() for rid, relation in self.relations.items()},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraph':
        """从字典创建知识图谱"""
        graph = cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', '')
        )
        
        # 恢复实体
        entities_data = data.get('entities', {})
        for entity_data in entities_data.values():
            entity = Entity.from_dict(entity_data)
            graph.add_entity(entity)
        
        # 恢复关系
        relations_data = data.get('relations', {})
        for relation_data in relations_data.values():
            relation = Relation.from_dict(relation_data, graph.entities)
            if relation.head_entity and relation.tail_entity:
                graph.add_relation(relation)
        
        if 'created_at' in data:
            graph.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            graph.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return graph