def infer_chart_type_from_query(query: str) -> str:
    """
    根据用户问题推断合适的图表类型
    """
    query_lower = query.lower()

    # 饼图关键词
    pie_keywords = ['占比', '比例', '百分比', '分布', '构成', '份额', 'percentage', 'proportion', 'share',
                    'composition']
    if any(keyword in query_lower for keyword in pie_keywords):
        return "pie"

    # 折线图关键词
    line_keywords = ['趋势', '变化', '增长', '下降', '时间', '月份', '年份', '日期', '发展', 'trend', 'change',
                     'growth', 'time', 'month', 'year', 'date']
    if any(keyword in query_lower for keyword in line_keywords):
        return "line"

    # 散点图关键词
    scatter_keywords = ['相关', '关系', '分布图', '散布', 'correlation', 'relationship', 'scatter', 'distribution']
    if any(keyword in query_lower for keyword in scatter_keywords):
        return "scatter"

    # 面积图关键词
    area_keywords = ['面积', '区域', '填充', 'area', 'region', 'fill']
    if any(keyword in query_lower for keyword in area_keywords):
        return "area"

    # 默认返回柱状图
    return "bar"
