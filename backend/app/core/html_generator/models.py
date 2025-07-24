from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ChartType(str, Enum):
    """支持的图表类型"""
    BAR = "bar"
    LINE = "line" 
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"


class DataPoint(BaseModel):
    """通用数据点模型"""
    name: Optional[str] = None
    value: Optional[Union[int, float]] = None
    x: Optional[Union[int, float]] = None
    y: Optional[Union[int, float]] = None
    
    class Config:
        extra = "allow"


class ProcessedData(BaseModel):
    """处理后的数据结构"""
    chart_type: ChartType = Field(..., description="图表类型")
    sample_data: List[DataPoint] = Field(..., description="示例数据")
    original_query: str = Field(..., description="原始查询语句")
    
    class Config:
        use_enum_values = True


class ColorStop(BaseModel):
    """颜色渐变停止点"""
    offset: float = Field(..., ge=0, le=1, description="偏移量，0-1之间")
    color: str = Field(..., description="颜色值")


class LinearGradient(BaseModel):
    """线性渐变配置"""
    type: str = Field(default="linear", description="渐变类型")
    x: float = Field(default=0, description="起始点x坐标")
    y: float = Field(default=0, description="起始点y坐标") 
    x2: float = Field(default=0, description="结束点x坐标")
    y2: float = Field(default=1, description="结束点y坐标")
    colorStops: List[ColorStop] = Field(..., description="颜色停止点列表")


class RadialGradient(BaseModel):
    """径向渐变配置"""
    type: str = Field(default="radial", description="渐变类型")
    x: float = Field(default=0.5, description="中心点x坐标")
    y: float = Field(default=0.5, description="中心点y坐标")
    r: float = Field(default=0.5, description="半径")
    colorStops: List[ColorStop] = Field(..., description="颜色停止点列表")


class ItemStyle(BaseModel):
    """图表项样式配置"""
    color: Optional[Union[str, LinearGradient, RadialGradient]] = None
    borderRadius: Optional[int] = None
    borderColor: Optional[str] = None
    borderWidth: Optional[int] = None


class LineStyle(BaseModel):
    """线条样式配置"""
    width: Optional[int] = None
    color: Optional[Union[str, LinearGradient]] = None


class AreaStyle(BaseModel):
    """区域样式配置"""
    color: Optional[Union[str, LinearGradient]] = None


class TextStyle(BaseModel):
    """文本样式配置"""
    fontSize: Optional[int] = None
    fontWeight: Optional[str] = None
    color: Optional[str] = None


class Title(BaseModel):
    """标题配置"""
    text: str = Field(..., description="标题文本")
    left: str = Field(default="center", description="水平位置")
    textStyle: Optional[TextStyle] = None


class Tooltip(BaseModel):
    """提示框配置"""
    trigger: str = Field(default="axis", description="触发类型")
    backgroundColor: Optional[str] = None
    textStyle: Optional[TextStyle] = None


class Legend(BaseModel):
    """图例配置"""
    bottom: Optional[str] = None
    left: Optional[str] = None


class Axis(BaseModel):
    """坐标轴配置"""
    type: str = Field(..., description="坐标轴类型")
    data: Optional[List[str]] = None
    name: Optional[str] = None
    boundaryGap: Optional[bool] = None
    axisLabel: Optional[Dict[str, Any]] = None


class Label(BaseModel):
    """标签配置"""
    show: bool = Field(default=True, description="是否显示标签")
    position: Optional[str] = None
    formatter: Optional[str] = None
    fontSize: Optional[str] = None
    fontWeight: Optional[str] = None


class Emphasis(BaseModel):
    """高亮状态配置"""
    itemStyle: Optional[ItemStyle] = None
    label: Optional[Label] = None


class Series(BaseModel):
    """系列配置"""
    name: Optional[str] = None
    type: str = Field(..., description="系列类型")
    data: List[Any] = Field(..., description="数据")
    itemStyle: Optional[ItemStyle] = None
    lineStyle: Optional[LineStyle] = None
    areaStyle: Optional[AreaStyle] = None
    emphasis: Optional[Emphasis] = None
    smooth: Optional[bool] = None
    symbol: Optional[str] = None
    symbolSize: Optional[int] = None
    radius: Optional[List[str]] = None
    center: Optional[List[str]] = None
    avoidLabelOverlap: Optional[bool] = None
    label: Optional[Label] = None
    labelLine: Optional[Dict[str, bool]] = None


class EChartsOption(BaseModel):
    """ECharts完整配置"""
    title: Optional[Title] = None
    tooltip: Optional[Tooltip] = None
    legend: Optional[Legend] = None
    xAxis: Optional[Axis] = None
    yAxis: Optional[Axis] = None
    series: List[Series] = Field(..., description="系列列表")


class HTMLGenerationRequest(BaseModel):
    """HTML生成请求"""
    processed_data: ProcessedData = Field(..., description="处理后的数据")


class HTMLGenerationResponse(BaseModel):
    """HTML生成响应"""
    html_content: str = Field(..., description="生成的HTML内容")
    chart_option: EChartsOption = Field(..., description="ECharts配置")