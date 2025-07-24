"""HTML生成器主模块"""
import json
from typing import Dict, Any
from .models import ProcessedData, HTMLGenerationResponse, EChartsOption
from .chart_generator import ChartOptionGenerator
from .config import HTMLTemplate


class HTMLGenerator:
    """HTML生成器"""
    
    def __init__(self):
        self.chart_generator = ChartOptionGenerator()
        self.template = HTMLTemplate()
    
    def generate_html_page(self, processed_data: ProcessedData) -> HTMLGenerationResponse:
        """
        生成完整的HTML页面
        
        Args:
            processed_data: 处理后的数据
            
        Returns:
            HTMLGenerationResponse: 包含HTML内容和图表配置的响应
        """
        # 生成ECharts配置
        chart_option = self.chart_generator.generate_option(
            processed_data.chart_type,
            processed_data.sample_data
        )
        
        # 生成HTML内容
        html_content = self._render_html_template(processed_data, chart_option)
        
        return HTMLGenerationResponse(
            html_content=html_content,
            chart_option=chart_option
        )
    
    def _render_html_template(self, processed_data: ProcessedData, chart_option: EChartsOption) -> str:
        """渲染HTML模板"""
        template = self.template.get_base_template()
        
        # 将EChartsOption转换为字典，然后序列化为JSON
        chart_option_dict = self._convert_option_to_dict(chart_option)
        
        return template.format(
            original_query=processed_data.original_query,
            chart_type=processed_data.chart_type.title(),
            data_points=len(processed_data.sample_data),
            echarts_option=json.dumps(chart_option_dict, indent=2, ensure_ascii=False)
        )
    
    def _convert_option_to_dict(self, chart_option: EChartsOption) -> Dict[str, Any]:
        """将EChartsOption转换为字典格式"""
        option_dict = {}
        
        # 处理标题
        if chart_option.title:
            title_dict = {"text": chart_option.title.text, "left": chart_option.title.left}
            if chart_option.title.textStyle:
                title_dict["textStyle"] = chart_option.title.textStyle.dict(exclude_none=True)
            option_dict["title"] = title_dict
        
        # 处理提示框
        if chart_option.tooltip:
            tooltip_dict = {"trigger": chart_option.tooltip.trigger}
            if chart_option.tooltip.backgroundColor:
                tooltip_dict["backgroundColor"] = chart_option.tooltip.backgroundColor
            if chart_option.tooltip.textStyle:
                tooltip_dict["textStyle"] = chart_option.tooltip.textStyle.dict(exclude_none=True)
            option_dict["tooltip"] = tooltip_dict
        
        # 处理图例
        if chart_option.legend:
            option_dict["legend"] = chart_option.legend.dict(exclude_none=True)
        
        # 处理坐标轴
        if chart_option.xAxis:
            option_dict["xAxis"] = chart_option.xAxis.dict(exclude_none=True)
        if chart_option.yAxis:
            option_dict["yAxis"] = chart_option.yAxis.dict(exclude_none=True)
        
        # 处理系列
        series_list = []
        for series in chart_option.series:
            series_dict = {
                "type": series.type,
                "data": series.data
            }
            
            # 添加可选属性
            optional_attrs = [
                "name", "smooth", "symbol", "symbolSize", "radius", "center",
                "avoidLabelOverlap"
            ]
            for attr in optional_attrs:
                value = getattr(series, attr, None)
                if value is not None:
                    series_dict[attr] = value
            
            # 处理样式对象
            if series.itemStyle:
                series_dict["itemStyle"] = self._convert_item_style(series.itemStyle)
            if series.lineStyle:
                series_dict["lineStyle"] = self._convert_line_style(series.lineStyle)
            if series.areaStyle:
                series_dict["areaStyle"] = self._convert_area_style(series.areaStyle)
            if series.emphasis:
                series_dict["emphasis"] = self._convert_emphasis(series.emphasis)
            if series.label:
                series_dict["label"] = self._convert_label(series.label)
            if series.labelLine:
                series_dict["labelLine"] = series.labelLine
            
            series_list.append(series_dict)
        
        option_dict["series"] = series_list
        return option_dict
    
    def _convert_item_style(self, item_style) -> Dict[str, Any]:
        """转换ItemStyle对象"""
        result = {}
        if item_style.color:
            if isinstance(item_style.color, str):
                result["color"] = item_style.color
            else:
                result["color"] = item_style.color.dict(exclude_none=True)
        
        optional_attrs = ["borderRadius", "borderColor", "borderWidth"]
        for attr in optional_attrs:
            value = getattr(item_style, attr, None)
            if value is not None:
                result[attr] = value
        
        return result
    
    def _convert_line_style(self, line_style) -> Dict[str, Any]:
        """转换LineStyle对象"""
        result = {}
        if line_style.width is not None:
            result["width"] = line_style.width
        if line_style.color:
            if isinstance(line_style.color, str):
                result["color"] = line_style.color
            else:
                result["color"] = line_style.color.dict(exclude_none=True)
        return result
    
    def _convert_area_style(self, area_style) -> Dict[str, Any]:
        """转换AreaStyle对象"""
        result = {}
        if area_style.color:
            if isinstance(area_style.color, str):
                result["color"] = area_style.color
            else:
                result["color"] = area_style.color.dict(exclude_none=True)
        return result
    
    def _convert_emphasis(self, emphasis) -> Dict[str, Any]:
        """转换Emphasis对象"""
        result = {}
        if emphasis.itemStyle:
            result["itemStyle"] = self._convert_item_style(emphasis.itemStyle)
        if emphasis.label:
            result["label"] = self._convert_label(emphasis.label)
        return result
    
    def _convert_label(self, label) -> Dict[str, Any]:
        """转换Label对象"""
        return label.dict(exclude_none=True)


# 便捷函数，保持向后兼容
def generate_html_page(processed_data: Dict[str, Any]) -> str:
    """
    生成HTML页面的便捷函数，保持与原有接口的兼容性
    
    Args:
        processed_data: 原有格式的处理数据
        
    Returns:
        str: HTML内容
    """
    # 转换为新的数据格式
    print(processed_data)
    pydantic_data = ProcessedData(**processed_data)
    
    # 使用新的生成器
    generator = HTMLGenerator()
    response = generator.generate_html_page(pydantic_data)
    
    return response.html_content