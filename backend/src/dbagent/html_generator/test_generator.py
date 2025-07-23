"""测试HTML生成器"""
from .models import ProcessedData, ChartType, DataPoint
from .generator import HTMLGenerator


def test_html_generator():
    """测试HTML生成器功能"""
    
    # 创建测试数据
    test_data = ProcessedData(
        chart_type=ChartType.BAR,
        sample_data=[
            DataPoint(name="A", value=10),
            DataPoint(name="B", value=20),
            DataPoint(name="C", value=15),
            DataPoint(name="D", value=25)
        ],
        original_query="显示各类别的销售数据"
    )
    
    # 创建生成器并生成HTML
    generator = HTMLGenerator()
    response = generator.generate_html_page(test_data)
    
    # 验证响应
    assert response.html_content is not None
    assert len(response.html_content) > 0
    assert "Data Visualization" in response.html_content
    assert "显示各类别的销售数据" in response.html_content
    
    # 验证图表配置
    assert response.chart_option is not None
    assert response.chart_option.title is not None
    assert response.chart_option.title.text == "Bar Chart"
    assert len(response.chart_option.series) == 1
    assert response.chart_option.series[0].type == "bar"
    
    print("✅ HTML生成器测试通过")


def test_pie_chart():
    """测试饼图生成"""
    test_data = ProcessedData(
        chart_type=ChartType.PIE,
        sample_data=[
            DataPoint(name="苹果", value=40),
            DataPoint(name="香蕉", value=30),
            DataPoint(name="橙子", value=20),
            DataPoint(name="葡萄", value=10)
        ],
        original_query="显示水果销售比例"
    )
    
    generator = HTMLGenerator()
    response = generator.generate_html_page(test_data)
    
    assert response.chart_option.series[0].type == "pie"
    assert len(response.chart_option.series[0].data) == 4
    
    print("✅ 饼图生成测试通过")


def test_line_chart():
    """测试折线图生成"""
    test_data = ProcessedData(
        chart_type=ChartType.LINE,
        sample_data=[
            DataPoint(name="1月", value=100),
            DataPoint(name="2月", value=120),
            DataPoint(name="3月", value=110),
            DataPoint(name="4月", value=140)
        ],
        original_query="显示月度趋势"
    )
    
    generator = HTMLGenerator()
    response = generator.generate_html_page(test_data)
    
    assert response.chart_option.series[0].type == "line"
    assert response.chart_option.series[0].smooth == True
    
    print("✅ 折线图生成测试通过")


if __name__ == "__main__":
    test_html_generator()
    test_pie_chart()
    test_line_chart()
    print("🎉 所有测试通过！")