import datetime
from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse

from ...services.visualization_service import VisualizationService
from ...services.agent_service import AgentService
from ...utils.chart_utils import infer_chart_type_from_query

router = APIRouter(prefix="/visualization", tags=["visualization"])

@router.post("/generate", response_class=HTMLResponse)
async def generate_visualization(
    request: Request, 
    query: str = Form(...), 
    db_name: str = Form(...),
    chart_type: str = Form(default=None)
):
    """Generate visualization from query"""
    start_time = datetime.datetime.now()
    generated_sql = None
    response_data = None
    error_message = None
    
    try:
        # Get database agent instance
        agent_service = AgentService()
        agent = agent_service.get_agent(db_name)
        
        # If chart type not specified, infer from query
        if chart_type is None:
            chart_type = infer_chart_type_from_query(query)
        
        # Generate visualization
        visualization_service = VisualizationService()
        response = visualization_service.generate_visualization(agent, query, chart_type)
        
        # Extract SQL from agent if available
        if hasattr(agent, 'last_generated_sql'):
            generated_sql = agent.last_generated_sql
        
        # Prepare response data for logging
        response_data = {
            "chart_type": response.chart_type,
            "data_points_count": response.data_points_count,
            "html_length": response.html_length
        }
        
        # Calculate execution time
        execution_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
        
        # Log successful request
        from ...services.logging_service import LoggingService
        logging_service = LoggingService()
        logging_service.log_request(
            query=query,
            db_name=db_name,
            chart_type=chart_type,
            response_status="success",
            generated_sql=generated_sql,
            response_data=response_data,
            execution_time_ms=int(execution_time)
        )
        
        return HTMLResponse(content=response.html_content)
    
    except Exception as e:
        error_message = str(e)
        execution_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
        
        # Log failed request
        from ...services.logging_service import LoggingService
        logging_service = LoggingService()
        logging_service.log_request(
            query=query,
            db_name=db_name,
            chart_type=chart_type,
            response_status="error",
            generated_sql=generated_sql,
            error_message=error_message,
            execution_time_ms=int(execution_time)
        )
        
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 
            status_code=500
        )