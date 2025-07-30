"""
图嵌入处理器模块
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
import logging
import numpy as np
from collections import defaultdict
import random

from ..entities import Entity
from ..relations import Relation
from ..graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class GraphEmbedding(ABC):
    """图嵌入基类"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.entity_embeddings = {}
        self.relation_embeddings = {}
        self.entity_to_id = {}
        self.id_to_entity = {}
        self.relation_to_id = {}
        self.id_to_relation = {}
    
    @abstractmethod
    def train(self, graph: KnowledgeGraph, **kwargs) -> bool:
        """
        训练图嵌入模型
        
        Args:
            graph: 知识图谱
            **kwargs: 训练参数
            
        Returns:
            bool: 训练是否成功
        """
        pass
    
    @abstractmethod
    def get_entity_embedding(self, entity_id: str) -> Optional[np.ndarray]:
        """
        获取实体嵌入向量
        
        Args:
            entity_id: 实体ID
            
        Returns:
            np.ndarray: 嵌入向量，如果不存在则返回None
        """
        pass
    
    def compute_entity_similarity(self, entity1_id: str, entity2_id: str) -> float:
        """
        计算实体相似度
        
        Args:
            entity1_id: 实体1 ID
            entity2_id: 实体2 ID
            
        Returns:
            float: 相似度分数 (0-1)
        """
        try:
            emb1 = self.get_entity_embedding(entity1_id)
            emb2 = self.get_entity_embedding(entity2_id)
            
            if emb1 is None or emb2 is None:
                return 0.0
            
            # 计算余弦相似度
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, (similarity + 1) / 2))  # 将[-1,1]映射到[0,1]
        
        except Exception as e:
            logger.error(f"Error computing entity similarity: {e}")
            return 0.0
    
    def recommend_entities(self, entity_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        基于嵌入的实体推荐
        
        Args:
            entity_id: 输入实体ID
            top_k: 推荐数量
            
        Returns:
            List[Tuple[str, float]]: 推荐实体列表及相似度
        """
        try:
            similarities = []
            
            for other_entity_id in self.entity_embeddings:
                if other_entity_id != entity_id:
                    similarity = self.compute_entity_similarity(entity_id, other_entity_id)
                    similarities.append((other_entity_id, similarity))
            
            # 按相似度排序并返回Top-K
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
        
        except Exception as e:
            logger.error(f"Error recommending entities: {e}")
            return []
    
    def save_embeddings(self, filepath: str) -> bool:
        """
        保存嵌入向量
        
        Args:
            filepath: 保存路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            import pickle
            
            embedding_data = {
                'entity_embeddings': self.entity_embeddings,
                'relation_embeddings': self.relation_embeddings,
                'entity_to_id': self.entity_to_id,
                'id_to_entity': self.id_to_entity,
                'relation_to_id': self.relation_to_id,
                'id_to_relation': self.id_to_relation,
                'embedding_dim': self.embedding_dim
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(embedding_data, f)
            
            logger.info(f"Embeddings saved to {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            return False
    
    def load_embeddings(self, filepath: str) -> bool:
        """
        加载嵌入向量
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            import pickle
            
            with open(filepath, 'rb') as f:
                embedding_data = pickle.load(f)
            
            self.entity_embeddings = embedding_data.get('entity_embeddings', {})
            self.relation_embeddings = embedding_data.get('relation_embeddings', {})
            self.entity_to_id = embedding_data.get('entity_to_id', {})
            self.id_to_entity = embedding_data.get('id_to_entity', {})
            self.relation_to_id = embedding_data.get('relation_to_id', {})
            self.id_to_relation = embedding_data.get('id_to_relation', {})
            self.embedding_dim = embedding_data.get('embedding_dim', self.embedding_dim)
            
            logger.info(f"Embeddings loaded from {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return False
    
    def _build_entity_mapping(self, graph: KnowledgeGraph):
        """构建实体映射"""
        entity_list = list(graph.entities.keys())
        self.entity_to_id = {entity: i for i, entity in enumerate(entity_list)}
        self.id_to_entity = {i: entity for entity, i in self.entity_to_id.items()}
    
    def _build_relation_mapping(self, graph: KnowledgeGraph):
        """构建关系映射"""
        relation_types = set()
        for relation in graph.relations.values():
            relation_types.add(relation.relation_type.value)
        
        relation_list = list(relation_types)
        self.relation_to_id = {relation: i for i, relation in enumerate(relation_list)}
        self.id_to_relation = {i: relation for relation, i in self.relation_to_id.items()}


class Node2VecEmbedding(GraphEmbedding):
    """Node2Vec图嵌入"""
    
    def __init__(self, embedding_dim: int = 128, walk_length: int = 80, 
                 num_walks: int = 10, p: float = 1, q: float = 1):
        super().__init__(embedding_dim)
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p  # 返回参数
        self.q = q  # 进出参数
        
    def train(self, graph: KnowledgeGraph, epochs: int = 100, learning_rate: float = 0.025) -> bool:
        """训练Node2Vec嵌入"""
        try:
            self._build_entity_mapping(graph)
            
            # 构建邻接表
            adjacency = self._build_adjacency_list(graph)
            
            # 生成随机游走序列
            walks = self._generate_walks(adjacency)
            
            # 训练Skip-gram模型
            self._train_skipgram(walks, epochs, learning_rate)
            
            logger.info(f"Node2Vec training completed with {len(self.entity_embeddings)} entity embeddings")
            return True
        
        except Exception as e:
            logger.error(f"Error training Node2Vec: {e}")
            return False
    
    def get_entity_embedding(self, entity_id: str) -> Optional[np.ndarray]:
        """获取实体嵌入向量"""
        return self.entity_embeddings.get(entity_id)
    
    def _build_adjacency_list(self, graph: KnowledgeGraph) -> Dict[str, List[str]]:
        """构建邻接表"""
        adjacency = defaultdict(list)
        
        for relation in graph.relations.values():
            head_id = relation.head_entity.id
            tail_id = relation.tail_entity.id
            
            # 构建无向图
            adjacency[head_id].append(tail_id)
            adjacency[tail_id].append(head_id)
        
        return adjacency
    
    def _generate_walks(self, adjacency: Dict[str, List[str]]) -> List[List[str]]:
        """生成随机游走序列"""
        walks = []
        nodes = list(adjacency.keys())
        
        for _ in range(self.num_walks):
            random.shuffle(nodes)
            for node in nodes:
                walk = self._random_walk(adjacency, node)
                if len(walk) > 1:
                    walks.append(walk)
        
        return walks
    
    def _random_walk(self, adjacency: Dict[str, List[str]], start_node: str) -> List[str]:
        """执行单次随机游走"""
        walk = [start_node]
        
        while len(walk) < self.walk_length:
            current = walk[-1]
            neighbors = adjacency.get(current, [])
            
            if not neighbors:
                break
            
            if len(walk) == 1:
                # 第一步，随机选择邻居
                next_node = random.choice(neighbors)
            else:
                # 根据p, q参数选择下一个节点
                prev = walk[-2]
                next_node = self._choose_next_node(current, prev, neighbors, adjacency)
            
            walk.append(next_node)
        
        return walk
    
    def _choose_next_node(self, current: str, prev: str, neighbors: List[str], 
                         adjacency: Dict[str, List[str]]) -> str:
        """根据p, q参数选择下一个节点"""
        probs = []
        
        for neighbor in neighbors:
            if neighbor == prev:
                # 返回上一个节点的概率
                prob = 1.0 / self.p
            elif neighbor in adjacency.get(prev, []):
                # 到达公共邻居的概率
                prob = 1.0
            else:
                # 探索远离之前节点的概率
                prob = 1.0 / self.q
            
            probs.append(prob)
        
        # 归一化概率
        total_prob = sum(probs)
        if total_prob == 0:
            return random.choice(neighbors)
        
        probs = [p / total_prob for p in probs]
        
        # 根据概率选择
        r = random.random()
        cumsum = 0
        for i, prob in enumerate(probs):
            cumsum += prob
            if r <= cumsum:
                return neighbors[i]
        
        return neighbors[-1]
    
    def _train_skipgram(self, walks: List[List[str]], epochs: int, learning_rate: float):
        """训练Skip-gram模型"""
        # 简化的Skip-gram实现
        vocabulary = set()
        for walk in walks:
            vocabulary.update(walk)
        
        vocab_size = len(vocabulary)
        vocab_to_idx = {word: i for i, word in enumerate(vocabulary)}
        
        # 初始化嵌入矩阵
        W1 = np.random.uniform(-0.5/self.embedding_dim, 0.5/self.embedding_dim, 
                              (vocab_size, self.embedding_dim))
        W2 = np.random.uniform(-0.5/self.embedding_dim, 0.5/self.embedding_dim, 
                              (self.embedding_dim, vocab_size))
        
        window_size = 5
        
        for epoch in range(epochs):
            total_loss = 0
            
            for walk in walks:
                for i, center_word in enumerate(walk):
                    center_idx = vocab_to_idx[center_word]
                    
                    # 获取上下文窗口
                    context_indices = []
                    for j in range(max(0, i - window_size), 
                                 min(len(walk), i + window_size + 1)):
                        if i != j:
                            context_indices.append(vocab_to_idx[walk[j]])
                    
                    if not context_indices:
                        continue
                    
                    # 前向传播
                    h = W1[center_idx]
                    
                    for context_idx in context_indices:
                        # 计算输出层
                        u = np.dot(h, W2)
                        y_pred = self._softmax(u)
                        
                        # 计算损失
                        loss = -np.log(y_pred[context_idx] + 1e-10)
                        total_loss += loss
                        
                        # 反向传播
                        e = y_pred.copy()
                        e[context_idx] -= 1.0
                        
                        # 更新权重
                        W2 -= learning_rate * np.outer(h, e)
                        W1[center_idx] -= learning_rate * np.dot(W2, e)
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}, Loss: {total_loss:.4f}")
        
        # 保存最终嵌入
        for entity_id in vocabulary:
            if entity_id in vocab_to_idx:
                idx = vocab_to_idx[entity_id]
                self.entity_embeddings[entity_id] = W1[idx].copy()
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax函数"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)


class TransEEmbedding(GraphEmbedding):
    """TransE平移模型嵌入"""
    
    def __init__(self, embedding_dim: int = 128, margin: float = 1.0):
        super().__init__(embedding_dim)
        self.margin = margin
    
    def train(self, graph: KnowledgeGraph, epochs: int = 100, 
              learning_rate: float = 0.01, batch_size: int = 100) -> bool:
        """训练TransE嵌入"""
        try:
            self._build_entity_mapping(graph)
            self._build_relation_mapping(graph)
            
            # 构建训练三元组
            triplets = self._build_triplets(graph)
            
            # 初始化嵌入
            self._initialize_embeddings()
            
            # 训练模型
            self._train_model(triplets, epochs, learning_rate, batch_size)
            
            logger.info(f"TransE training completed with {len(self.entity_embeddings)} entity embeddings")
            return True
        
        except Exception as e:
            logger.error(f"Error training TransE: {e}")
            return False
    
    def get_entity_embedding(self, entity_id: str) -> Optional[np.ndarray]:
        """获取实体嵌入向量"""
        return self.entity_embeddings.get(entity_id)
    
    def get_relation_embedding(self, relation_type: str) -> Optional[np.ndarray]:
        """获取关系嵌入向量"""
        return self.relation_embeddings.get(relation_type)
    
    def _build_triplets(self, graph: KnowledgeGraph) -> List[Tuple[str, str, str]]:
        """构建训练三元组 (head, relation, tail)"""
        triplets = []
        
        for relation in graph.relations.values():
            triplet = (
                relation.head_entity.id,
                relation.relation_type.value,
                relation.tail_entity.id
            )
            triplets.append(triplet)
        
        return triplets
    
    def _initialize_embeddings(self):
        """初始化嵌入向量"""
        # 初始化实体嵌入
        for entity_id in self.entity_to_id:
            embedding = np.random.uniform(-6/np.sqrt(self.embedding_dim), 
                                        6/np.sqrt(self.embedding_dim), 
                                        self.embedding_dim)
            # L2归一化
            embedding = embedding / np.linalg.norm(embedding)
            self.entity_embeddings[entity_id] = embedding
        
        # 初始化关系嵌入
        for relation_type in self.relation_to_id:
            embedding = np.random.uniform(-6/np.sqrt(self.embedding_dim), 
                                        6/np.sqrt(self.embedding_dim), 
                                        self.embedding_dim)
            # L2归一化
            embedding = embedding / np.linalg.norm(embedding)
            self.relation_embeddings[relation_type] = embedding
    
    def _train_model(self, triplets: List[Tuple[str, str, str]], epochs: int, 
                    learning_rate: float, batch_size: int):
        """训练TransE模型"""
        for epoch in range(epochs):
            total_loss = 0
            random.shuffle(triplets)
            
            for i in range(0, len(triplets), batch_size):
                batch = triplets[i:i + batch_size]
                batch_loss = 0
                
                for head, relation, tail in batch:
                    # 正样本
                    h_pos = self.entity_embeddings[head]
                    r = self.relation_embeddings[relation]
                    t_pos = self.entity_embeddings[tail]
                    
                    # 生成负样本
                    neg_head, neg_relation, neg_tail = self._generate_negative_sample(
                        head, relation, tail, triplets
                    )
                    
                    h_neg = self.entity_embeddings[neg_head]
                    r_neg = self.relation_embeddings[neg_relation]
                    t_neg = self.entity_embeddings[neg_tail]
                    
                    # 计算损失
                    pos_score = np.linalg.norm(h_pos + r - t_pos)
                    neg_score = np.linalg.norm(h_neg + r_neg - t_neg)
                    
                    loss = max(0, self.margin + pos_score - neg_score)
                    batch_loss += loss
                    
                    if loss > 0:
                        # 计算梯度并更新
                        self._update_embeddings(
                            head, relation, tail, neg_head, neg_relation, neg_tail, 
                            learning_rate
                        )
                
                total_loss += batch_loss
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}, Loss: {total_loss:.4f}")
    
    def _generate_negative_sample(self, head: str, relation: str, tail: str, 
                                triplets: List[Tuple[str, str, str]]) -> Tuple[str, str, str]:
        """生成负样本"""
        # 随机替换头实体或尾实体
        if random.random() < 0.5:
            # 替换头实体
            neg_head = random.choice(list(self.entity_to_id.keys()))
            while (neg_head, relation, tail) in triplets:
                neg_head = random.choice(list(self.entity_to_id.keys()))
            return neg_head, relation, tail
        else:
            # 替换尾实体
            neg_tail = random.choice(list(self.entity_to_id.keys()))
            while (head, relation, neg_tail) in triplets:
                neg_tail = random.choice(list(self.entity_to_id.keys()))
            return head, relation, neg_tail
    
    def _update_embeddings(self, head: str, relation: str, tail: str,
                          neg_head: str, neg_relation: str, neg_tail: str,
                          learning_rate: float):
        """更新嵌入向量"""
        h_pos = self.entity_embeddings[head]
        r = self.relation_embeddings[relation]
        t_pos = self.entity_embeddings[tail]
        
        h_neg = self.entity_embeddings[neg_head]
        r_neg = self.relation_embeddings[neg_relation]
        t_neg = self.entity_embeddings[neg_tail]
        
        # 计算梯度
        pos_diff = h_pos + r - t_pos
        neg_diff = h_neg + r_neg - t_neg
        
        pos_norm = np.linalg.norm(pos_diff)
        neg_norm = np.linalg.norm(neg_diff)
        
        if pos_norm > 0:
            pos_gradient = pos_diff / pos_norm
        else:
            pos_gradient = np.zeros_like(pos_diff)
        
        if neg_norm > 0:
            neg_gradient = neg_diff / neg_norm
        else:
            neg_gradient = np.zeros_like(neg_diff)
        
        # 更新正样本嵌入
        self.entity_embeddings[head] -= learning_rate * pos_gradient
        self.relation_embeddings[relation] -= learning_rate * pos_gradient
        self.entity_embeddings[tail] += learning_rate * pos_gradient
        
        # 更新负样本嵌入
        self.entity_embeddings[neg_head] += learning_rate * neg_gradient
        self.relation_embeddings[neg_relation] += learning_rate * neg_gradient
        self.entity_embeddings[neg_tail] -= learning_rate * neg_gradient
        
        # L2归一化
        for entity_id in [head, tail, neg_head, neg_tail]:
            embedding = self.entity_embeddings[entity_id]
            norm = np.linalg.norm(embedding)
            if norm > 0:
                self.entity_embeddings[entity_id] = embedding / norm
        
        for rel_type in [relation, neg_relation]:
            embedding = self.relation_embeddings[rel_type]
            norm = np.linalg.norm(embedding)
            if norm > 0:
                self.relation_embeddings[rel_type] = embedding / norm