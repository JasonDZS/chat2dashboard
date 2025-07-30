"""
知识图谱工具函数
"""
from typing import Dict, List, Any, Optional, Tuple, Set
import json
import logging
from datetime import datetime

from .graph import KnowledgeGraph
from .entities import Entity
from .relations import Relation
from .types import EntityType, RelationType

logger = logging.getLogger(__name__)


def export_graph_to_cytoscape(graph: KnowledgeGraph) -> Dict[str, Any]:
    """
    将知识图谱导出为Cytoscape.js格式
    
    Args:
        graph: 知识图谱
        
    Returns:
        Dict[str, Any]: Cytoscape.js格式的数据
    """
    nodes = []
    edges = []
    
    # 转换实体为节点
    for entity in graph.entities.values():
        node = {
            'data': {
                'id': entity.id,
                'label': entity.name,
                'type': entity.entity_type.value,
                'description': entity.description,
                'confidence': entity.confidence,
                'source': entity.source
            },
            'classes': entity.entity_type.value
        }
        nodes.append(node)
    
    # 转换关系为边
    for relation in graph.relations.values():
        edge = {
            'data': {
                'id': relation.id,
                'source': relation.head_entity.id,
                'target': relation.tail_entity.id,
                'label': relation.relation_type.value,
                'type': relation.relation_type.value,
                'confidence': relation.confidence,
                'source_info': relation.source
            },
            'classes': relation.relation_type.value
        }
        edges.append(edge)
    
    return {
        'elements': {
            'nodes': nodes,
            'edges': edges
        },
        'graph_info': {
            'id': graph.id,
            'name': graph.name,
            'created_at': graph.created_at.isoformat(),
            'updated_at': graph.updated_at.isoformat(),
            'statistics': graph.get_statistics()
        }
    }


def export_graph_to_d3(graph: KnowledgeGraph) -> Dict[str, Any]:
    """
    将知识图谱导出为D3.js格式
    
    Args:
        graph: 知识图谱
        
    Returns:
        Dict[str, Any]: D3.js格式的数据
    """
    nodes = []
    links = []
    
    # 创建节点ID映射
    node_id_map = {entity_id: i for i, entity_id in enumerate(graph.entities.keys())}
    
    # 转换实体为节点
    for i, entity in enumerate(graph.entities.values()):
        node = {
            'id': i,
            'entity_id': entity.id,
            'name': entity.name,
            'type': entity.entity_type.value,
            'description': entity.description,
            'confidence': entity.confidence,
            'group': entity.entity_type.value,
            'size': max(5, min(20, entity.confidence * 15))  # 根据置信度设置大小
        }
        nodes.append(node)
    
    # 转换关系为链接
    for relation in graph.relations.values():
        if (relation.head_entity.id in node_id_map and 
            relation.tail_entity.id in node_id_map):
            
            link = {
                'source': node_id_map[relation.head_entity.id],
                'target': node_id_map[relation.tail_entity.id],
                'relation_id': relation.id,
                'type': relation.relation_type.value,
                'confidence': relation.confidence,
                'value': relation.confidence  # D3中的链接权重
            }
            links.append(link)
    
    return {
        'nodes': nodes,
        'links': links,
        'graph_info': {
            'id': graph.id,
            'name': graph.name,
            'node_count': len(nodes),
            'link_count': len(links)
        }
    }


def find_shortest_path(graph: KnowledgeGraph, start_entity_id: str, 
                      end_entity_id: str) -> Optional[List[Relation]]:
    """
    查找两个实体间的最短路径
    
    Args:
        graph: 知识图谱
        start_entity_id: 起始实体ID
        end_entity_id: 目标实体ID
        
    Returns:
        List[Relation]: 最短路径上的关系列表，如果不存在路径则返回None
    """
    if start_entity_id not in graph.entities or end_entity_id not in graph.entities:
        return None
    
    if start_entity_id == end_entity_id:
        return []
    
    # BFS查找最短路径
    from collections import deque
    
    queue = deque([(start_entity_id, [])])
    visited = {start_entity_id}
    
    while queue:
        current_entity_id, path = queue.popleft()
        
        # 获取当前实体的所有邻居
        neighbors = graph.get_neighbors(current_entity_id)
        relations = graph.get_entity_relations(current_entity_id, direction='out')
        
        for relation in relations:
            neighbor_id = relation.tail_entity.id
            
            if neighbor_id == end_entity_id:
                return path + [relation]
            
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append((neighbor_id, path + [relation]))
    
    return None


