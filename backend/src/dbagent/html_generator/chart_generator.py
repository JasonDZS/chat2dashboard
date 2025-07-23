"""图表生成器"""
from typing import Dict, Any, List
from .models import (
    EChartsOption, ChartType, DataPoint, Title, Tooltip, Legend,
    Axis, Series, ItemStyle, LineStyle, AreaStyle, Label, Emphasis,
    TextStyle
)
from .config import ChartColorSchemes, ChartDefaults


class ChartOptionGenerator:
    """ECharts配置生成器"""
    
    def __init__(self):
        self.color_schemes = ChartColorSchemes()
        self.defaults = ChartDefaults()
    
    def generate_option(self, chart_type: ChartType, data: List[DataPoint]) -> EChartsOption:
        """生成ECharts配置"""
        base_option = self._create_base_option(chart_type)
        
        if chart_type == ChartType.BAR:
            return self._generate_bar_chart(base_option, data)
        elif chart_type == ChartType.LINE:
            return self._generate_line_chart(base_option, data)
        elif chart_type == ChartType.PIE:
            return self._generate_pie_chart(base_option, data)
        elif chart_type == ChartType.SCATTER:
            return self._generate_scatter_chart(base_option, data)
        elif chart_type == ChartType.AREA:
            return self._generate_area_chart(base_option, data)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
    
    def _create_base_option(self, chart_type: ChartType) -> Dict[str, Any]:
        """创建基础配置"""
        return {
            "title": Title(
                text=f"{chart_type.title()} Chart",
                left="center",
                textStyle=TextStyle(**self.defaults.DEFAULT_TITLE_STYLE)
            ),
            "tooltip": Tooltip(
                trigger="item" if chart_type == ChartType.PIE else "axis",
                **self.defaults.DEFAULT_TOOLTIP_STYLE
            ),
            "legend": Legend(**self.defaults.DEFAULT_LEGEND_POSITION)
        }
    
    def _generate_bar_chart(self, base_option: Dict[str, Any], data: List[DataPoint]) -> EChartsOption:
        """生成条形图"""
        names = [item.name for item in data if item.name is not None]
        values = [item.value for item in data if item.value is not None]
        
        base_option.update({
            "xAxis": Axis(
                type="category",
                data=names,
                axisLabel={"rotate": 45 if len(data) > 6 else 0}
            ),
            "yAxis": Axis(type="value"),
            "series": [Series(
                type="bar",
                data=values,
                itemStyle=ItemStyle(color=self.color_schemes.BAR_GRADIENT),
                emphasis=Emphasis(
                    itemStyle=ItemStyle(color=self.color_schemes.BAR_EMPHASIS_GRADIENT)
                )
            )]
        })
        
        return EChartsOption(**base_option)
    
    def _generate_line_chart(self, base_option: Dict[str, Any], data: List[DataPoint]) -> EChartsOption:
        """生成折线图"""
        names = [item.name for item in data if item.name is not None]
        values = [item.value for item in data if item.value is not None]
        
        base_option.update({
            "xAxis": Axis(
                type="category",
                data=names,
                boundaryGap=False
            ),
            "yAxis": Axis(type="value"),
            "series": [Series(
                type="line",
                data=values,
                smooth=True,
                symbol="circle",
                symbolSize=8,
                lineStyle=LineStyle(
                    width=3,
                    color=self.color_schemes.LINE_GRADIENT
                ),
                itemStyle=ItemStyle(color="#13C2C2"),
                areaStyle=AreaStyle(color=self.color_schemes.LINE_AREA_GRADIENT)
            )]
        })
        
        return EChartsOption(**base_option)
    
    def _generate_pie_chart(self, base_option: Dict[str, Any], data: List[DataPoint]) -> EChartsOption:
        """生成饼图"""
        pie_data = []
        for item in data:
            if item.name is not None and item.value is not None:
                pie_data.append({"name": item.name, "value": item.value})
        
        base_option.update({
            "series": [Series(
                name="Data",
                type="pie",
                data=pie_data,
                **self.defaults.PIE_CHART_CONFIG,
                label=Label(
                    show=True,
                    position="outside",
                    formatter="{b}: {c} ({d}%)"
                ),
                emphasis=Emphasis(
                    label=Label(
                        show=True,
                        fontSize="16",
                        fontWeight="bold"
                    )
                ),
                labelLine={"show": True}
            )]
        })
        
        return EChartsOption(**base_option)
    
    def _generate_scatter_chart(self, base_option: Dict[str, Any], data: List[DataPoint]) -> EChartsOption:
        """生成散点图"""
        scatter_data = []
        for item in data:
            if item.x is not None and item.y is not None:
                scatter_data.append([item.x, item.y])
        
        base_option.update({
            "xAxis": Axis(type="value", name="X Axis"),
            "yAxis": Axis(type="value", name="Y Axis"),
            "series": [Series(
                type="scatter",
                data=scatter_data,
                symbolSize=20,
                itemStyle=ItemStyle(color=self.color_schemes.SCATTER_RADIAL),
                emphasis=Emphasis(
                    itemStyle=ItemStyle(color="#ff4757")
                )
            )]
        })
        
        return EChartsOption(**base_option)
    
    def _generate_area_chart(self, base_option: Dict[str, Any], data: List[DataPoint]) -> EChartsOption:
        """生成面积图"""
        names = [item.name for item in data if item.name is not None]
        values = [item.value for item in data if item.value is not None]
        
        base_option.update({
            "xAxis": Axis(
                type="category",
                data=names,
                boundaryGap=False
            ),
            "yAxis": Axis(type="value"),
            "series": [Series(
                type="line",
                data=values,
                smooth=True,
                areaStyle=AreaStyle(color=self.color_schemes.AREA_GRADIENT),
                lineStyle=LineStyle(color="#ff9e44"),
                itemStyle=ItemStyle(color="#ff9e44")
            )]
        })
        
        return EChartsOption(**base_option)