"""
关系相关的数据结构和操作
"""
from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .types import RelationType
from .entities import Entity


@dataclass  
class Relation:
    """关系类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    head_entity: Entity = None
    tail_entity: Entity = None
    relation_type: RelationType = RelationType.RELATED_TO
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Relation):
            return self.id == other.id
        return False
    
    def add_property(self, key: str, value: Any):
        """添加属性"""
        self.properties[key] = value
    
    def get_property(self, key: str, default=None):
        """获取属性"""
        return self.properties.get(key, default)
    
    def is_valid(self) -> bool:
        """验证关系有效性"""
        return (self.head_entity is not None and 
                self.tail_entity is not None and
                self.head_entity != self.tail_entity)
    
    def reverse(self) -> 'Relation':
        """创建反向关系"""
        return Relation(
            head_entity=self.tail_entity,
            tail_entity=self.head_entity,
            relation_type=self._get_reverse_relation_type(),
            properties=self.properties.copy(),
            confidence=self.confidence,
            source=self.source
        )
    
    def _get_reverse_relation_type(self) -> RelationType:
        """获取反向关系类型"""
        reverse_map = {
            RelationType.CONTAINS: RelationType.BELONGS_TO,
            RelationType.BELONGS_TO: RelationType.CONTAINS,
            RelationType.REFERENCES: RelationType.REFERENCES,
            RelationType.SIMILAR_TO: RelationType.SIMILAR_TO,
            RelationType.SYNONYMS: RelationType.SYNONYMS,
        }
        return reverse_map.get(self.relation_type, self.relation_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'head_entity_id': self.head_entity.id if self.head_entity else None,
            'tail_entity_id': self.tail_entity.id if self.tail_entity else None,
            'relation_type': self.relation_type.value,
            'properties': self.properties,
            'confidence': self.confidence,
            'source': self.source,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], entities_map: Dict[str, Entity]) -> 'Relation':
        """从字典创建关系"""
        head_entity = entities_map.get(data.get('head_entity_id'))
        tail_entity = entities_map.get(data.get('tail_entity_id'))
        
        relation = cls(
            id=data.get('id', str(uuid.uuid4())),
            head_entity=head_entity,
            tail_entity=tail_entity,
            relation_type=RelationType(data.get('relation_type', RelationType.RELATED_TO.value)),
            properties=data.get('properties', {}),
            confidence=data.get('confidence', 1.0),
            source=data.get('source', '')
        )
        if 'created_at' in data:
            relation.created_at = datetime.fromisoformat(data['created_at'])
        return relation