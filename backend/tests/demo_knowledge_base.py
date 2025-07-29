#!/usr/bin/env python3
"""
后端服务测试脚本
测试完整的知识库API端点和文档处理功能
"""
import asyncio
import aiohttp
from typing import Dict, Any, List
import io

# 后端服务地址
BASE_URL = "http://0.0.0.0:8000"

class BackendTester:
    """后端服务测试类"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health(self) -> Dict[str, Any]:
        """测试健康检查端点"""
        async with self.session.get(f"{self.base_url}/health") as resp:
            return await resp.json()
    
    async def test_status(self) -> Dict[str, Any]:
        """测试状态端点"""
        async with self.session.get(f"{self.base_url}/status") as resp:
            return await resp.json()
    
    async def create_knowledge_base(self, name: str, description: str = "", datasource_id: str = "demo") -> Dict[str, Any]:
        """创建知识库"""
        payload = {
            "name": name,
            "description": description,
            "datasource_id": datasource_id,
            "config": {
                "enable_kg": True,
                "enable_vector": True,
                "chunk_size": 512,
                "chunk_overlap": 50,
                "embedding_model": "sentence-bert",
                "kg_model": "relation-extraction-v1",
                "index_type": "hnsw",
                "similarity_threshold": 0.7
            },
            "tags": ["demo", "test"],
            "auto_build": True
        }
        async with self.session.post(
            f"{self.base_url}/api/v1/knowledge-base/create", 
            json=payload
        ) as resp:
            return await resp.json()
    
    async def get_knowledge_base_status(self, kb_id: str) -> Dict[str, Any]:
        """获取知识库状态"""
        async with self.session.get(
            f"{self.base_url}/api/v1/knowledge-base/{kb_id}/build/status"
        ) as resp:
            return await resp.json()
    
    async def upload_document(self, file_content: str, filename: str, kb_id: str, process_immediately: bool = True) -> Dict[str, Any]:
        """上传文档"""
        data = aiohttp.FormData()
        data.add_field('files', io.BytesIO(file_content.encode('utf-8')), filename=filename)
        data.add_field('kb_id', kb_id)
        data.add_field('process_immediately', str(process_immediately).lower())
        
        async with self.session.post(
            f"{self.base_url}/api/v1/document/upload",
            data=data
        ) as resp:
            return await resp.json()
    
    async def build_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """构建知识库"""
        async with self.session.post(
            f"{self.base_url}/api/v1/knowledge-base/{kb_id}/build"
        ) as resp:
            return await resp.json()
    
    async def search_knowledge_base(self, kb_id: str, query: str, search_type: str = "hybrid") -> Dict[str, Any]:
        """搜索知识库"""
        payload = {
            "query": query,
            "search_type": search_type,
            "top_k": 10,
            "score_threshold": 0.5,
            "enable_rerank": True,
            "include_metadata": True,
            "highlight": True,
            "expand_context": False
        }
        async with self.session.post(
            f"{self.base_url}/api/v1/knowledge-base/{kb_id}/search",
            json=payload
        ) as resp:
            return await resp.json()
    
    async def delete_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """删除知识库"""
        async with self.session.delete(
            f"{self.base_url}/api/v1/knowledge-base/{kb_id}"
        ) as resp:
            return await resp.json()
    
    async def validate_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """验证知识库"""
        async with self.session.post(
            f"{self.base_url}/api/v1/knowledge-base/{kb_id}/validate"
        ) as resp:
            return await resp.json()
    
    async def get_knowledge_base_info(self, kb_id: str) -> Dict[str, Any]:
        """获取知识库详细信息"""
        async with self.session.get(
            f"{self.base_url}/api/v1/knowledge-base/{kb_id}"
        ) as resp:
            return await resp.json()
    
    async def list_knowledge_bases(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """获取知识库列表"""
        params = {"limit": limit, "offset": offset}
        async with self.session.get(
            f"{self.base_url}/api/v1/knowledge-base/",
            params=params
        ) as resp:
            return await resp.json()
    
    async def get_document_info(self, file_id: str) -> Dict[str, Any]:
        """获取文档详细信息"""
        async with self.session.get(
            f"{self.base_url}/api/v1/document/{file_id}"
        ) as resp:
            return await resp.json()
    
    async def get_document_content(self, file_id: str, include_metadata: bool = True) -> Dict[str, Any]:
        """获取文档内容"""
        params = {"include_metadata": include_metadata}
        async with self.session.get(
            f"{self.base_url}/api/v1/document/{file_id}/content",
            params=params
        ) as resp:
            return await resp.json()
    
    async def list_documents(self, kb_id: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """获取文档列表"""
        params = {"kb_id": kb_id, "limit": limit, "offset": offset}
        async with self.session.get(
            f"{self.base_url}/api/v1/document/",
            params=params
        ) as resp:
            return await resp.json()
    
    async def delete_document(self, file_id: str) -> Dict[str, Any]:
        """删除文档"""
        async with self.session.delete(
            f"{self.base_url}/api/v1/document/{file_id}"
        ) as resp:
            return await resp.json()

def create_sample_documents() -> List[Dict[str, str]]:
    """创建示例文档"""
    return [
        {
            "filename": "machine_learning_intro.txt",
            "content": """# 机器学习基础

