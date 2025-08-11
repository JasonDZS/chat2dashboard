"""
Data conversion utilities for converting database query results to chart-ready format.
"""

from typing import Dict, Any
import pandas as pd

from ..core.html_generator.models import ProcessedData, DataPoint, ChartType


def to_processed_data(query_result: Dict[str, Any], question: str, chart_type: str = "bar") -> ProcessedData:
    """
    Converts database query result to ProcessedData format for HTML generation.

    Args:
        query_result (Dict[str, Any]): Query result containing 'sql' and 'data' keys.
        question (str): The original question asked.
        chart_type (str): The chart type to use ("bar", "line", "pie", "scatter", "area").

    Returns:
        ProcessedData: Formatted data ready for HTML generation.
    """
    df = query_result["data"]
    
    # Convert DataFrame to DataPoint list
    sample_data = []
    
    if isinstance(df, pd.DataFrame) and not df.empty:
        # Get column names
        columns = df.columns.tolist()
        
        # Handle scatter chart differently - requires x,y coordinates
        if chart_type.lower() == "scatter":
            sample_data = _process_scatter_data(df, columns)
        else:
            # Handle other chart types (bar, line, pie, area)
            sample_data = _process_standard_data(df, columns)
    
    # Validate chart_type
    try:
        chart_type_enum = ChartType(chart_type.lower())
    except ValueError:
        chart_type_enum = ChartType.BAR
    
    print(chart_type_enum, sample_data, question)
    return ProcessedData(
        chart_type=chart_type_enum,
        sample_data=sample_data,
        original_query=question
    )


def _process_scatter_data(df: pd.DataFrame, columns: list) -> list[DataPoint]:
    """
    Process DataFrame for scatter chart format.
    
    Args:
        df (pd.DataFrame): The dataframe to process.
        columns (list): List of column names.
        
    Returns:
        list[DataPoint]: List of data points for scatter chart.
    """
    sample_data = []
    
    if len(columns) >= 2:
        # Use first two columns as x and y coordinates
        x_col, y_col = columns[0], columns[1]
        
        for idx, row in df.iterrows():
            x_val = row[x_col]
            y_val = row[y_col]
            
            # Smart conversion for x coordinate
            x_numeric = _convert_to_numeric(x_val, fallback=float(idx))
            
            # Smart conversion for y coordinate
            y_numeric = _convert_to_numeric(y_val, fallback=0.0)
            
            sample_data.append(DataPoint(
                x=x_numeric,
                y=y_numeric,
                name=f"({x_val}, {y_val})"
            ))
    elif len(columns) == 1:
        # Single column - use index as x and column as y
        y_col = columns[0]
        for idx, row in df.iterrows():
            y_val = row[y_col]
            
            # Smart conversion for y coordinate
            y_numeric = _convert_to_numeric(y_val, fallback=0.0)
            
            sample_data.append(DataPoint(
                x=float(int(idx)) if isinstance(idx, (int, float)) else float(hash(idx)),
                y=y_numeric,
                name=f"({idx}, {y_val})"
            ))
    
    return sample_data


def _process_standard_data(df: pd.DataFrame, columns: list) -> list[DataPoint]:
    """
    Process DataFrame for standard chart formats (bar, line, pie, area).
    
    Args:
        df (pd.DataFrame): The dataframe to process.
        columns (list): List of column names.
        
    Returns:
        list[DataPoint]: List of data points for standard charts.
    """
    sample_data = []
    
    if len(columns) >= 2:
        # Use first column as name and second as value
        name_col, value_col = columns[0], columns[1]
        
        for _, row in df.iterrows():
            sample_data.append(DataPoint(
                name=str(row[name_col]),
                value=_convert_to_numeric(row[value_col], fallback=0.0)
            ))
    elif len(columns) == 1:
        # Single column - use index as name and column as value
        value_col = columns[0]
        for idx, row in df.iterrows():
            sample_data.append(DataPoint(
                name=str(idx),
                value=_convert_to_numeric(row[value_col], fallback=0.0)
            ))
    
    return sample_data


def _convert_to_numeric(value: Any, fallback: float = 0.0) -> float:
    """
    Smart conversion of values to numeric format.
    
    Args:
        value: The value to convert.
        fallback (float): Fallback value if conversion fails.
        
    Returns:
        float: Converted numeric value.
    """
    try:
        if pd.notna(value):
            if isinstance(value, str):
                # Try direct numeric conversion first
                try:
                    return float(value)
                except ValueError:
                    # Try to parse as datetime
                    try:
                        return pd.to_datetime(value).timestamp()
                    except:
                        # Extract numbers from string if possible
                        import re
                        numbers = re.findall(r'-?\d+\.?\d*', value)
                        if numbers:
                            return float(numbers[0])
                        return fallback
            else:
                return float(value)
        else:
            return fallback
    except:
        return fallback