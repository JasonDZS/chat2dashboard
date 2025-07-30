"""
关系抽取器模块
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Set
import re
import logging

from ..entities import Entity
from ..relations import Relation
from ..types import EntityType, RelationType

logger = logging.getLogger(__name__)


class BaseRelationExtractor(ABC):
    """关系抽取器基类"""
    
    def __init__(self):
        self.relation_patterns = {}
        self.dependency_parser = None
        self.confidence_threshold = 0.5
    
    @abstractmethod
    def extract_from_text(self, text: str, entities: List[Entity]) -> List[Relation]:
        """
        从文本中抽取实体关系
        
        Args:
            text: 输入文本
            entities: 已识别的实体列表
            
        Returns:
            List[Relation]: 抽取的关系列表
        """
        pass
    
    @abstractmethod
    def extract_from_database(self, schema: Dict[str, Any], entities: List[Entity]) -> List[Relation]:
        """
        从数据库模式中抽取关系
        
        Args:
            schema: 数据库模式信息
            entities: 数据库实体列表
            
        Returns:
            List[Relation]: 抽取的关系列表
        """
        pass
    
    def validate_relation(self, relation: Relation) -> bool:
        """
        验证关系有效性
        
        Args:
            relation: 待验证的关系
            
        Returns:
            bool: 关系是否有效
        """
        if not relation.is_valid():
            return False
        
        # 检查置信度阈值
        if relation.confidence < self.confidence_threshold:
            return False
        
        # 检查关系类型合理性
        if not self._is_relation_type_valid(relation):
            return False
        
        return True
    
    def infer_implicit_relations(self, entities: List[Entity], relations: List[Relation]) -> List[Relation]:
        """
        推断隐式关系
        
        Args:
            entities: 实体列表
            relations: 已知关系列表
            
        Returns:
            List[Relation]: 推断的隐式关系
        """
        implicit_relations = []
        
        # 基于传递性推断关系
        transitive_relations = self._infer_transitive_relations(relations)
        implicit_relations.extend(transitive_relations)
        
        # 基于对称性推断关系
        symmetric_relations = self._infer_symmetric_relations(relations)
        implicit_relations.extend(symmetric_relations)
        
        # 基于层次结构推断关系
        hierarchical_relations = self._infer_hierarchical_relations(entities, relations)
        implicit_relations.extend(hierarchical_relations)
        
        return implicit_relations
    
    def _is_relation_type_valid(self, relation: Relation) -> bool:
        """检查关系类型合理性"""
        head_type = relation.head_entity.entity_type
        tail_type = relation.tail_entity.entity_type
        relation_type = relation.relation_type
        
        # 定义合理的关系类型组合
        valid_combinations = {
            (EntityType.DATABASE, EntityType.TABLE, RelationType.CONTAINS),
            (EntityType.TABLE, EntityType.COLUMN, RelationType.CONTAINS),
            (EntityType.COLUMN, EntityType.COLUMN, RelationType.FOREIGN_KEY),
            (EntityType.DOCUMENT, EntityType.CONCEPT, RelationType.MENTIONS),
            (EntityType.PERSON, EntityType.ORGANIZATION, RelationType.BELONGS_TO),
            (EntityType.CONCEPT, EntityType.CONCEPT, RelationType.SIMILAR_TO),
        }
        
        return (head_type, tail_type, relation_type) in valid_combinations
    
    def _infer_transitive_relations(self, relations: List[Relation]) -> List[Relation]:
        """基于传递性推断关系"""
        transitive_relations = []
        
        # A contains B, B contains C => A contains C
        for r1 in relations:
            if r1.relation_type == RelationType.CONTAINS:
                for r2 in relations:
                    if (r2.relation_type == RelationType.CONTAINS and 
                        r1.tail_entity.id == r2.head_entity.id):
                        
                        # 创建传递关系
                        transitive_relation = Relation(
                            head_entity=r1.head_entity,
                            tail_entity=r2.tail_entity,
                            relation_type=RelationType.CONTAINS,
                            confidence=min(r1.confidence, r2.confidence) * 0.8,
                            source='transitive_inference',
                            properties={'inferred_from': [r1.id, r2.id]}
                        )
                        transitive_relations.append(transitive_relation)
        
        return transitive_relations
    
    def _infer_symmetric_relations(self, relations: List[Relation]) -> List[Relation]:
        """基于对称性推断关系"""
        symmetric_relations = []
        
        symmetric_types = {RelationType.SIMILAR_TO, RelationType.SYNONYMS}
        
        for relation in relations:
            if relation.relation_type in symmetric_types:
                # 创建反向关系
                reverse_relation = Relation(
                    head_entity=relation.tail_entity,
                    tail_entity=relation.head_entity,
                    relation_type=relation.relation_type,
                    confidence=relation.confidence * 0.9,
                    source='symmetric_inference',
                    properties={'inferred_from': relation.id}
                )
                symmetric_relations.append(reverse_relation)
        
        return symmetric_relations
    
    def _infer_hierarchical_relations(self, entities: List[Entity], relations: List[Relation]) -> List[Relation]:
        """基于层次结构推断关系"""
        hierarchical_relations = []
        
        # 基于实体类型推断层次关系
        type_hierarchy = {
            EntityType.DATABASE: [EntityType.TABLE],
            EntityType.TABLE: [EntityType.COLUMN],
            EntityType.ORGANIZATION: [EntityType.PERSON],
            EntityType.DOCUMENT: [EntityType.CONCEPT, EntityType.KEYWORD]
        }
        
        entity_by_type = {}
        for entity in entities:
            if entity.entity_type not in entity_by_type:
                entity_by_type[entity.entity_type] = []
            entity_by_type[entity.entity_type].append(entity)
        
        for parent_type, child_types in type_hierarchy.items():
            parent_entities = entity_by_type.get(parent_type, [])
            
            for child_type in child_types:
                child_entities = entity_by_type.get(child_type, [])
                
                for parent_entity in parent_entities:
                    for child_entity in child_entities:
                        # 基于命名相似性推断层次关系
                        if self._is_hierarchically_related(parent_entity, child_entity):
                            hierarchical_relation = Relation(
                                head_entity=parent_entity,
                                tail_entity=child_entity,
                                relation_type=RelationType.CONTAINS,
                                confidence=0.6,
                                source='hierarchical_inference'
                            )
                            hierarchical_relations.append(hierarchical_relation)
        
        return hierarchical_relations
    
    def _is_hierarchically_related(self, parent_entity: Entity, child_entity: Entity) -> bool:
        """检查实体是否有层次关系"""
        parent_name = parent_entity.name.lower()
        child_name = child_entity.name.lower()
        
        # 检查名称包含关系
        if parent_name in child_name:
            return True
        
        # 检查属性中的关联信息
        if hasattr(child_entity, 'properties'):
            if 'table' in child_entity.properties:
                return child_entity.properties['table'] == parent_entity.name
        
        return False


class TextRelationExtractor(BaseRelationExtractor):
    """文本关系抽取器"""
    
    def __init__(self):
        super().__init__()
        self._init_relation_patterns()
    
    def _init_relation_patterns(self):
        """初始化关系模式"""
        self.relation_patterns = {
            RelationType.BELONGS_TO: [
                r'(.+?) (?:belongs to|is part of|works for) (.+)',
                r'(.+?) of (.+)',
            ],
            RelationType.CONTAINS: [
                r'(.+?) (?:contains|includes|has) (.+)',
                r'(.+?) with (.+)',
            ],
            RelationType.SIMILAR_TO: [
                r'(.+?) (?:is similar to|resembles|is like) (.+)',
                r'(.+?) and (.+?) are similar',
            ],
            RelationType.RELATED_TO: [
                r'(.+?) (?:is related to|relates to|associated with) (.+)',
                r'(.+?) and (.+?) are related',
            ],
            RelationType.DESCRIBES: [
                r'(.+?) (?:describes|explains|defines) (.+)',
                r'(.+?) is described by (.+)',
            ]
        }
    
    def extract_from_text(self, text: str, entities: List[Entity]) -> List[Relation]:
        """从文本中抽取实体关系"""
        relations = []
        
        try:
            # 创建实体名称到实体的映射
            entity_map = {entity.name.lower(): entity for entity in entities}
            
            # 基于模式匹配抽取关系
            for relation_type, patterns in self.relation_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        groups = match.groups()
                        if len(groups) >= 2:
                            head_name = groups[0].strip().lower()
                            tail_name = groups[1].strip().lower()
                            
                            # 查找对应的实体
                            head_entity = self._find_entity_by_name(head_name, entity_map)
                            tail_entity = self._find_entity_by_name(tail_name, entity_map)
                            
                            if head_entity and tail_entity:
                                relation = Relation(
                                    head_entity=head_entity,
                                    tail_entity=tail_entity,
                                    relation_type=relation_type,
                                    confidence=0.7,
                                    source='text_pattern_matching',
                                    properties={
                                        'pattern': pattern,
                                        'context': text[max(0, match.start()-50):match.end()+50]
                                    }
                                )
                                relations.append(relation)
            
            # 基于共现关系抽取
            cooccurrence_relations = self._extract_cooccurrence_relations(text, entities)
            relations.extend(cooccurrence_relations)
            
            # 过滤和验证关系
            valid_relations = [r for r in relations if self.validate_relation(r)]
            
            return valid_relations
        
        except Exception as e:
            logger.error(f"Error extracting relations from text: {e}")
            return []
    
    def extract_from_database(self, schema: Dict[str, Any], entities: List[Entity]) -> List[Relation]:
        """文本抽取器不处理数据库关系"""
        return []
    
    def _find_entity_by_name(self, name: str, entity_map: Dict[str, Entity]) -> Optional[Entity]:
        """根据名称查找实体"""
        # 精确匹配
        if name in entity_map:
            return entity_map[name]
        
        # 模糊匹配
        for entity_name, entity in entity_map.items():
            if name in entity_name or entity_name in name:
                return entity
            
            # 检查别名
            for alias in entity.aliases:
                if name == alias.lower() or name in alias.lower():
                    return entity
        
        return None
    
    def _extract_cooccurrence_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        """基于共现抽取关系"""
        relations = []
        
        # 在句子级别寻找共现实体
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip().lower()
            if not sentence:
                continue
            
            # 找到在同一句子中出现的实体
            sentence_entities = []
            for entity in entities:
                if (entity.name.lower() in sentence or 
                    any(alias.lower() in sentence for alias in entity.aliases)):
                    sentence_entities.append(entity)
            
            # 为共现实体创建关系
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    relation = Relation(
                        head_entity=entity1,
                        tail_entity=entity2,
                        relation_type=RelationType.RELATED_TO,
                        confidence=0.5,
                        source='cooccurrence',
                        properties={'sentence': sentence[:200]}
                    )
                    relations.append(relation)
        
        return relations


class DatabaseRelationExtractor(BaseRelationExtractor):
    """数据库关系抽取器"""
    
    def __init__(self):
        super().__init__()
    
    def extract_from_text(self, text: str, entities: List[Entity]) -> List[Relation]:
        """数据库抽取器不处理文本"""
        return []
    
    def extract_from_database(self, schema: Dict[str, Any], entities: List[Entity]) -> List[Relation]:
        """从数据库模式中抽取关系"""
        relations = []
        
        try:
            # 创建实体映射
            entity_map = {entity.name: entity for entity in entities}
            
            # 抽取数据库-表关系
            db_table_relations = self._extract_database_table_relations(schema, entity_map)
            relations.extend(db_table_relations)
            
            # 抽取表-列关系
            table_column_relations = self._extract_table_column_relations(schema, entity_map)
            relations.extend(table_column_relations)
            
            # 抽取外键关系
            foreign_key_relations = self._extract_foreign_key_relations(schema, entity_map)
            relations.extend(foreign_key_relations)
            
            # 抽取基于命名的语义关系
            semantic_relations = self._extract_semantic_relations(schema, entity_map)
            relations.extend(semantic_relations)
            
            return relations
        
        except Exception as e:
            logger.error(f"Error extracting database relations: {e}")
            return []
    
    def _extract_database_table_relations(self, schema: Dict[str, Any], entity_map: Dict[str, Entity]) -> List[Relation]:
        """抽取数据库-表关系"""
        relations = []
        
        database_name = schema.get('database_name')
        if not database_name or database_name not in entity_map:
            return relations
        
        database_entity = entity_map[database_name]
        tables = schema.get('tables', [])
        
        for table in tables:
            table_name = table.get('name')
            if table_name and table_name in entity_map:
                table_entity = entity_map[table_name]
                
                relation = Relation(
                    head_entity=database_entity,
                    tail_entity=table_entity,
                    relation_type=RelationType.CONTAINS,
                    confidence=1.0,
                    source='database_schema',
                    properties={
                        'schema_name': table.get('schema', ''),
                        'table_type': table.get('type', 'table')
                    }
                )
                relations.append(relation)
        
        return relations
    
    def _extract_table_column_relations(self, schema: Dict[str, Any], entity_map: Dict[str, Entity]) -> List[Relation]:
        """抽取表-列关系"""
        relations = []
        
        tables = schema.get('tables', [])
        for table in tables:
            table_name = table.get('name')
            if not table_name or table_name not in entity_map:
                continue
            
            table_entity = entity_map[table_name]
            columns = table.get('columns', [])
            
            for column in columns:
                column_name = column.get('name')
                if not column_name:
                    continue
                
                full_column_name = f"{table_name}.{column_name}"
                if full_column_name in entity_map:
                    column_entity = entity_map[full_column_name]
                    
                    relation = Relation(
                        head_entity=table_entity,
                        tail_entity=column_entity,
                        relation_type=RelationType.CONTAINS,
                        confidence=1.0,
                        source='database_schema',
                        properties={
                            'column_position': column.get('position', 0),
                            'is_primary_key': column.get('primary_key', False),
                            'is_nullable': column.get('nullable', True)
                        }
                    )
                    relations.append(relation)
        
        return relations
    
    def _extract_foreign_key_relations(self, schema: Dict[str, Any], entity_map: Dict[str, Entity]) -> List[Relation]:
        """抽取外键关系"""
        relations = []
        
        tables = schema.get('tables', [])
        for table in tables:
            table_name = table.get('name')
            columns = table.get('columns', [])
            
            for column in columns:
                foreign_key = column.get('foreign_key')
                if not foreign_key:
                    continue
                
                source_column_name = f"{table_name}.{column.get('name')}"
                target_table = foreign_key.get('table')
                target_column = foreign_key.get('column')
                target_column_name = f"{target_table}.{target_column}"
                
                if (source_column_name in entity_map and 
                    target_column_name in entity_map):
                    
                    source_entity = entity_map[source_column_name]
                    target_entity = entity_map[target_column_name]
                    
                    relation = Relation(
                        head_entity=source_entity,
                        tail_entity=target_entity,
                        relation_type=RelationType.FOREIGN_KEY,
                        confidence=1.0,
                        source='database_schema',
                        properties={
                            'constraint_name': foreign_key.get('constraint_name', ''),
                            'on_delete': foreign_key.get('on_delete', 'RESTRICT'),
                            'on_update': foreign_key.get('on_update', 'RESTRICT')
                        }
                    )
                    relations.append(relation)
        
        return relations
    
    def _extract_semantic_relations(self, schema: Dict[str, Any], entity_map: Dict[str, Entity]) -> List[Relation]:
        """抽取基于命名的语义关系"""
        relations = []
        
        # 基于表名相似性的关系
        tables = schema.get('tables', [])
        table_entities = []
        
        for table in tables:
            table_name = table.get('name')
            if table_name and table_name in entity_map:
                table_entities.append(entity_map[table_name])
        
        # 寻找相似的表名
        for i, table1 in enumerate(table_entities):
            for table2 in table_entities[i+1:]:
                similarity = self._calculate_name_similarity(table1.name, table2.name)
                if similarity > 0.6:
                    relation = Relation(
                        head_entity=table1,
                        tail_entity=table2,
                        relation_type=RelationType.SIMILAR_TO,
                        confidence=similarity,
                        source='name_similarity',
                        properties={'similarity_score': similarity}
                    )
                    relations.append(relation)
        
        return relations
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度"""
        name1 = name1.lower()
        name2 = name2.lower()
        
        # 简单的Jaccard相似度
        set1 = set(name1.split('_'))
        set2 = set(name2.split('_'))
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union