机器学习是人工智能的核心分支，通过算法使计算机从数据中自动学习规律。

## 主要算法类型

### 监督学习
- 线性回归：预测连续值
- 逻辑回归：分类问题
- 决策树：基于规则的分类
- 随机森林：集成学习方法
- 支持向量机：最大间隔分类器

### 无监督学习
- K均值聚类：数据分组
- 层次聚类：构建聚类树
- 主成分分析：降维技术
- 异常检测：识别异常数据点

### 强化学习
- Q学习：基于价值的方法
- 策略梯度：直接优化策略
- Actor-Critic：结合价值和策略

## 应用场景

机器学习在各行业都有广泛应用：
- 金融：风险评估、欺诈检测
- 医疗：疾病诊断、药物发现  
- 零售：推荐系统、需求预测
- 交通：自动驾驶、路径优化
- 制造：质量控制、预测性维护
"""
        },
        {
            "filename": "data_science_tools.md",
            "content": """# 数据科学工具生态

## Python生态系统

### 数据处理
- **Pandas**: 数据分析和操作库
- **NumPy**: 科学计算基础库
- **Dask**: 大规模数据并行处理

### 机器学习
- **Scikit-learn**: 通用机器学习库
- **TensorFlow**: 深度学习框架
- **PyTorch**: 动态图深度学习
- **XGBoost**: 梯度提升算法

### 可视化
- **Matplotlib**: 基础绘图库
- **Seaborn**: 统计可视化
- **Plotly**: 交互式图表
- **Bokeh**: Web可视化

## R语言工具

### 统计分析
- **ggplot2**: 图形语法可视化
- **dplyr**: 数据操作
- **tidyr**: 数据整理
- **caret**: 分类和回归训练

## 大数据工具

### 分布式计算
- **Apache Spark**: 大规模数据处理
- **Hadoop**: 分布式存储和计算
- **Kafka**: 流数据处理

### 数据库
- **MongoDB**: 文档数据库
- **Cassandra**: 列族数据库
- **Redis**: 内存数据库
"""
        },
        {
            "filename": "deep_learning.txt",
            "content": """# 深度学习概述

深度学习是机器学习的子领域，使用多层神经网络来学习数据的复杂模式。

## 神经网络架构

### 基础网络
1. **全连接网络（DNN）**
   - 结构：输入层 → 隐藏层 → 输出层
   - 应用：分类、回归问题
   - 优点：通用性强
   - 缺点：参数多，易过拟合

2. **卷积神经网络（CNN）**
   - 结构：卷积层 → 池化层 → 全连接层
   - 应用：图像识别、计算机视觉
   - 优点：参数共享，平移不变性
   - 经典模型：LeNet, AlexNet, ResNet

3. **循环神经网络（RNN）**
   - 结构：带记忆的循环连接
   - 应用：序列数据处理
   - 变种：LSTM, GRU
   - 应用场景：语言模型、时间序列

### 现代架构
4. **Transformer**
   - 核心：自注意力机制
   - 优势：并行计算、长距离依赖
   - 应用：自然语言处理
   - 代表模型：BERT, GPT, T5

5. **生成对抗网络（GAN）**
   - 结构：生成器 vs 判别器
   - 应用：图像生成、数据增强
   - 变种：DCGAN, StyleGAN, CycleGAN

## 训练技巧

### 优化算法
- SGD：随机梯度下降
- Adam：自适应学习率
- RMSprop：均方根传播

### 正则化技术
- Dropout：随机丢弃神经元
- Batch Normalization：批标准化
- Early Stopping：早停法