def calculate_graph_metrics(graph: KnowledgeGraph) -> Dict[str, Any]:
    """
    计算图谱的网络指标
    
    Args:
        graph: 知识图谱
        
    Returns:
        Dict[str, Any]: 图谱指标
    """
    if not graph.entities:
        return {}
    
    # 基本统计
    node_count = len(graph.entities)
    edge_count = len(graph.relations)
    
    # 计算度分布
    degree_map = {}
    in_degree_map = {}
    out_degree_map = {}
    
    for entity_id in graph.entities:
        total_degree = len(graph.get_entity_relations(entity_id))
        in_degree = len(graph.get_entity_relations(entity_id, direction='in'))
        out_degree = len(graph.get_entity_relations(entity_id, direction='out'))
        
        degree_map[entity_id] = total_degree
        in_degree_map[entity_id] = in_degree
        out_degree_map[entity_id] = out_degree
    
    # 统计指标
    degrees = list(degree_map.values())
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0
    min_degree = min(degrees) if degrees else 0
    
    # 密度计算
    max_possible_edges = node_count * (node_count - 1)
    density = (2 * edge_count) / max_possible_edges if max_possible_edges > 0 else 0
    
    # 找出度最高的节点（中心节点）
    central_nodes = sorted(degree_map.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # 连通性分析
    components = _find_connected_components(graph)
    
    return {
        'basic_stats': {
            'node_count': node_count,
            'edge_count': edge_count,
            'density': round(density, 4),
            'avg_degree': round(avg_degree, 2),
            'max_degree': max_degree,
            'min_degree': min_degree
        },
        'centrality': {
            'top_central_nodes': [
                {
                    'entity_id': entity_id,
                    'entity_name': graph.entities[entity_id].name,
                    'degree': degree
                }
                for entity_id, degree in central_nodes
            ]
        },
        'connectivity': {
            'connected_components': len(components),
            'largest_component_size': max(len(comp) for comp in components) if components else 0,
            'is_connected': len(components) <= 1
        },
        'type_distribution': _calculate_type_distribution(graph)
    }


def _find_connected_components(graph: KnowledgeGraph) -> List[List[str]]:
    """查找连通分量"""
    visited = set()
    components = []
    
    for entity_id in graph.entities:
        if entity_id not in visited:
            component = []
            stack = [entity_id]
            
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    component.append(current)
                    
                    # 添加邻居节点
                    neighbors = graph.get_neighbors(current)
                    for neighbor in neighbors:
                        if neighbor.id not in visited:
                            stack.append(neighbor.id)
            
            components.append(component)
    
    return components


def _calculate_type_distribution(graph: KnowledgeGraph) -> Dict[str, Any]:
    """计算类型分布"""
    entity_types = {}
    relation_types = {}
    
    for entity in graph.entities.values():
        entity_type = entity.entity_type.value
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    for relation in graph.relations.values():
        relation_type = relation.relation_type.value
        relation_types[relation_type] = relation_types.get(relation_type, 0) + 1
    
    return {
        'entity_types': entity_types,
        'relation_types': relation_types
    }


def merge_similar_entities(graph: KnowledgeGraph, similarity_threshold: float = 0.8) -> int:
    """
    合并相似的实体
    
    Args:
        graph: 知识图谱
        similarity_threshold: 相似度阈值
        
    Returns:
        int: 合并的实体数量
    """
    merged_count = 0
    entities_to_remove = set()
    
    entity_list = list(graph.entities.values())
    
    for i in range(len(entity_list)):
        if entity_list[i].id in entities_to_remove:
            continue
            
        for j in range(i + 1, len(entity_list)):
            if entity_list[j].id in entities_to_remove:
                continue
                
            entity1 = entity_list[i]
            entity2 = entity_list[j]
            
            # 计算名称相似度
            similarity = _calculate_name_similarity(entity1.name, entity2.name)
            
            if similarity >= similarity_threshold:
                # 合并实体
                if graph.merge_entity(entity1, entity2):
                    entities_to_remove.add(entity2.id)
                    merged_count += 1
                    logger.info(f"Merged entities: {entity1.name} <- {entity2.name}")
    
    return merged_count


def _calculate_name_similarity(name1: str, name2: str) -> float:
    """计算名称相似度（简单的Jaccard相似度）"""
    set1 = set(name1.lower().split())
    set2 = set(name2.lower().split())
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


def validate_graph_consistency(graph: KnowledgeGraph) -> List[Dict[str, Any]]:
    """
    验证图谱一致性
    
    Args:
        graph: 知识图谱
        
    Returns:
        List[Dict[str, Any]]: 一致性问题列表
    """
    issues = []
    
    # 检查关系的实体引用
    for relation in graph.relations.values():
        if not relation.head_entity or relation.head_entity.id not in graph.entities:
            issues.append({
                'type': 'missing_head_entity',
                'relation_id': relation.id,
                'description': f"关系 {relation.id} 的头实体不存在"
            })
        
        if not relation.tail_entity or relation.tail_entity.id not in graph.entities:
            issues.append({
                'type': 'missing_tail_entity', 
                'relation_id': relation.id,
                'description': f"关系 {relation.id} 的尾实体不存在"
            })
    
    # 检查重复的关系
    relation_signatures = {}
    for relation in graph.relations.values():
        if relation.head_entity and relation.tail_entity:
            signature = (
                relation.head_entity.id,
                relation.tail_entity.id,
                relation.relation_type.value
            )
            
            if signature in relation_signatures:
                issues.append({
                    'type': 'duplicate_relation',
                    'relation_ids': [relation_signatures[signature], relation.id],
                    'description': f"发现重复关系: {signature}"
                })
            else:
                relation_signatures[signature] = relation.id
    
    # 检查自环关系
    for relation in graph.relations.values():
        if (relation.head_entity and relation.tail_entity and 
            relation.head_entity.id == relation.tail_entity.id):
            issues.append({
                'type': 'self_loop',
                'relation_id': relation.id,
                'entity_id': relation.head_entity.id,
                'description': f"实体 {relation.head_entity.name} 存在自环关系"
            })
    
    return issues


def create_graph_summary(graph: KnowledgeGraph) -> str:
    """
    创建图谱摘要报告
    
    Args:
        graph: 知识图谱
        
    Returns:
        str: 图谱摘要
    """
    stats = graph.get_statistics()
    metrics = calculate_graph_metrics(graph)
    
    summary = f"""
知识图谱摘要报告
==================

基本信息:
- 图谱名称: {graph.name}
- 图谱ID: {graph.id}
- 创建时间: {graph.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- 更新时间: {graph.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

统计信息:
- 实体数量: {stats['total_entities']}
- 关系数量: {stats['total_relations']}
- 图密度: {metrics.get('basic_stats', {}).get('density', 0):.4f}
- 平均度数: {metrics.get('basic_stats', {}).get('avg_degree', 0):.2f}

实体类型分布:
"""
    
    for entity_type, count in stats.get('entity_types', {}).items():
        summary += f"- {entity_type}: {count}个\n"
    
    summary += "\n关系类型分布:\n"
    for relation_type, count in stats.get('relation_types', {}).items():
        summary += f"- {relation_type}: {count}个\n"
    
    # 添加中心节点
    central_nodes = metrics.get('centrality', {}).get('top_central_nodes', [])
    if central_nodes:
        summary += "\n中心节点 (度数最高):\n"
        for node in central_nodes[:3]:
            summary += f"- {node['entity_name']} (度数: {node['degree']})\n"
    
    # 连通性信息
    connectivity = metrics.get('connectivity', {})
    summary += f"\n连通性:\n"
    summary += f"- 连通分量数: {connectivity.get('connected_components', 0)}\n"
    summary += f"- 最大连通分量大小: {connectivity.get('largest_component_size', 0)}\n"
    summary += f"- 是否连通: {'是' if connectivity.get('is_connected', False) else '否'}\n"
    
    return summary