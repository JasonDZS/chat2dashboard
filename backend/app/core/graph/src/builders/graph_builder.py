"""
知识图谱构建器模块
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

from ..entities import Entity
from ..relations import Relation
from ..graph import KnowledgeGraph
from ..extractors.entity_extractor import BaseEntityExtractor, TextEntityExtractor, DatabaseEntityExtractor
from ..extractors.relation_extractor import BaseRelationExtractor, TextRelationExtractor, DatabaseRelationExtractor

logger = logging.getLogger(__name__)


class BaseKnowledgeGraphBuilder(ABC):
    """知识图谱构建器基类"""
    
    def __init__(self):
        self.entity_extractor = None
        self.relation_extractor = None
        self.graph_storage = None
        self.merge_threshold = 0.8
    
    @abstractmethod
    def build_graph(self, 
                   texts: List[str] = None, 
                   database_schema: Dict[str, Any] = None,
                   graph_name: str = "knowledge_graph") -> KnowledgeGraph:
        """
        构建知识图谱
        
        Args:
            texts: 文本列表
            database_schema: 数据库模式
            graph_name: 图谱名称
            
        Returns:
            KnowledgeGraph: 构建的知识图谱
        """
        pass
    
    @abstractmethod
    def update_graph(self, graph: KnowledgeGraph, 
                    new_entities: List[Entity] = None,
                    new_relations: List[Relation] = None) -> KnowledgeGraph:
        """
        更新知识图谱
        
        Args:
            graph: 现有知识图谱
            new_entities: 新增实体
            new_relations: 新增关系
            
        Returns:
            KnowledgeGraph: 更新后的知识图谱
        """
        pass
    
    def merge_graphs(self, graphs: List[KnowledgeGraph]) -> KnowledgeGraph:
        """
        合并多个知识图谱
        
        Args:
            graphs: 待合并的图谱列表
            
        Returns:
            KnowledgeGraph: 合并后的图谱
        """
        if not graphs:
            return KnowledgeGraph()
        
        if len(graphs) == 1:
            return graphs[0]
        
        # 创建新的合并图谱
        merged_graph = KnowledgeGraph(name="merged_graph")
        all_entities = []
        all_relations = []
        
        # 收集所有实体和关系
        for graph in graphs:
            all_entities.extend(graph.entities.values())
            all_relations.extend(graph.relations.values())
        
        # 实体对齐和去重
        aligned_entities = self._align_entities(all_entities)
        
        # 添加实体到合并图谱
        entity_id_mapping = {}  # 原ID -> 新ID的映射
        for entity in aligned_entities:
            if merged_graph.add_entity(entity):
                entity_id_mapping[entity.id] = entity.id
        
        # 更新关系中的实体引用并添加到合并图谱
        for relation in all_relations:
            if (relation.head_entity.id in entity_id_mapping and 
                relation.tail_entity.id in entity_id_mapping):
                
                # 更新实体引用
                relation.head_entity = merged_graph.get_entity(entity_id_mapping[relation.head_entity.id])
                relation.tail_entity = merged_graph.get_entity(entity_id_mapping[relation.tail_entity.id])
                
                merged_graph.add_relation(relation)
        
        return merged_graph
    
    def validate_graph(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        验证知识图谱质量
        
        Args:
            graph: 待验证的知识图谱
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'statistics': graph.get_statistics(),
            'recommendations': []
        }
        
        # 检查实体和关系完整性
        integrity_issues = self._check_integrity(graph)
        validation_result['issues'].extend(integrity_issues)
        
        # 验证图连通性
        connectivity_issues = self._check_connectivity(graph)
        validation_result['issues'].extend(connectivity_issues)
        
        # 检测孤立节点
        isolated_nodes = self._find_isolated_nodes(graph)
        if isolated_nodes:
            validation_result['issues'].append({
                'type': 'isolated_nodes',
                'count': len(isolated_nodes),
                'nodes': isolated_nodes[:10]  # 只显示前10个
            })
        
        # 检测循环依赖
        cycles = self._detect_cycles(graph)
        if cycles:
            validation_result['issues'].append({
                'type': 'cycles',
                'count': len(cycles),
                'cycles': cycles[:5]  # 只显示前5个
            })
        
        # 生成建议
        recommendations = self._generate_recommendations(graph, validation_result['issues'])
        validation_result['recommendations'] = recommendations
        
        # 设置整体有效性
        validation_result['valid'] = len([issue for issue in validation_result['issues'] 
                                        if issue.get('severity', 'medium') == 'high']) == 0
        
        return validation_result
    
    def _align_entities(self, entities: List[Entity]) -> List[Entity]:
        """实体对齐和去重"""
        aligned_entities = []
        processed_names = set()
        
        for entity in entities:
            # 标准化实体名称
            normalized_name = entity.name.lower().strip()
            
            if normalized_name in processed_names:
                # 查找已存在的实体进行合并
                existing_entity = next(
                    (e for e in aligned_entities if e.name.lower().strip() == normalized_name), 
                    None
                )
                if existing_entity:
                    self._merge_entity_attributes(existing_entity, entity)
            else:
                aligned_entities.append(entity)
                processed_names.add(normalized_name)
        
        return aligned_entities
    
    def _merge_entity_attributes(self, target_entity: Entity, source_entity: Entity):
        """合并实体属性"""
        # 合并别名
        target_entity.aliases.extend(source_entity.aliases)
        target_entity.aliases = list(set(target_entity.aliases))
        
        # 合并属性
        target_entity.properties.update(source_entity.properties)
        
        # 更新置信度（取较高值）
        if source_entity.confidence > target_entity.confidence:
            target_entity.confidence = source_entity.confidence
            target_entity.description = source_entity.description or target_entity.description
    
    def _check_integrity(self, graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """检查图谱完整性"""
        issues = []
        
        # 检查关系中的实体引用
        for relation in graph.relations.values():
            if not relation.head_entity or relation.head_entity.id not in graph.entities:
                issues.append({
                    'type': 'missing_head_entity',
                    'relation_id': relation.id,
                    'severity': 'high'
                })
            
            if not relation.tail_entity or relation.tail_entity.id not in graph.entities:
                issues.append({
                    'type': 'missing_tail_entity',
                    'relation_id': relation.id,
                    'severity': 'high'
                })
        
        return issues
    
    def _check_connectivity(self, graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """检查图连通性"""
        issues = []
        
        if not graph.entities:
            return issues
        
        # 使用DFS检查连通性
        visited = set()
        components = []
        
        for entity_id in graph.entities:
            if entity_id not in visited:
                component = self._dfs_component(graph, entity_id, visited)
                components.append(component)
        
        if len(components) > 1:
            issues.append({
                'type': 'disconnected_components',
                'count': len(components),
                'component_sizes': [len(comp) for comp in components],
                'severity': 'medium'
            })
        
        return issues
    
    def _dfs_component(self, graph: KnowledgeGraph, start_entity_id: str, visited: set) -> List[str]:
        """DFS遍历连通分量"""
        component = []
        stack = [start_entity_id]
        
        while stack:
            entity_id = stack.pop()
            if entity_id in visited:
                continue
            
            visited.add(entity_id)
            component.append(entity_id)
            
            # 找邻居节点
            neighbors = graph.get_neighbors(entity_id)
            for neighbor in neighbors:
                if neighbor.id not in visited:
                    stack.append(neighbor.id)
        
        return component
    
    def _find_isolated_nodes(self, graph: KnowledgeGraph) -> List[str]:
        """查找孤立节点"""
        isolated_nodes = []
        
        for entity_id, entity in graph.entities.items():
            relations = graph.get_entity_relations(entity_id)
            if not relations:
                isolated_nodes.append(entity_id)
        
        return isolated_nodes
    
    def _detect_cycles(self, graph: KnowledgeGraph) -> List[List[str]]:
        """检测循环依赖"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs_cycle(entity_id: str, path: List[str]) -> bool:
            if entity_id in rec_stack:
                # 找到循环
                cycle_start = path.index(entity_id)
                cycle = path[cycle_start:] + [entity_id]
                cycles.append(cycle)
                return True
            
            if entity_id in visited:
                return False
            
            visited.add(entity_id)
            rec_stack.add(entity_id)
            path.append(entity_id)
            
            # 检查出边
            relations = graph.get_entity_relations(entity_id, direction='out')
            for relation in relations:
                if dfs_cycle(relation.tail_entity.id, path):
                    break
            
            path.pop()
            rec_stack.remove(entity_id)
            return False
        
        for entity_id in graph.entities:
            if entity_id not in visited:
                dfs_cycle(entity_id, [])
        
        return cycles
    
    def _generate_recommendations(self, graph: KnowledgeGraph, issues: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于问题类型生成建议
        issue_types = [issue['type'] for issue in issues]
        
        if 'missing_head_entity' in issue_types or 'missing_tail_entity' in issue_types:
            recommendations.append("清理无效的关系引用，确保所有关系的头尾实体都存在")
        
        if 'disconnected_components' in issue_types:
            recommendations.append("考虑添加连接不同组件的关系，提高图谱连通性")
        
        if 'isolated_nodes' in issue_types:
            recommendations.append("为孤立节点添加相关关系，或考虑删除无关的孤立实体")
        
        if 'cycles' in issue_types:
            recommendations.append("检查循环依赖的合理性，必要时调整关系类型或方向")
        
        # 基于统计信息生成建议
        stats = graph.get_statistics()
        entity_count = stats['total_entities']
        relation_count = stats['total_relations']
        
        if relation_count == 0:
            recommendations.append("图谱缺少关系，建议添加实体间的关联")
        elif relation_count / entity_count < 0.5:
            recommendations.append("关系密度较低，考虑挖掘更多实体间的关联")
        elif relation_count / entity_count > 5:
            recommendations.append("关系密度较高，可能存在冗余关系，建议清理")
        
        return recommendations


class StandardGraphBuilder(BaseKnowledgeGraphBuilder):
    """标准知识图谱构建器"""
    
    def __init__(self):
        super().__init__()
        self.text_entity_extractor = TextEntityExtractor()
        self.db_entity_extractor = DatabaseEntityExtractor()
        self.text_relation_extractor = TextRelationExtractor()
        self.db_relation_extractor = DatabaseRelationExtractor()
    
    def build_graph(self, 
                   texts: List[str] = None, 
                   database_schema: Dict[str, Any] = None,
                   graph_name: str = "knowledge_graph") -> KnowledgeGraph:
        """构建知识图谱"""
        try:
            # 创建新图谱
            graph = KnowledgeGraph(name=graph_name)
            all_entities = []
            all_relations = []
            
            # 从文本抽取实体和关系
            if texts:
                logger.info(f"Processing {len(texts)} text documents")
                for text in texts:
                    # 抽取实体
                    text_entities = self.text_entity_extractor.extract_from_text(text)
                    all_entities.extend(text_entities)
                    
                    # 抽取关系
                    text_relations = self.text_relation_extractor.extract_from_text(text, text_entities)
                    all_relations.extend(text_relations)
            
            # 从数据库模式抽取实体和关系
            if database_schema:
                logger.info("Processing database schema")
                # 抽取数据库实体
                db_entities = self.db_entity_extractor.extract_from_database(database_schema)
                all_entities.extend(db_entities)
                
                # 抽取数据库关系
                db_relations = self.db_relation_extractor.extract_from_database(database_schema, db_entities)
                all_relations.extend(db_relations)
            
            # 实体去重和标准化
            logger.info(f"Deduplicating {len(all_entities)} entities")
            unique_entities = self.text_entity_extractor.deduplicate_entities(all_entities)
            
            # 添加实体到图谱
            for entity in unique_entities:
                graph.add_entity(entity)
            
            # 过滤和添加关系
            logger.info(f"Processing {len(all_relations)} relations")
            valid_relations = []
            for relation in all_relations:
                # 确保关系的实体存在于图谱中
                if (relation.head_entity.id in graph.entities and 
                    relation.tail_entity.id in graph.entities):
                    # 更新关系中的实体引用
                    relation.head_entity = graph.get_entity(relation.head_entity.id)
                    relation.tail_entity = graph.get_entity(relation.tail_entity.id)
                    valid_relations.append(relation)
            
            # 添加关系到图谱
            for relation in valid_relations:
                graph.add_relation(relation)
            
            # 推断隐式关系
            implicit_relations = self.text_relation_extractor.infer_implicit_relations(
                list(graph.entities.values()), 
                list(graph.relations.values())
            )
            
            for relation in implicit_relations:
                if (relation.head_entity.id in graph.entities and 
                    relation.tail_entity.id in graph.entities):
                    graph.add_relation(relation)
            
            logger.info(f"Graph built successfully: {len(graph.entities)} entities, {len(graph.relations)} relations")
            return graph
        
        except Exception as e:
            logger.error(f"Error building graph: {e}")
            raise
    
    def update_graph(self, graph: KnowledgeGraph, 
                    new_entities: List[Entity] = None,
                    new_relations: List[Relation] = None) -> KnowledgeGraph:
        """更新知识图谱"""
        try:
            # 添加新实体
            if new_entities:
                logger.info(f"Adding {len(new_entities)} new entities")
                for entity in new_entities:
                    if entity.id not in graph.entities:
                        graph.add_entity(entity)
                    else:
                        # 合并已存在实体的属性
                        existing_entity = graph.get_entity(entity.id)
                        self._merge_entity_attributes(existing_entity, entity)
            
            # 添加新关系
            if new_relations:
                logger.info(f"Adding {len(new_relations)} new relations")
                for relation in new_relations:
                    if relation.id not in graph.relations:
                        # 确保关系的实体存在
                        if (relation.head_entity.id in graph.entities and 
                            relation.tail_entity.id in graph.entities):
                            graph.add_relation(relation)
            
            # 更新图谱时间戳
            graph.updated_at = datetime.now()
            
            logger.info(f"Graph updated successfully: {len(graph.entities)} entities, {len(graph.relations)} relations")
            return graph
        
        except Exception as e:
            logger.error(f"Error updating graph: {e}")
            raise


class MultiSourceGraphBuilder(StandardGraphBuilder):
    """多源知识图谱构建器"""
    
    def __init__(self):
        super().__init__()
        self.source_weights = {
            'database_schema': 1.0,
            'text_extraction': 0.8,
            'keyword_extraction': 0.6,
            'inference': 0.4
        }
    
    def build_graph_from_multiple_sources(self, 
                                        sources: List[Dict[str, Any]],
                                        graph_name: str = "multi_source_graph") -> KnowledgeGraph:
        """
        从多个数据源构建知识图谱
        
        Args:
            sources: 数据源列表，每个源包含类型和数据
            graph_name: 图谱名称
            
        Returns:
            KnowledgeGraph: 构建的知识图谱
        """
        try:
            sub_graphs = []
            
            # 为每个数据源构建子图
            for i, source in enumerate(sources):
                source_type = source.get('type')
                source_data = source.get('data')
                source_name = source.get('name', f"source_{i}")
                
                logger.info(f"Processing source: {source_name} ({source_type})")
                
                if source_type == 'text':
                    texts = source_data if isinstance(source_data, list) else [source_data]
                    sub_graph = self.build_graph(texts=texts, graph_name=f"{graph_name}_{source_name}")
                elif source_type == 'database':
                    sub_graph = self.build_graph(database_schema=source_data, graph_name=f"{graph_name}_{source_name}")
                elif source_type == 'mixed':
                    texts = source_data.get('texts', [])
                    db_schema = source_data.get('database_schema')
                    sub_graph = self.build_graph(texts=texts, database_schema=db_schema, graph_name=f"{graph_name}_{source_name}")
                else:
                    logger.warning(f"Unknown source type: {source_type}")
                    continue
                
                # 应用源权重
                self._apply_source_weights(sub_graph, source.get('weight', 1.0))
                sub_graphs.append(sub_graph)
            
            # 合并所有子图
            if not sub_graphs:
                return KnowledgeGraph(name=graph_name)
            
            logger.info(f"Merging {len(sub_graphs)} sub-graphs")
            merged_graph = self.merge_graphs(sub_graphs)
            merged_graph.name = graph_name
            
            return merged_graph
        
        except Exception as e:
            logger.error(f"Error building multi-source graph: {e}")
            raise
    
    def _apply_source_weights(self, graph: KnowledgeGraph, weight: float):
        """应用数据源权重"""
        # 调整实体置信度
        for entity in graph.entities.values():
            source_weight = self.source_weights.get(entity.source, 1.0)
            entity.confidence *= weight * source_weight
        
        # 调整关系置信度
        for relation in graph.relations.values():
            source_weight = self.source_weights.get(relation.source, 1.0)
            relation.confidence *= weight * source_weight