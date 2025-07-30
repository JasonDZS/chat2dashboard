"""
实体抽取器模块
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
import re
import logging

from ..entities import Entity
from ..types import EntityType

logger = logging.getLogger(__name__)


class BaseEntityExtractor(ABC):
    """实体抽取器基类"""
    
    def __init__(self):
        self.entity_patterns = {}
        self.confidence_threshold = 0.5
        self.stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    @abstractmethod
    def extract_from_text(self, text: str, context: Dict[str, Any] = None) -> List[Entity]:
        """
        从文本中抽取实体
        
        Args:
            text: 输入文本
            context: 上下文信息
            
        Returns:
            List[Entity]: 抽取的实体列表
        """
        pass
    
    @abstractmethod
    def extract_from_database(self, schema: Dict[str, Any]) -> List[Entity]:
        """
        从数据库模式中抽取实体
        
        Args:
            schema: 数据库模式信息
            
        Returns:
            List[Entity]: 抽取的实体列表
        """
        pass
    
    def normalize_entity(self, entity: Entity) -> Entity:
        """
        实体标准化
        
        Args:
            entity: 原始实体
            
        Returns:
            Entity: 标准化后的实体
        """
        # 名称标准化
        entity.name = entity.name.strip().lower()
        
        # 别名去重和标准化
        normalized_aliases = []
        for alias in entity.aliases:
            normalized_alias = alias.strip().lower()
            if normalized_alias and normalized_alias not in normalized_aliases:
                normalized_aliases.append(normalized_alias)
        entity.aliases = normalized_aliases
        
        return entity
    
    def deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        实体去重
        
        Args:
            entities: 实体列表
            
        Returns:
            List[Entity]: 去重后的实体列表
        """
        unique_entities = {}
        name_to_entity = {}
        
        for entity in entities:
            # 基于名称的精确匹配
            normalized_name = entity.name.lower().strip()
            
            if normalized_name in name_to_entity:
                # 合并实体信息
                existing_entity = name_to_entity[normalized_name]
                existing_entity.aliases.extend(entity.aliases)
                existing_entity.aliases = list(set(existing_entity.aliases))
                existing_entity.properties.update(entity.properties)
                
                # 保留更高置信度的实体
                if entity.confidence > existing_entity.confidence:
                    existing_entity.confidence = entity.confidence
                    existing_entity.description = entity.description or existing_entity.description
            else:
                name_to_entity[normalized_name] = entity
                unique_entities[entity.id] = entity
        
        return list(unique_entities.values())
    
    def _calculate_entity_confidence(self, entity_name: str, context: Dict[str, Any] = None) -> float:
        """计算实体置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于长度的置信度调整
        if len(entity_name) > 1:
            confidence += 0.1
        if len(entity_name) > 3:
            confidence += 0.1
        
        # 基于大小写的置信度调整
        if entity_name[0].isupper():
            confidence += 0.1
        
        # 基于停用词的置信度调整
        if entity_name.lower() in self.stopwords:
            confidence -= 0.3
        
        return min(1.0, max(0.0, confidence))


class TextEntityExtractor(BaseEntityExtractor):
    """文本实体抽取器"""
    
    def __init__(self):
        super().__init__()
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化实体识别模式"""
        self.entity_patterns = {
            EntityType.PERSON: [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # 人名模式
                r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.? [A-Z][a-z]+\b'  # 称谓+名字
            ],
            EntityType.ORGANIZATION: [
                r'\b[A-Z][a-zA-Z\s&]+ (?:Inc|Corp|Ltd|LLC|Company|Organization)\b',
                r'\b[A-Z][A-Z\s]+\b'  # 全大写可能是组织
            ],
            EntityType.LOCATION: [
                r'\b[A-Z][a-z]+ (?:City|State|Country|Province|District)\b',
                r'\bin [A-Z][a-z]+\b'  # 地点介词短语
            ],
            EntityType.CONCEPT: [
                r'\b[a-z]+ (?:concept|theory|principle|method|approach)\b'
            ]
        }
    
    def extract_from_text(self, text: str, context: Dict[str, Any] = None) -> List[Entity]:
        """从文本中抽取实体"""
        entities = []
        
        try:
            # 基于正则表达式的实体抽取
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entity_name = match.group().strip()
                        if len(entity_name) < 2:
                            continue
                        
                        confidence = self._calculate_entity_confidence(entity_name, context)
                        if confidence < self.confidence_threshold:
                            continue
                        
                        entity = Entity(
                            name=entity_name,
                            entity_type=entity_type,
                            confidence=confidence,
                            source='text_extraction',
                            properties={
                                'position': match.span(),
                                'context': text[max(0, match.start()-50):match.end()+50]
                            }
                        )
                        
                        entities.append(entity)
            
            # 基于关键词的概念实体抽取
            concept_keywords = self._extract_concept_keywords(text)
            for keyword in concept_keywords:
                entity = Entity(
                    name=keyword,
                    entity_type=EntityType.CONCEPT,
                    confidence=0.6,
                    source='keyword_extraction'
                )
                entities.append(entity)
            
            return self.deduplicate_entities(entities)
        
        except Exception as e:
            logger.error(f"Error extracting entities from text: {e}")
            return []
    
    def extract_from_database(self, schema: Dict[str, Any]) -> List[Entity]:
        """从数据库模式中抽取实体"""
        entities = []
        
        try:
            # 数据库实体
            if 'database_name' in schema:
                db_entity = Entity(
                    name=schema['database_name'],
                    entity_type=EntityType.DATABASE,
                    confidence=1.0,
                    source='database_schema',
                    description=f"Database: {schema['database_name']}"
                )
                entities.append(db_entity)
            
            # 表实体
            tables = schema.get('tables', [])
            for table in tables:
                table_name = table.get('name', '')
                if table_name:
                    table_entity = Entity(
                        name=table_name,
                        entity_type=EntityType.TABLE,
                        confidence=1.0,
                        source='database_schema',
                        description=table.get('comment', f"Table: {table_name}"),
                        properties={
                            'row_count': table.get('row_count', 0),
                            'columns': [col.get('name') for col in table.get('columns', [])]
                        }
                    )
                    entities.append(table_entity)
                    
                    # 列实体
                    columns = table.get('columns', [])
                    for column in columns:
                        column_name = column.get('name', '')
                        if column_name:
                            column_entity = Entity(
                                name=f"{table_name}.{column_name}",
                                entity_type=EntityType.COLUMN,
                                confidence=1.0,
                                source='database_schema',
                                description=column.get('comment', f"Column: {column_name}"),
                                properties={
                                    'table': table_name,
                                    'data_type': column.get('type', ''),
                                    'nullable': column.get('nullable', True),
                                    'primary_key': column.get('primary_key', False),
                                    'foreign_key': column.get('foreign_key', False)
                                }
                            )
                            entities.append(column_entity)
            
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities from database schema: {e}")
            return []
    
    def _extract_concept_keywords(self, text: str) -> List[str]:
        """抽取概念关键词"""
        # 简单的关键词抽取，基于词频和位置
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # 过滤停用词
        keywords = [word for word in words if word not in self.stopwords]
        
        # 统计词频
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回高频词作为概念
        concept_keywords = [word for word, freq in word_freq.items() if freq >= 2]
        return concept_keywords[:10]  # 限制数量


