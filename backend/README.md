# Chat2Dashboard Backend 🎨

A FastAPI-based backend service that converts natural language queries into beautiful HTML visualizations using ECharts. This backend provides API endpoints for the Chat2Dashboard frontend application.

## Features

- 🗣️ Natural language processing for visualization requests
- 📊 Multiple chart types (bar, line, pie, scatter, area, radar)
- 🎨 Beautiful, responsive HTML output with animations
- ⚡ Fast FastAPI backend with CORS support
- 🔄 Real-time chart generation
- 🚀 Easy setup and deployment

## Requirements

- Python 3.11+
- uv package manager

## Quick Start

1. **Install dependencies with uv:**
   ```bash
   uv sync
   ```

2. **Run the application:**
   ```bash
   uv run python start.py
   ```

3. **Or run manually:**
   ```bash
   uv run python main.py
   ```

4. **Server will start at:**
   - API: `http://localhost:8000`
   - Web interface: `http://localhost:8000`

## API Endpoints

- `GET /` - Main web interface
- `POST /generate` - Generate visualization from natural language query
  - **Body**: `FormData` with `query` field
  - **Response**: HTML page with ECharts visualization

## Example API Usage

```bash
curl -X POST http://localhost:8000/generate \
  -F "query=Create a bar chart showing sales data for 6 months"
```

## Example Queries

- "Create a bar chart showing sales data for the last 6 months"
- "Generate a pie chart displaying market share by company"  
- "Show a line chart of temperature trends over time"
- "Create a scatter plot of price vs quality ratings"
- "Make an area chart showing revenue growth"
- "Create a radar chart for performance metrics"

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── start.py            # Easy startup script with auto-install
├── pyproject.toml      # uv project configuration
├── requirements.txt    # Python dependencies (legacy)
├── uv.lock            # uv lock file
├── src/
│   ├── nlp_processor.py     # Natural language processing logic
│   └── html_generator.py    # HTML/ECharts generation
├── templates/
│   └── index.html      # Main web interface template
└── README.md           # This documentation
```

## How It Works

1. **Input**: Natural language query received via POST request
2. **Processing**: NLP module (`nlp_processor.py`) extracts:
   - Chart type from keywords
   - Data requirements and categories
   - Time periods and data points
   - Styling preferences
3. **Generation**: HTML generator (`html_generator.py`) creates:
   - Complete HTML page with embedded ECharts
   - Responsive styling and animations
   - Interactive chart configuration
4. **Output**: Ready-to-display HTML visualization

## Supported Chart Types

- **Bar Chart**: Column/bar visualizations with gradients
- **Line Chart**: Smooth trend lines with area fills
- **Pie Chart**: Donut-style circular data distribution
- **Scatter Plot**: X/Y coordinate plotting with custom styling
- **Area Chart**: Filled area under curves
- **Radar Chart**: Multi-dimensional data visualization

## Technologies Used

- **Backend**: FastAPI 0.104.1, Python 3.11+
- **Package Management**: uv
- **Web Framework**: FastAPI with CORS middleware
- **Template Engine**: Jinja2 3.1.2
- **Server**: Uvicorn with standard extras
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualization**: ECharts 5.4+

## Development

### Dependencies

Core dependencies are managed via `pyproject.toml`:
- `fastapi==0.104.1` - Web framework
- `jinja2==3.1.2` - Template engine
- `pydantic==2.5.0` - Data validation
- `python-multipart==0.0.6` - Form data handling
- `uvicorn[standard]==0.24.0` - ASGI server

### Configuration

The server runs with:
- Host: `0.0.0.0` (all interfaces)
- Port: `8000`
- CORS enabled for all origins (development)
- Auto-reload in development mode