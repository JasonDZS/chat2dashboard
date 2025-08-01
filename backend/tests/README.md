# 测试文档

## 概述

本目录包含了Chat2Dashboard后端API的完整测试套件，使用pytest框架进行测试驱动开发(TDD)。

## 测试结构

```
tests/
├── conftest.py              # pytest配置和fixtures
├── pytest.ini              # pytest配置文件
├── README.md               # 测试文档
├── requirements-test.txt   # 测试依赖
└── api/
    └── v1/
        ├── test_database.py        # 数据库接口测试
        ├── test_knowledge_base.py  # 知识库接口测试
        ├── test_document.py        # 文档处理接口测试
        ├── test_search.py          # 混合检索接口测试
        ├── test_visualization.py   # 可视化接口测试
        ├── test_schema.py          # 模式管理接口测试
        ├── test_logs.py            # 日志接口测试
        └── test_system.py          # 系统接口测试
```

## 测试类型

### 1. 单元测试 (Unit Tests)
- 测试单个函数或方法的功能
- 使用Mock隔离外部依赖
- 快速执行，提供即时反馈

### 2. 集成测试 (Integration Tests)
- 测试多个组件协作
- 测试完整的业务流程
- 验证端到端功能

### 3. API测试 (API Tests)
- 测试HTTP接口的请求和响应
- 验证状态码、响应格式和数据正确性
- 包含错误处理和边界条件测试

### 4. 参数化测试 (Parametrized Tests)
- 使用不同参数组合测试同一功能
- 提高测试覆盖率
- 减少代码重复

## 测试覆盖的功能

### 数据库接口 (test_database.py)
- ✅ 文件上传（CSV/Excel）
- ✅ 文档上传（PDF/DOCX/TXT/MD）
- ✅ 数据库模式获取
- ✅ 模式JSON管理
- ✅ 数据库列表查询
- ✅ 错误处理和验证
- ✅ 并发请求处理
- ✅ 集成工作流程

### 知识库接口 (test_knowledge_base.py)
- ✅ 知识库创建和配置
- ✅ 知识库构建和状态跟踪
- ✅ 增量更新
- ✅ 知识库搜索
- ✅ 知识库验证
- ✅ 生命周期管理
- ✅ 并发操作
- ✅ 配置验证

### 文档处理接口 (test_document.py)
- ✅ 多格式文档上传
- ✅ 单文档和批量处理
- ✅ 处理状态跟踪
- ✅ 文档内容和分块获取
- ✅ 文档内搜索
- ✅ 文档生命周期管理
- ✅ 性能测试
- ✅ 错误处理

### 混合检索接口 (test_search.py)
- ✅ 混合检索策略
- ✅ 向量检索
- ✅ 关键词检索
- ✅ 图检索
- ✅ SQL生成
- ✅ 查询扩展
- ✅ 搜索建议
- ✅ 分析统计
- ✅ 用户反馈
- ✅ 健康检查

### 其他接口
- ✅ 可视化接口 (test_visualization.py)
- ✅ 模式管理接口 (test_schema.py)
- ✅ 日志接口 (test_logs.py)
- ✅ 系统接口 (test_system.py)

## 运行测试

### 安装测试依赖
```bash
pip install -r requirements-test.txt
```

### 运行所有测试
```bash
pytest
```

### 运行特定测试文件
```bash
pytest tests/api/v1/test_database.py
```

### 运行特定测试类
```bash
pytest tests/api/v1/test_database.py::TestDatabaseRouter
```

### 运行特定测试方法
```bash
pytest tests/api/v1/test_database.py::TestDatabaseRouter::test_upload_data_files_success
```

### 运行标记的测试
```bash
# 运行集成测试
pytest -m integration

# 跳过慢测试
pytest -m "not slow"

# 只运行API测试
pytest -m api
```

### 并行测试
```bash
pytest -n auto  # 自动检测CPU核心数
pytest -n 4     # 使用4个进程
```

### 生成覆盖率报告
```bash
pytest --cov=app --cov-report=html
```

## 测试配置

### Fixtures
`conftest.py` 提供了以下重要的fixtures：

- `client`: 同步测试客户端
- `async_client`: 异步测试客户端
- `mock_database_manager`: 模拟数据库管理器
- `mock_knowledge_base`: 模拟知识库数据
- `mock_document`: 模拟文档数据
- `mock_search_results`: 模拟搜索结果
- `sample_upload_file`: 样本上传文件
- `test_data`: 测试数据常量

### Mock策略
- 使用`unittest.mock.patch`隔离外部依赖
- Mock数据库操作避免实际数据库访问
- Mock文件操作避免文件系统影响
- Mock外部API调用

## 测试最佳实践

### 1. 测试命名规范
```python
def test_[功能]_[场景]_[期望结果](self, fixtures):
    """测试描述"""
```

### 2. 测试结构 (AAA模式)
```python
def test_example(self):
    # Arrange - 准备测试数据
    request_data = {...}
    
    # Act - 执行被测试的操作
    response = client.post("/api/endpoint", json=request_data)
    
    # Assert - 验证结果
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### 3. 测试隔离
- 每个测试方法独立运行
- 使用fixtures提供干净的测试环境
- 避免测试间的数据依赖

### 4. 错误测试
- 测试各种错误场景
- 验证错误响应格式
- 测试边界条件

### 5. 性能测试
- 验证响应时间在合理范围内
- 测试并发请求处理
- 监控资源使用

## 持续集成

测试套件设计为支持CI/CD流程：

1. **快速反馈**: 单元测试提供快速反馈
2. **全面覆盖**: 集成测试确保功能完整性
3. **质量保证**: 代码覆盖率要求80%以上
4. **自动化**: 支持自动化测试执行

## 测试数据管理

### 测试数据原则
- 使用最小化的测试数据
- 避免依赖外部数据源
- 使用factory或builder模式生成测试数据

### Mock数据
- 所有外部依赖都通过Mock提供
- Mock数据应该反映真实场景
- 保持Mock数据的一致性

## 调试测试

### 查看详细输出
```bash
pytest -v -s
```

### 运行失败时停止
```bash
pytest -x
```

### 调试特定失败
```bash
pytest --pdb
```

### 查看覆盖率详情
```bash
pytest --cov=app --cov-report=term-missing
```

## 贡献指南

### 添加新测试
1. 确定测试所属的模块
2. 遵循现有的测试结构和命名规范
3. 包含正常情况和错误情况的测试
4. 添加适当的文档字符串
5. 确保新测试通过并不影响现有测试

### 测试维护
1. 定期审查测试覆盖率
2. 更新过时的Mock数据
3. 重构重复的测试代码
4. 优化测试执行速度

## 性能基准

目标性能指标：
- 单元测试: < 100ms per test
- 集成测试: < 5s per test
- 总测试套件: < 10 minutes
- 代码覆盖率: > 80%

## 问题排查

### 常见问题
1. **Import错误**: 检查PYTHONPATH设置
2. **Mock失效**: 确认patch路径正确
3. **异步测试失败**: 使用pytest-asyncio标记
4. **数据库连接问题**: 确认Mock配置正确

### 联系方式
如有测试相关问题，请联系开发团队或提交Issue。