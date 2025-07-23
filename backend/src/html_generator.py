from typing import Dict, Any, List
import json

def generate_html_page(processed_data: Dict[str, Any]) -> str:
    """
    Generate complete HTML page with ECharts visualization
    """
    chart_type = processed_data["chart_type"]
    sample_data = processed_data["sample_data"]
    original_query = processed_data["original_query"]
    
    # Generate ECharts option based on chart type
    echarts_option = generate_echarts_option(chart_type, sample_data)
    
    html_template = f"""
<!DOCTYPE html>
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
            <p><strong>Chart Type:</strong> {chart_type.title()} Chart</p>
            <p><strong>Data Points:</strong> {len(sample_data)}</p>
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
        var option = {json.dumps(echarts_option, indent=2)};
        
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
</html>
    """
    
    return html_template

def generate_echarts_option(chart_type: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate ECharts option configuration based on chart type and data
    """
    base_option = {
        "title": {
            "text": f"{chart_type.title()} Chart",
            "left": "center",
            "textStyle": {
                "fontSize": 24,
                "fontWeight": "normal"
            }
        },
        "tooltip": {
            "trigger": "item" if chart_type == "pie" else "axis",
            "backgroundColor": "rgba(50,50,50,0.8)",
            "textStyle": {
                "color": "#fff"
            }
        },
        "legend": {
            "bottom": "5%",
            "left": "center"
        }
    }
    
    if chart_type == "bar":
        base_option.update({
            "xAxis": {
                "type": "category",
                "data": [item["name"] for item in data],
                "axisLabel": {
                    "rotate": 45 if len(data) > 6 else 0
                }
            },
            "yAxis": {
                "type": "value"
            },
            "series": [{
                "data": [item["value"] for item in data],
                "type": "bar",
                "itemStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "#83bff6"},
                            {"offset": 0.5, "color": "#188df0"},
                            {"offset": 1, "color": "#188df0"}
                        ]
                    }
                },
                "emphasis": {
                    "itemStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": "#2378f7"},
                                {"offset": 0.7, "color": "#2378f7"},
                                {"offset": 1, "color": "#83bff6"}
                            ]
                        }
                    }
                }
            }]
        })
    
    elif chart_type == "line":
        base_option.update({
            "xAxis": {
                "type": "category",
                "data": [item["name"] for item in data],
                "boundaryGap": False
            },
            "yAxis": {
                "type": "value"
            },
            "series": [{
                "data": [item["value"] for item in data],
                "type": "line",
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 8,
                "lineStyle": {
                    "width": 3,
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 1, "y2": 0,
                        "colorStops": [
                            {"offset": 0, "color": "#13C2C2"},
                            {"offset": 1, "color": "#6BCF7F"}
                        ]
                    }
                },
                "itemStyle": {
                    "color": "#13C2C2"
                },
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(19, 194, 194, 0.3)"},
                            {"offset": 1, "color": "rgba(19, 194, 194, 0.1)"}
                        ]
                    }
                }
            }]
        })
    
    elif chart_type == "pie":
        base_option.update({
            "series": [{
                "name": "Data",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["50%", "45%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2
                },
                "label": {
                    "show": True,
                    "position": "outside",
                    "formatter": "{b}: {c} ({d}%)"
                },
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": "16",
                        "fontWeight": "bold"
                    }
                },
                "labelLine": {
                    "show": True
                },
                "data": data
            }]
        })
    
    elif chart_type == "scatter":
        base_option.update({
            "xAxis": {
                "type": "value",
                "name": "X Axis"
            },
            "yAxis": {
                "type": "value",
                "name": "Y Axis"
            },
            "series": [{
                "data": [[item["x"], item["y"]] for item in data],
                "type": "scatter",
                "symbolSize": 20,
                "itemStyle": {
                    "color": {
                        "type": "radial",
                        "x": 0.5, "y": 0.5, "r": 0.5,
                        "colorStops": [
                            {"offset": 0, "color": "#ffd43b"},
                            {"offset": 1, "color": "#ff6b35"}
                        ]
                    }
                },
                "emphasis": {
                    "itemStyle": {
                        "color": "#ff4757"
                    }
                }
            }]
        })
    
    elif chart_type == "area":
        base_option.update({
            "xAxis": {
                "type": "category",
                "data": [item["name"] for item in data],
                "boundaryGap": False
            },
            "yAxis": {
                "type": "value"
            },
            "series": [{
                "data": [item["value"] for item in data],
                "type": "line",
                "smooth": True,
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(255, 158, 68, 0.8)"},
                            {"offset": 1, "color": "rgba(255, 158, 68, 0.1)"}
                        ]
                    }
                },
                "lineStyle": {
                    "color": "#ff9e44"
                },
                "itemStyle": {
                    "color": "#ff9e44"
                }
            }]
        })
    
    return base_option