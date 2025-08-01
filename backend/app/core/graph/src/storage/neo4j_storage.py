"""
Neo4j图数据库存储实现
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .base_storage import GraphStorage
from ..entities import Entity
from ..relations import Relation
from ..graph import KnowledgeGraph
from ..types import EntityType, RelationType

logger = logging.getLogger(__name__)


class Neo4jStorage(GraphStorage):
    """Neo4j图数据库存储"""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        super().__init__()
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
    
    def connect(self) -> bool:
        """连接Neo4j数据库"""
        try:
            # 延迟导入neo4j，避免必须安装依赖
            try:
                from neo4j import GraphDatabase
            except ImportError:
                logger.error("neo4j package not installed. Please install it with: pip install neo4j")
                return False
            
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            
            # 测试连接
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            
            self.is_connected = True
            logger.info(f"Connected to Neo4j database at {self.uri}")
            
            # 创建索引
            self.create_indexes()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
            self.is_connected = False
            logger.info("Disconnected from Neo4j database")
    
    def create_indexes(self):
        """创建图数据库索引"""
        if not self.is_connected:
            return
        
        try:
            with self.driver.session(database=self.database) as session:
                # 为实体创建索引
                session.run("CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.id)")
                session.run("CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)")
                session.run("CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)")
                
                # 为关系创建索引
                session.run("CREATE INDEX relation_id_index IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.id)")
                session.run("CREATE INDEX relation_type_index IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.relation_type)")
                
                logger.info("Neo4j indexes created successfully")
        
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def save_graph(self, graph: KnowledgeGraph) -> bool:
        """保存知识图谱"""
        if not self.is_connected:
            logger.error("Not connected to Neo4j database")
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                # 开始事务
                with session.begin_transaction() as tx:
                    # 先清除已存在的图谱数据
                    self._clear_graph_data(tx, graph.id)
                    
                    # 保存图谱元数据
                    self._save_graph_metadata(tx, graph)
                    
                    # 保存实体
                    self._save_entities(tx, graph.id, list(graph.entities.values()))
                    
                    # 保存关系
                    self._save_relations(tx, graph.id, list(graph.relations.values()))
                    
                    tx.commit()
            
            logger.info(f"Graph {graph.id} saved successfully to Neo4j")
            return True
        
        except Exception as e:
            logger.error(f"Error saving graph to Neo4j: {e}")
            return False
    
    def load_graph(self, graph_id: str) -> Optional[KnowledgeGraph]:
        """加载知识图谱"""
        if not self.is_connected:
            logger.error("Not connected to Neo4j database")
            return None
        
        try:
            with self.driver.session(database=self.database) as session:
                # 加载图谱元数据
                graph_metadata = self._load_graph_metadata(session, graph_id)
                if not graph_metadata:
                    return None
                
                # 创建图谱对象
                graph = KnowledgeGraph(
                    id=graph_id,
                    name=graph_metadata.get('name', ''),
                    created_at=datetime.fromisoformat(graph_metadata.get('created_at', datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(graph_metadata.get('updated_at', datetime.now().isoformat()))
                )
                
                # 加载实体
                entities = self._load_entities(session, graph_id)
                for entity in entities:
                    graph.add_entity(entity)
                
                # 加载关系
                relations = self._load_relations(session, graph_id, graph.entities)
                for relation in relations:
                    graph.add_relation(relation)
                
                logger.info(f"Graph {graph_id} loaded successfully from Neo4j")
                return graph
        
        except Exception as e:
            logger.error(f"Error loading graph from Neo4j: {e}")
            return None
    
    def delete_graph(self, graph_id: str) -> bool:
        """删除知识图谱"""
        if not self.is_connected:
            logger.error("Not connected to Neo4j database")
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                with session.begin_transaction() as tx:
                    self._clear_graph_data(tx, graph_id)
                    tx.commit()
            
            logger.info(f"Graph {graph_id} deleted successfully from Neo4j")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting graph from Neo4j: {e}")
            return False
    
    def list_graphs(self) -> List[Dict[str, Any]]:
        """列出所有图谱"""
        if not self.is_connected:
            logger.error("Not connected to Neo4j database")
            return []
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("""
                    MATCH (g:Graph)
                    RETURN g.id as id, g.name as name, g.created_at as created_at, 
                           g.updated_at as updated_at
                    ORDER BY g.updated_at DESC
                """)
                
                graphs = []
                for record in result:
                    graphs.append({
                        'id': record['id'],
                        'name': record['name'],
                        'created_at': record['created_at'],
                        'updated_at': record['updated_at']
                    })
                
                return graphs
        
        except Exception as e:
            logger.error(f"Error listing graphs: {e}")
            return []
    
    def query_entities(self, conditions: Dict[str, Any]) -> List[Entity]:
        """查询实体"""
        if not self.is_connected:
            logger.error("Not connected to Neo4j database")
            return []
        
        try:
            with self.driver.session(database=self.database) as session:
                # 构建查询条件
                where_clauses = []
                params = {}
                
                if 'graph_id' in conditions:
                    where_clauses.append("e.graph_id = $graph_id")
                    params['graph_id'] = conditions['graph_id']
                
                if 'entity_type' in conditions:
                    where_clauses.append("e.entity_type = $entity_type")
                    params['entity_type'] = conditions['entity_type']
                
                if 'name' in conditions:
                    where_clauses.append("e.name CONTAINS $name")
                    params['name'] = conditions['name']
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = f"""
                    MATCH (e:Entity)
                    WHERE {where_clause}
                    RETURN e
                    LIMIT {conditions.get('limit', 100)}
                """
                
                result = session.run(query, params)
                entities = []
                
                for record in result:
                    entity_data = dict(record['e'])
                    entity = self._record_to_entity(entity_data)
                    entities.append(entity)
                
                return entities
        
        except Exception as e:
            logger.error(f"Error querying entities: {e}")
            return []
    
    def query_relations(self, 
                       head_entity: str = None, 
                       tail_entity: str = None,
                       relation_type: RelationType = None) -> List[Relation]:
        """查询关系"""
        if not self.is_connected:
            logger.error("Not connected to Neo4j database")
            return []
        
        try:
            with self.driver.session(database=self.database) as session:
                # 构建查询
                where_clauses = []
                params = {}
                
                if head_entity:
                    where_clauses.append("head.id = $head_entity")
                    params['head_entity'] = head_entity
                
                if tail_entity:
                    where_clauses.append("tail.id = $tail_entity")
                    params['tail_entity'] = tail_entity
                
                if relation_type:
                    where_clauses.append("r.relation_type = $relation_type")
                    params['relation_type'] = relation_type.value
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = f"""
                    MATCH (head:Entity)-[r:RELATION]->(tail:Entity)
                    WHERE {where_clause}
                    RETURN head, r, tail
                    LIMIT 100
                """
                
                result = session.run(query, params)
                relations = []
                
                for record in result:
                    head_entity = self._record_to_entity(dict(record['head']))
                    tail_entity = self._record_to_entity(dict(record['tail']))
                    relation_data = dict(record['r'])
                    
                    relation = self._record_to_relation(relation_data, head_entity, tail_entity)
                    relations.append(relation)
                
                return relations
        
        except Exception as e:
            logger.error(f"Error querying relations: {e}")
            return []
    
    def add_entity(self, graph_id: str, entity: Entity) -> bool:
        """添加实体"""
        if not self.is_connected:
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                self._save_entities(session, graph_id, [entity])
            return True
        except Exception as e:
            logger.error(f"Error adding entity: {e}")
            return False
    
    def add_relation(self, graph_id: str, relation: Relation) -> bool:
        """添加关系"""
        if not self.is_connected:
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                self._save_relations(session, graph_id, [relation])
            return True
        except Exception as e:
            logger.error(f"Error adding relation: {e}")
            return False
    
    def update_entity(self, graph_id: str, entity: Entity) -> bool:
        """更新实体"""
        return self.add_entity(graph_id, entity)  # Neo4j的MERGE会处理更新
    
    def update_relation(self, graph_id: str, relation: Relation) -> bool:
        """更新关系"""
        return self.add_relation(graph_id, relation)  # Neo4j的MERGE会处理更新
    
    def remove_entity(self, graph_id: str, entity_id: str) -> bool:
        """删除实体"""
        if not self.is_connected:
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                session.run("""
                    MATCH (e:Entity {id: $entity_id, graph_id: $graph_id})
                    DETACH DELETE e
                """, entity_id=entity_id, graph_id=graph_id)
            return True
        except Exception as e:
            logger.error(f"Error removing entity: {e}")
            return False
    
    def remove_relation(self, graph_id: str, relation_id: str) -> bool:
        """删除关系"""
        if not self.is_connected:
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                session.run("""
                    MATCH ()-[r:RELATION {id: $relation_id, graph_id: $graph_id}]-()
                    DELETE r
                """, relation_id=relation_id, graph_id=graph_id)
            return True
        except Exception as e:
            logger.error(f"Error removing relation: {e}")
            return False
    
    def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        if not self.is_connected:
            logger.error("Not connected to Neo4j database")
            return []
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                records = []
                
                for record in result:
                    records.append(dict(record))
                
                return records
        
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return []
    
    def _clear_graph_data(self, tx, graph_id: str):
        """清除图谱数据"""
        # 删除关系
        tx.run("MATCH ()-[r:RELATION {graph_id: $graph_id}]-() DELETE r", graph_id=graph_id)
        # 删除实体
        tx.run("MATCH (e:Entity {graph_id: $graph_id}) DELETE e", graph_id=graph_id)
        # 删除图谱元数据
        tx.run("MATCH (g:Graph {id: $graph_id}) DELETE g", graph_id=graph_id)
    
    def _save_graph_metadata(self, tx, graph: KnowledgeGraph):
        """保存图谱元数据"""
        tx.run("""
            MERGE (g:Graph {id: $id})
            SET g.name = $name,
                g.created_at = $created_at,
                g.updated_at = $updated_at
        """, 
        id=graph.id,
        name=graph.name,
        created_at=graph.created_at.isoformat(),
        updated_at=graph.updated_at.isoformat())
    
    def _save_entities(self, tx, graph_id: str, entities: List[Entity]):
        """保存实体"""
        for entity in entities:
            tx.run("""
                MERGE (e:Entity {id: $id})
                SET e.graph_id = $graph_id,
                    e.name = $name,
                    e.entity_type = $entity_type,
                    e.description = $description,
                    e.properties = $properties,
                    e.aliases = $aliases,
                    e.confidence = $confidence,
                    e.source = $source,
                    e.created_at = $created_at
            """,
            id=entity.id,
            graph_id=graph_id,
            name=entity.name,
            entity_type=entity.entity_type.value,
            description=entity.description,
            properties=entity.properties,
            aliases=entity.aliases,
            confidence=entity.confidence,
            source=entity.source,
            created_at=entity.created_at.isoformat())
    
    def _save_relations(self, tx, graph_id: str, relations: List[Relation]):
        """保存关系"""
        for relation in relations:
            tx.run("""
                MATCH (head:Entity {id: $head_id})
                MATCH (tail:Entity {id: $tail_id})
                MERGE (head)-[r:RELATION {id: $id}]->(tail)
                SET r.graph_id = $graph_id,
                    r.relation_type = $relation_type,
                    r.properties = $properties,
                    r.confidence = $confidence,
                    r.source = $source,
                    r.created_at = $created_at
            """,
            id=relation.id,
            graph_id=graph_id,
            head_id=relation.head_entity.id,
            tail_id=relation.tail_entity.id,
            relation_type=relation.relation_type.value,
            properties=relation.properties,
            confidence=relation.confidence,
            source=relation.source,
            created_at=relation.created_at.isoformat())
    
    def _load_graph_metadata(self, session, graph_id: str) -> Optional[Dict[str, Any]]:
        """加载图谱元数据"""
        result = session.run("MATCH (g:Graph {id: $id}) RETURN g", id=graph_id)
        record = result.single()
        
        if record:
            return dict(record['g'])
        return None
    
    def _load_entities(self, session, graph_id: str) -> List[Entity]:
        """加载实体"""
        result = session.run("MATCH (e:Entity {graph_id: $graph_id}) RETURN e", graph_id=graph_id)
        entities = []
        
        for record in result:
            entity_data = dict(record['e'])
            entity = self._record_to_entity(entity_data)
            entities.append(entity)
        
        return entities
    
    def _load_relations(self, session, graph_id: str, entities: Dict[str, Entity]) -> List[Relation]:
        """加载关系"""
        result = session.run("""
            MATCH (head:Entity)-[r:RELATION {graph_id: $graph_id}]->(tail:Entity)
            RETURN head.id as head_id, tail.id as tail_id, r
        """, graph_id=graph_id)
        
        relations = []
        
        for record in result:
            head_entity = entities.get(record['head_id'])
            tail_entity = entities.get(record['tail_id'])
            
            if head_entity and tail_entity:
                relation_data = dict(record['r'])
                relation = self._record_to_relation(relation_data, head_entity, tail_entity)
                relations.append(relation)
        
        return relations
    
    def _record_to_entity(self, record: Dict[str, Any]) -> Entity:
        """将数据库记录转换为实体对象"""
        return Entity(
            id=record.get('id', ''),
            name=record.get('name', ''),
            entity_type=EntityType(record.get('entity_type', EntityType.UNKNOWN.value)),
            description=record.get('description', ''),
            properties=record.get('properties', {}),
            aliases=record.get('aliases', []),
            confidence=record.get('confidence', 1.0),
            source=record.get('source', ''),
            created_at=datetime.fromisoformat(record.get('created_at', datetime.now().isoformat()))
        )
    
    def _record_to_relation(self, record: Dict[str, Any], head_entity: Entity, tail_entity: Entity) -> Relation:
        """将数据库记录转换为关系对象"""
        return Relation(
            id=record.get('id', ''),
            head_entity=head_entity,
            tail_entity=tail_entity,
            relation_type=RelationType(record.get('relation_type', RelationType.RELATED_TO.value)),
            properties=record.get('properties', {}),
            confidence=record.get('confidence', 1.0),
            source=record.get('source', ''),
            created_at=datetime.fromisoformat(record.get('created_at', datetime.now().isoformat()))
        )