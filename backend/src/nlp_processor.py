import re
from typing import Dict, Any, List

def process_natural_language(query: str) -> Dict[str, Any]:
    """
    Process natural language input to extract visualization requirements
    """
    query_lower = query.lower()
    
    # Extract chart type
    chart_type = extract_chart_type(query_lower)
    
    # Extract data requirements
    data_info = extract_data_info(query_lower)
    
    # Extract styling preferences
    style_info = extract_style_info(query_lower)
    
    # Generate sample data based on the request
    sample_data = generate_sample_data(chart_type, data_info)
    
    return {
        "chart_type": chart_type,
        "data_info": data_info,
        "style_info": style_info,
        "sample_data": sample_data,
        "original_query": query
    }

def extract_chart_type(query: str) -> str:
    """Extract chart type from natural language query"""
    chart_patterns = {
        "bar": ["bar chart", "bar graph", "column chart", "histogram", "柱状图", "条形图"],
        "line": ["line chart", "line graph", "trend", "time series", "折线图", "曲线图"],
        "pie": ["pie chart", "pie graph", "donut", "circular", "饼图", "圆形图"],
        "scatter": ["scatter plot", "scatter chart", "correlation", "散点图", "气泡图"],
        "area": ["area chart", "area graph", "stacked area", "filled area", "面积图"],
        "radar": ["radar chart", "spider chart", "polar", "雷达图", "蜘蛛图"],
    }
    
    for chart_type, patterns in chart_patterns.items():
        for pattern in patterns:
            if pattern in query:
                return chart_type
    
    return "bar"  # default

def extract_data_info(query: str) -> Dict[str, Any]:
    """Extract data-related information from query"""
    info = {
        "categories": [],
        "metrics": [],
        "time_period": None,
        "data_points": 6  # default
    }
    
    # Extract common categories
    category_patterns = [
        "sales", "revenue", "profit", "temperature", "price", "quality",
        "market share", "performance", "growth", "users", "customers"
    ]
    
    for pattern in category_patterns:
        if pattern in query:
            info["categories"].append(pattern)
    
    # Extract time periods
    time_patterns = {
        "months": ["month", "monthly"],
        "weeks": ["week", "weekly"],
        "days": ["day", "daily"],
        "years": ["year", "yearly", "annual"]
    }
    
    for period, patterns in time_patterns.items():
        for pattern in patterns:
            if pattern in query:
                info["time_period"] = period
                break
    
    # Extract numbers for data points
    numbers = re.findall(r'\d+', query)
    if numbers:
        info["data_points"] = min(int(numbers[0]), 20)  # cap at 20
    
    return info

def extract_style_info(query: str) -> Dict[str, Any]:
    """Extract styling preferences from query"""
    return {
        "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
        "theme": "light"
    }

def generate_sample_data(chart_type: str, data_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate sample data based on chart type and data info"""
    import random
    
    data_points = data_info.get("data_points", 6)
    
    if chart_type == "pie":
        categories = ["Category A", "Category B", "Category C", "Category D", "Category E"]
        return [
            {"name": cat, "value": random.randint(10, 100)}
            for cat in categories[:data_points]
        ]
    
    elif chart_type in ["bar", "line", "area"]:
        if data_info.get("time_period") == "months":
            categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        else:
            categories = [f"Item {i+1}" for i in range(data_points)]
        
        return [
            {"name": cat, "value": random.randint(20, 200)}
            for cat in categories[:data_points]
        ]
    
    elif chart_type == "scatter":
        return [
            {"x": random.randint(1, 100), "y": random.randint(1, 100), "name": f"Point {i+1}"}
            for i in range(data_points)
        ]
    
    else:
        return [
            {"name": f"Data {i+1}", "value": random.randint(10, 100)}
            for i in range(data_points)
        ]