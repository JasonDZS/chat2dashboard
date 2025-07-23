"""HTML生成器配置"""
from typing import Dict, List
from .models import ColorStop, LinearGradient, RadialGradient


class ChartColorSchemes:
    """图表颜色方案"""
    
    # 条形图渐变色
    BAR_GRADIENT = LinearGradient(
        type="linear",
        x=0, y=0, x2=0, y2=1,
        colorStops=[
            ColorStop(offset=0, color="#83bff6"),
            ColorStop(offset=0.5, color="#188df0"), 
            ColorStop(offset=1, color="#188df0")
        ]
    )
    
    BAR_EMPHASIS_GRADIENT = LinearGradient(
        type="linear",
        x=0, y=0, x2=0, y2=1,
        colorStops=[
            ColorStop(offset=0, color="#2378f7"),
            ColorStop(offset=0.7, color="#2378f7"),
            ColorStop(offset=1, color="#83bff6")
        ]
    )
    
    # 折线图渐变色
    LINE_GRADIENT = LinearGradient(
        type="linear",
        x=0, y=0, x2=1, y2=0,
        colorStops=[
            ColorStop(offset=0, color="#13C2C2"),
            ColorStop(offset=1, color="#6BCF7F")
        ]
    )
    
    LINE_AREA_GRADIENT = LinearGradient(
        type="linear", 
        x=0, y=0, x2=0, y2=1,
        colorStops=[
            ColorStop(offset=0, color="rgba(19, 194, 194, 0.3)"),
            ColorStop(offset=1, color="rgba(19, 194, 194, 0.1)")
        ]
    )
    
    # 散点图径向渐变
    SCATTER_RADIAL = RadialGradient(
        type="radial",
        x=0.5, y=0.5, r=0.5,
        colorStops=[
            ColorStop(offset=0, color="#ffd43b"),
            ColorStop(offset=1, color="#ff6b35")
        ]
    )
    
    # 面积图渐变色
    AREA_GRADIENT = LinearGradient(
        type="linear",
        x=0, y=0, x2=0, y2=1,
        colorStops=[
            ColorStop(offset=0, color="rgba(255, 158, 68, 0.8)"),
            ColorStop(offset=1, color="rgba(255, 158, 68, 0.1)")
        ]
    )


class HTMLTemplate:
    """HTML模板配置"""
    
    @staticmethod
    def get_base_template() -> str:
        """获取基础HTML模板"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
        }}
        .query-info {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            margin-top: 20px;
            border-radius: 8px;
            font-style: italic;
        }}
        .chart-container {{
            padding: 40px;
        }}
        #chart {{
            width: 100%;
            height: 500px;
            border-radius: 8px;
        }}
        .metadata {{
            background: #f8f9fa;
            padding: 20px;
            border-top: 1px solid #dee2e6;
        }}
        .metadata h3 {{
            margin-top: 0;
            color: #495057;
        }}
        .metadata p {{
            margin: 5px 0;
            color: #6c757d;
        }}
        .btn-container {{
            text-align: center;
            padding: 20px;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
            display: inline-block;
            transition: transform 0.2s;
        }}
        .btn:hover {{
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Data Visualization</h1>
            <div class="query-info">
                <strong>Your Query:</strong> "{original_query}"
            </div>
        </div>
        
        <div class="chart-container">
            <div id="chart"></div>
        </div>
        
        <div class="metadata">
            <h3>📊 Chart Information</h3>
            <p><strong>Chart Type:</strong> {chart_type} Chart</p>
            <p><strong>Data Points:</strong> {data_points}</p>
            <p><strong>Generated:</strong> Automatically from natural language query</p>
        </div>
        
        <div class="btn-container">
            <a href="/" class="btn">← Create Another Visualization</a>
        </div>
    </div>

    <script>
        // Initialize ECharts
        var chartDom = document.getElementById('chart');
        var myChart = echarts.init(chartDom);
        
        // Chart configuration
        var option = {echarts_option};
        
        // Apply configuration
        myChart.setOption(option);
        
        // Make chart responsive
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
        
        // Add animation and interactivity
        myChart.on('click', function(params) {{
            console.log('Clicked:', params);
        }});
    </script>
</body>
</html>"""


class ChartDefaults:
    """图表默认配置"""
    
    DEFAULT_TITLE_STYLE = {
        "fontSize": 24,
        "fontWeight": "normal"
    }
    
    DEFAULT_TOOLTIP_STYLE = {
        "backgroundColor": "rgba(50,50,50,0.8)",
        "textStyle": {
            "color": "#fff"
        }
    }
    
    DEFAULT_LEGEND_POSITION = {
        "bottom": "5%",
        "left": "center"
    }
    
    PIE_CHART_CONFIG = {
        "radius": ["40%", "70%"],
        "center": ["50%", "45%"],
        "avoidLabelOverlap": False,
        "itemStyle": {
            "borderRadius": 10,
            "borderColor": "#fff",
            "borderWidth": 2
        }
    }