from ..core.html_generator.generator import HTMLGenerator
from ..core.agent import DBAgent

class VisualizationResponse:
    def __init__(self, html_content: str, chart_type: str, data_points_count: int):
        self.html_content = html_content
        self.chart_type = chart_type
        self.data_points_count = data_points_count
        self.html_length = len(html_content)

class VisualizationService:
    def __init__(self):
        self.html_generator = HTMLGenerator()
    
    def generate_visualization(self, agent: DBAgent, query: str, chart_type: str) -> VisualizationResponse:
        """Generate visualization from agent query result"""
        # Convert query result to ProcessedData format
        processed_data = agent.to_processed_data(query, chart_type)
        
        # Generate HTML using the HTMLGenerator
        response = self.html_generator.generate_html_page(processed_data)
        
        return VisualizationResponse(
            html_content=response.html_content,
            chart_type=processed_data.chart_type.value if hasattr(processed_data.chart_type, 'value') else str(processed_data.chart_type),
            data_points_count=len(processed_data.sample_data)
        )