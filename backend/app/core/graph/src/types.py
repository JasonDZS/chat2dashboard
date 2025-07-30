"""
图谱类型定义和枚举
"""
from enum import Enum


class EntityType(Enum):
    """实体类型枚举"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    TABLE = "table"
    COLUMN = "column"
    DATABASE = "database"
    DOCUMENT = "document"
    KEYWORD = "keyword"
    UNKNOWN = "unknown"


class RelationType(Enum):
    """关系类型枚举"""
    CONTAINS = "contains"          # 包含关系
    BELONGS_TO = "belongs_to"      # 属于关系
    REFERENCES = "references"      # 引用关系
    SIMILAR_TO = "similar_to"      # 相似关系
    RELATED_TO = "related_to"      # 相关关系
    DEPENDS_ON = "depends_on"      # 依赖关系
    FOREIGN_KEY = "foreign_key"    # 外键关系
    MENTIONS = "mentions"          # 提及关系
    DESCRIBES = "describes"        # 描述关系
    SYNONYMS = "synonyms"          # 同义词关系