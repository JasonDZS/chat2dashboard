# 知识图谱数据格式规范

本文档定义了知识图谱组件支持的JSON数据格式，基于ECharts图表库的要求。

## 数据结构

知识图谱数据应包含以下三个主要部分：

### 1. nodes（节点数组）

每个节点对象包含以下属性：

```json
{
  "id": "string",           // 节点唯一标识符
  "name": "string",         // 节点显示名称
  "symbolSize": "number",   // 节点大小（可选）
  "x": "number",           // 节点X坐标（可选）
  "y": "number",           // 节点Y坐标（可选）
  "value": "number",       // 节点权重值（可选）
  "category": "number"     // 节点分类索引（可选）
}
```

### 2. links（连接数组）

每个连接对象包含以下属性：

```json
{
  "source": "string",      // 源节点ID
  "target": "string"       // 目标节点ID
}
```

### 3. categories（分类数组）

每个分类对象包含以下属性：

```json
{
  "name": "string"         // 分类名称
}
```

## 完整示例

```json
{
  "nodes": [
    {
      "id": "0",
      "name": "节点A",
      "symbolSize": 19.12,
      "x": -266.83,
      "y": 299.69,
      "value": 28.69,
      "category": 0
    },
    {
      "id": "1", 
      "name": "节点B",
      "symbolSize": 15.5,
      "x": -418.08,
      "y": 446.89,
      "value": 23.2,
      "category": 1
    }
  ],
  "links": [
    {
      "source": "0",
      "target": "1"
    }
  ],
  "categories": [
    {
      "name": "类别A"
    },
    {
      "name": "类别B"
    }
  ]
}
```

## 属性说明

### 节点属性详解

- **id**: 必需，字符串类型，用于连接关系的引用
- **name**: 必需，字符串类型，节点的显示标签
- **symbolSize**: 可选，数值类型，控制节点图标大小
- **x, y**: 可选，数值类型，节点的固定位置坐标
- **value**: 可选，数值类型，节点的权重或重要性数值
- **category**: 可选，数值类型，对应categories数组的索引

### 连接属性详解

- **source**: 必需，字符串类型，源节点的ID
- **target**: 必需，字符串类型，目标节点的ID

### 分类属性详解

- **name**: 必需，字符串类型，分类的显示名称

## 注意事项

1. 节点的`id`必须唯一
2. 连接中的`source`和`target`必须对应存在的节点ID
3. 节点的`category`值应对应categories数组中的有效索引
4. 坐标值`x`和`y`用于固定布局，如果不提供则使用自动布局
5. `symbolSize`和`value`可用于视觉编码，表示节点的重要程度