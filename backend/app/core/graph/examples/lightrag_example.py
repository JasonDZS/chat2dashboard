"""
LightRAG知识图谱构建器使用示例

本示例展示如何使用LightRAGGraphBuilder构建、查询和管理知识图谱。
"""
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import (
    create_lightrag_graph_builder,
    LightRAGGraphBuilder
)


async def basic_usage_example():
    """基本使用示例"""
    print("=== LightRAG知识图谱构建器基本使用示例 ===")
    
    # 1. 创建LightRAG构建器
    builder = create_lightrag_graph_builder("./workdir/example_lightrag_storage")
    
    # 2. 准备示例文档
    documents = [
        """
        北京是中华人民共和国的首都，位于华北地区。作为中国的政治、文化、国际交往、
        科技创新中心，北京有着3000多年建城史和860多年建都史。北京市下辖16个区，
        总面积16410.54平方千米。2022年末，北京市常住人口2184.3万人。
        """,
        """
        清华大学是中国著名的高等学府，位于北京市海淀区。学校创建于1911年，
        是中国九校联盟成员，被誉为"红色工程师的摇篮"。清华大学在工程技术、
        自然科学、经济管理、人文社科等多个学科领域都有很强的实力。
        """,
        """
        人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种
        新的能以人类智能相似的方式做出反应的智能机器。人工智能包括机器学习、
        深度学习、自然语言处理、计算机视觉等多个子领域。
        """
    ]
    
    try:
        # 3. 构建知识图谱
        print("正在构建知识图谱...")
        graph = await builder.build_graph(texts=documents, graph_name="示例知识图谱")
        
        print(f"构建完成! 实体数量: {len(graph.entities)}, 关系数量: {len(graph.relations)}")
        
        # 4. 显示部分实体信息
        print("\n=== 实体信息 ===")
        for i, entity in enumerate(list(graph.entities.values())[:5]):
            print(f"{i+1}. {entity.name} ({entity.entity_type.value})")
            print(f"   描述: {entity.description[:100]}...")
            print()
        
        # 5. 显示部分关系信息
        print("=== 关系信息 ===")
        for i, relation in enumerate(list(graph.relations.values())[:3]):
            print(f"{i+1}. {relation.head_entity.name} -> {relation.tail_entity.name}")
            print(f"   关系类型: {relation.relation_type.value}")
            print(f"   置信度: {relation.confidence}")
            print()
        
        return builder
        
    except Exception as e:
        print(f"构建过程中出现错误: {e}")
        return None
    finally:
        # 在这里不清理资源，因为我们要返回builder供后续使用
        pass


async def search_example(builder: LightRAGGraphBuilder):
    """搜索示例"""
    print("=== 知识图谱搜索示例 ===")
    
    if not builder:
        print("构建器未初始化，跳过搜索示例")
        return
    
    # 测试不同类型的搜索
    queries = [
        ("北京的基本信息是什么？", "hybrid"),
        ("清华大学有什么特点？", "local"),
        ("人工智能包括哪些技术？", "global"),
        ("中国的首都在哪里？", "naive")
    ]
    
    for query, search_type in queries:
        try:
            print(f"\n查询: {query}")
            print(f"搜索类型: {search_type}")
            
            result = await builder.search_graph(query, search_type)
            
            print("搜索结果:")
            print(result.get("result", "无结果")[:200] + "...")
            print("-" * 50)
            
        except Exception as e:
            print(f"搜索失败: {e}")


async def incremental_update_example(builder: LightRAGGraphBuilder):
    """增量更新示例"""
    print("=== 增量更新示例 ===")
    
    if not builder:
        print("构建器未初始化，跳过更新示例")
        return
    
    # 添加新文档
    new_documents = [
        """
        上海是中华人民共和国的直辖市，位于长江三角洲地区。作为中国的经济中心，
        上海是全球著名的金融中心之一。上海港是世界上最繁忙的集装箱港口之一。
        上海有着深厚的历史文化底蕴，同时也是现代化国际大都市。
        """,
        """
        机器学习是人工智能的一个重要分支，它使计算机能够无需明确编程即可学习。
        机器学习算法包括监督学习、无监督学习和强化学习等类型。深度学习是机器学习
        的一个子领域，使用神经网络来模拟人脑的工作方式。
        """
    ]
    
    try:
        print("正在添加新文档到知识图谱...")
        updated_graph = await builder.add_documents(new_documents, "更新后的示例知识图谱")
        
        print(f"更新完成! 新的实体数量: {len(updated_graph.entities)}, 关系数量: {len(updated_graph.relations)}")
        
        # 测试搜索新添加的内容
        print("\n测试搜索新内容:")
        result = await builder.search_graph("上海是什么样的城市？", "hybrid")
        print("搜索结果:", result.get("result", "无结果")[:200] + "...")
        
    except Exception as e:
        print(f"更新过程中出现错误: {e}")