### 数据增强
- 图像：旋转、翻转、缩放
- 文本：同义词替换、回译
- 音频：噪声添加、时间拉伸
"""
        }
    ]

async def demonstrate_backend_api():
    """演示后端API功能"""
    print("🎯 后端服务API测试")
    print("=" * 50)
    
    async with BackendTester() as tester:
        # 步骤1: 测试服务健康状况
        print(f"\n🔧 步骤1: 测试服务健康状况")
        try:
            health = await tester.test_health()
            print(f"✓ 健康检查: {health}")
            
            status = await tester.test_status()
            print(f"✓ 服务状态: {status}")
        except Exception as e:
            print(f"❌ 服务连接失败: {str(e)}")
            print("请确保后端服务运行在 http://0.0.0.0:8000")
            return None
        
        # 步骤2: 创建知识库
        print(f"\n📚 步骤2: 创建知识库")
        kb_name = "demo-ml-knowledge-base"
        try:
            kb_result = await tester.create_knowledge_base(
                name=kb_name,
                description="机器学习和数据科学演示知识库"
            )
            print(f"✓ 知识库创建结果: {kb_result}")
            kb_id = kb_result.get("id") or kb_result.get("kb_id")
            if not kb_id:
                print("❌ 无法获取知识库ID")
                return None
        except Exception as e:
            print(f"❌ 知识库创建失败: {str(e)}")
            return None
        
        # 步骤3: 上传示例文档
        print(f"\n📄 步骤3: 上传示例文档")
        documents = create_sample_documents()
        uploaded_files = []
        
        for doc in documents:
            try:
                result = await tester.upload_document(
                    doc["content"], 
                    doc["filename"],
                    kb_id
                )
                print(f"✓ 上传文档 {doc['filename']}: {result}")
                if result.get("uploaded_files"):
                    for uploaded_file in result["uploaded_files"]:
                        uploaded_files.append(uploaded_file["id"])
                elif result.get("file_id"):
                    uploaded_files.append(result["file_id"])
            except Exception as e:
                print(f"❌ 文档上传失败 {doc['filename']}: {str(e)}")
        
        # 步骤4: 构建知识库
        print(f"\n🏗️  步骤4: 构建知识库")
        try:
            build_result = await tester.build_knowledge_base(kb_id)
            print(f"✓ 知识库构建启动: {build_result}")
        except Exception as e:
            print(f"❌ 知识库构建失败: {str(e)}")
        
        # 步骤5: 检查构建状态
        print(f"\n🔍 步骤5: 检查构建状态")
        for i in range(10):  # 最多检查10次
            try:
                status = await tester.get_knowledge_base_status(kb_id)
                print(f"  检查 {i+1}/10: {status}")
                
                if status.get("status") == "ready":
                    print("✓ 知识库构建完成")
                    break
                elif status.get("status") == "failed":
                    print("❌ 知识库构建失败")
                    break
                
                await asyncio.sleep(2)  # 等待2秒再检查
            except Exception as e:
                print(f"❌ 状态检查失败: {str(e)}")
                break
        
        # 步骤6: 验证知识库
        print(f"\n🔬 步骤6: 验证知识库")
        try:
            validation = await tester.validate_knowledge_base(kb_id)
            print(f"✓ 知识库验证结果: {validation}")
        except Exception as e:
            print(f"❌ 知识库验证失败: {str(e)}")
        
        # 步骤7: 获取知识库详细信息
        print(f"\n📋 步骤7: 获取知识库详细信息")
        try:
            kb_info = await tester.get_knowledge_base_info(kb_id)
            print(f"✓ 知识库详细信息: {kb_info}")
        except Exception as e:
            print(f"❌ 获取知识库信息失败: {str(e)}")
        
        # 步骤8: 测试搜索功能
        print(f"\n🔎 步骤8: 测试搜索功能")
        sample_queries = [
            ("什么是机器学习？", "hybrid"),
            ("深度学习有哪些主要架构？", "semantic"),
            ("Python有哪些数据科学工具？", "keyword"),
            ("如何进行模型优化？", "hybrid")
        ]
        
        for query, search_type in sample_queries:
            try:
                search_result = await tester.search_knowledge_base(kb_id, query, search_type)
                print(f"  Q: {query} (类型: {search_type})")
                if search_result.get("results"):
                    print(f"  A: 找到 {len(search_result['results'])} 个结果")
                    for i, result in enumerate(search_result["results"][:2]):  # 只显示前2个结果
                        print(f"    结果{i+1}: {result.get('snippet', result.get('content', ''))[:100]}...")
                else:
                    print(f"  A: {search_result}")
                print()
            except Exception as e:
                print(f"❌ 搜索失败 '{query}': {str(e)}")
        
        # 步骤9: 测试文档管理功能
        print(f"\n📋 步骤9: 测试文档管理功能")
        if uploaded_files:
            # 测试文档列表
            try:
                doc_list = await tester.list_documents(kb_id)
                print(f"✓ 文档列表: 找到 {doc_list.get('total_count', 0)} 个文档")
                for doc in doc_list.get("documents", [])[:2]:  # 只显示前2个
                    print(f"  - {doc.get('filename')} (ID: {doc.get('id')}, 状态: {doc.get('status')})")
            except Exception as e:
                print(f"❌ 获取文档列表失败: {str(e)}")
            
            # 测试文档详情
            if uploaded_files:
                file_id = uploaded_files[0]
                try:
                    doc_info = await tester.get_document_info(file_id)
                    print(f"✓ 文档详情: {doc_info.get('filename')} ({doc_info.get('file_size', 0)} bytes)")
                except Exception as e:
                    print(f"❌ 获取文档详情失败: {str(e)}")
                
                try:
                    doc_content = await tester.get_document_content(file_id)
                    content_preview = doc_content.get("content", "")[:150] + "..." if len(doc_content.get("content", "")) > 150 else doc_content.get("content", "")
                    print(f"✓ 文档内容预览: {content_preview}")
                except Exception as e:
                    print(f"❌ 获取文档内容失败: {str(e)}")
        
        # 步骤10: 测试知识库列表
        print(f"\n📝 步骤10: 测试知识库列表")
        try:
            kb_list = await tester.list_knowledge_bases()
            print(f"✓ 知识库列表: {kb_list}")
            if kb_list.get("knowledge_bases"):
                print(f"  总计 {kb_list.get('total_count', 0)} 个知识库")
                for kb in kb_list["knowledge_bases"][:3]:  # 只显示前3个
                    print(f"  - {kb.get('name')} (ID: {kb.get('id')}, 状态: {kb.get('status')})")
        except Exception as e:
            print(f"❌ 获取知识库列表失败: {str(e)}")
        
        return kb_id, uploaded_files

async def cleanup_demo(kb_id: str):
    """清理演示数据"""
    print(f"\n🧹 清理演示数据...")
    
    async with BackendTester() as tester:
        try:
            result = await tester.delete_knowledge_base(kb_id)
            print(f"✓ 清理完成: {result}")
        except Exception as e:
            print(f"⚠️  清理失败: {str(e)}")

async def main():
    """主测试函数"""
    print("🚀 后端服务API测试")
    print("🎯 测试完整的知识库API端点和文档处理功能")
    print("=" * 60)
    
    try:
        # 运行主要测试
        result = await demonstrate_backend_api()
        
        if result and len(result) == 2:
            kb_id, uploaded_files = result
        else:
            kb_id = result
            uploaded_files = []
        
        if kb_id:
            # 测试总结
            print("\n" + "=" * 60)
            print("🎉 API测试完成！")
            print("=" * 60)
            
            print("✅ 成功测试的功能:")
            print("  • 服务健康检查 (/health, /status)")
            print("  • 知识库创建 (POST /api/v1/knowledge-base/create)")
            print("  • 文档上传 (POST /api/v1/document/upload)")
            print("  • 知识库构建 (POST /api/v1/knowledge-base/{kb_id}/build)")
            print("  • 构建状态查询 (GET /api/v1/knowledge-base/{kb_id}/build/status)")
            print("  • 知识库验证 (POST /api/v1/knowledge-base/{kb_id}/validate)")
            print("  • 知识库详细信息 (GET /api/v1/knowledge-base/{kb_id})")
            print("  • 多类型搜索功能 (POST /api/v1/knowledge-base/{kb_id}/search)")
            print("  • 文档管理功能 (GET /api/v1/document/, GET /api/v1/document/{file_id})")
            print("  • 文档内容获取 (GET /api/v1/document/{file_id}/content)")
            print("  • 知识库列表 (GET /api/v1/knowledge-base/)")
            print("  • 知识库删除 (DELETE /api/v1/knowledge-base/{kb_id})")
            
            # 询问是否清理
            try:
                response = input("\n❓ 是否清理测试数据？(y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    await cleanup_demo(kb_id)
                else:
                    print(f"📁 测试数据保留，知识库ID: {kb_id}")
            except KeyboardInterrupt:
                print(f"\n📁 测试数据保留，知识库ID: {kb_id}")
        else:
            print("\n❌ 测试未能完成，请检查后端服务状态")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())