class DatabaseEntityExtractor(BaseEntityExtractor):
    """数据库实体抽取器"""
    
    def __init__(self):
        super().__init__()
        self.table_prefixes = {'tbl_', 'tb_', 't_'}
        self.common_columns = {'id', 'created_at', 'updated_at', 'deleted_at'}
    
    def extract_from_text(self, text: str, context: Dict[str, Any] = None) -> List[Entity]:
        """数据库抽取器不处理文本"""
        return []
    
    def extract_from_database(self, schema: Dict[str, Any]) -> List[Entity]:
        """从数据库模式中抽取实体"""
        entities = []
        
        try:
            # 抽取数据库实体
            if 'database_name' in schema:
                db_entity = Entity(
                    name=schema['database_name'],
                    entity_type=EntityType.DATABASE,
                    confidence=1.0,
                    source='database_extraction',
                    description=f"Database: {schema.get('description', schema['database_name'])}"
                )
                entities.append(db_entity)
            
            # 抽取表和列实体
            tables = schema.get('tables', [])
            for table in tables:
                table_entities = self._extract_table_entities(table)
                entities.extend(table_entities)
            
            # 抽取业务概念实体
            business_entities = self._extract_business_concepts(schema)
            entities.extend(business_entities)
            
            return entities
        
        except Exception as e:
            logger.error(f"Error in database entity extraction: {e}")
            return []
    
    def _extract_table_entities(self, table: Dict[str, Any]) -> List[Entity]:
        """抽取表相关实体"""
        entities = []
        table_name = table.get('name', '')
        
        if not table_name:
            return entities
        
        # 表实体
        table_entity = Entity(
            name=table_name,
            entity_type=EntityType.TABLE,
            confidence=1.0,
            source='database_extraction',
            description=table.get('comment', f"数据表: {table_name}"),
            properties={
                'schema': table.get('schema', ''),
                'row_count': table.get('row_count', 0),
                'size_mb': table.get('size_mb', 0),
                'engine': table.get('engine', ''),
                'created_at': table.get('created_at', ''),
                'column_count': len(table.get('columns', []))
            }
        )
        
        # 添加表名别名（去掉前缀）
        clean_name = self._clean_table_name(table_name)
        if clean_name != table_name:
            table_entity.add_alias(clean_name)
        
        entities.append(table_entity)
        
        # 列实体
        columns = table.get('columns', [])
        for column in columns:
            column_entities = self._extract_column_entities(table_name, column)
            entities.extend(column_entities)
        
        return entities
    
    def _extract_column_entities(self, table_name: str, column: Dict[str, Any]) -> List[Entity]:
        """抽取列实体"""
        entities = []
        column_name = column.get('name', '')
        
        if not column_name:
            return entities
        
        # 跳过通用列
        if column_name.lower() in self.common_columns:
            return entities
        
        full_column_name = f"{table_name}.{column_name}"
        
        column_entity = Entity(
            name=full_column_name,
            entity_type=EntityType.COLUMN,
            confidence=1.0,
            source='database_extraction',
            description=column.get('comment', f"数据列: {column_name}"),
            properties={
                'table': table_name,
                'column': column_name,
                'data_type': column.get('type', ''),
                'max_length': column.get('max_length'),
                'nullable': column.get('nullable', True),
                'default_value': column.get('default'),
                'primary_key': column.get('primary_key', False),
                'foreign_key': column.get('foreign_key', {}),
                'unique': column.get('unique', False),
                'indexed': column.get('indexed', False)
            }
        )
        
        # 添加列名别名
        column_entity.add_alias(column_name)
        
        entities.append(column_entity)
        return entities
    
    def _extract_business_concepts(self, schema: Dict[str, Any]) -> List[Entity]:
        """抽取业务概念实体"""
        entities = []
        
        # 基于表名推断业务概念
        tables = schema.get('tables', [])
        business_concepts = set()
        
        for table in tables:
            table_name = table.get('name', '')
            clean_name = self._clean_table_name(table_name)
            
            # 从表名推断业务概念
            concepts = self._infer_business_concepts(clean_name)
            business_concepts.update(concepts)
        
        # 创建业务概念实体
        for concept in business_concepts:
            concept_entity = Entity(
                name=concept,
                entity_type=EntityType.CONCEPT,
                confidence=0.7,
                source='business_inference',
                description=f"业务概念: {concept}"
            )
            entities.append(concept_entity)
        
        return entities
    
    def _clean_table_name(self, table_name: str) -> str:
        """清理表名"""
        clean_name = table_name.lower()
        
        # 移除常见前缀
        for prefix in self.table_prefixes:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):]
                break
        
        return clean_name
    
    def _infer_business_concepts(self, table_name: str) -> Set[str]:
        """从表名推断业务概念"""
        concepts = set()
        
        # 简单的业务概念映射
        concept_mapping = {
            'user': 'User Management',
            'customer': 'Customer Management', 
            'order': 'Order Management',
            'product': 'Product Management',
            'inventory': 'Inventory Management',
            'payment': 'Payment Processing',
            'shipment': 'Shipping Management',
            'category': 'Category Management',
            'review': 'Review System',
            'cart': 'Shopping Cart',
            'wishlist': 'Wishlist Management'
        }
        
        for keyword, concept in concept_mapping.items():
            if keyword in table_name:
                concepts.add(concept)
        
        return concepts