async def export_example(builder: LightRAGGraphBuilder):
    """导出示例"""
    print("=== 导出GraphML示例 ===")
    
    if not builder:
        print("构建器未初始化，跳过导出示例")
        return
    
    try:
        # 获取当前图谱
        graphml_file = builder.working_dir / "graph_chunk_entity_relation.graphml"
        if graphml_file.exists():
            current_graph = builder._load_graph_from_graphml(str(graphml_file), "当前图谱")
            
            # 导出到新位置
            export_path = "./exported_knowledge_graph.graphml"
            success = builder.export_to_graphml(current_graph, export_path)
            
            if success:
                print(f"图谱已成功导出到: {export_path}")
                
                # 显示文件大小
                file_size = os.path.getsize(export_path)
                print(f"文件大小: {file_size} bytes")
            else:
                print("导出失败")
        else:
            print("未找到GraphML文件")
            
    except Exception as e:
        print(f"导出过程中出现错误: {e}")


async def statistics_example(builder: LightRAGGraphBuilder):
    """统计信息示例"""
    print("=== 图谱统计信息示例 ===")
    
    if not builder:
        print("构建器未初始化，跳过统计示例")
        return
    
    try:
        stats = await builder.get_graph_statistics()
        
        print("图谱统计信息:")
        print(f"- 实体数量: {stats.get('entities_count', 0)}")
        print(f"- 关系数量: {stats.get('relations_count', 0)}")
        print(f"- 状态: {stats.get('status', 'unknown')}")
        print(f"- GraphML文件: {stats.get('graphml_file', 'N/A')}")
        print(f"- 最后修改时间: {stats.get('last_modified', 'N/A')}")
        
        if 'error' in stats:
            print(f"- 错误信息: {stats['error']}")
            
    except Exception as e:
        print(f"获取统计信息时出现错误: {e}")


async def advanced_usage_example():
    """高级使用示例"""
    print("=== LightRAG高级使用示例 ===")
    
    # 创建自定义配置的构建器
    custom_builder = LightRAGGraphBuilder("./workdir/custom_lightrag_storage")
    
    # 模拟处理大量文档
    print("模拟处理多个文档类型...")
    
    documents = {
        "技术文档": [
            "Python是一种高级编程语言，具有简洁的语法和强大的功能。",
            "Docker是一个开源的应用容器引擎，让开发者可以打包应用。"
        ],
        "业务文档": [
            "我们公司专注于人工智能和大数据分析服务。",
            "客户满意度是我们最重要的业务指标之一。"
        ],
        "学术论文": [
            "深度学习在计算机视觉领域取得了显著进展。",
            "自然语言处理技术正在改变人机交互的方式。"
        ]
    }
    
    try:
        # 分类别处理文档
        all_texts = []
        for category, texts in documents.items():
            print(f"处理{category}...")
            all_texts.extend(texts)
        
        graph = await custom_builder.build_graph(texts=all_texts, graph_name="综合知识图谱")
        print(f"综合图谱构建完成: {len(graph.entities)} 实体, {len(graph.relations)} 关系")
        
        # 获取详细统计
        stats = await custom_builder.get_graph_statistics()
        print("详细统计:", stats)
        
    except Exception as e:
        print(f"高级示例执行失败: {e}")
    finally:
        # 清理高级示例的资源
        await custom_builder.cleanup()


async def main():
    """主函数"""
    print("LightRAG知识图谱构建器完整示例")
    print("=" * 50)
    
    # 1. 基本使用示例
    builder = await basic_usage_example()
    
    # 2. 搜索示例
    await search_example(builder)
    
    # 3. 增量更新示例
    await incremental_update_example(builder)
    
    # 4. 导出示例
    await export_example(builder)
    
    # 5. 统计信息示例
    await statistics_example(builder)
    
    # 6. 高级使用示例
    await advanced_usage_example()
    
    print("\n所有示例执行完成!")
    
    # 清理主要builder的资源
    if builder:
        await builder.cleanup()


if __name__ == "__main__":
    asyncio.run(main())