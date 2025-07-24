# Chat2Dashboard Backend 🎨

A FastAPI-based backend service that converts natural language queries into beautiful HTML visualizations using ECharts and AI-powered SQL generation. This backend provides API endpoints for database interaction, visualization generation, and schema management.

## Features

- 🤖 AI-powered SQL generation using Vanna + OpenAI/Qwen models
- 🗣️ Natural language to SQL conversion and execution
- 📊 Multiple chart types (bar, line, pie, scatter, area, radar)
- 🎨 Beautiful, responsive HTML output with ECharts animations
- 📁 File upload and database management (SQLite)
- 🔧 Schema management with training data support
- 📝 Request logging and system monitoring
- ⚡ Fast FastAPI backend with CORS support
- 🔄 Real-time chart generation
- 🚀 Easy setup and deployment

## Requirements

- Python 3.11+
- uv package manager
- OpenAI API key (or compatible API)
- SQLite (built-in with Python)

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

### Main Routes
- `GET /` - Main web interface
- `POST /generate` - Generate visualization from natural language query (legacy)
- `POST /upload-files` - Upload data files to create databases (legacy)

### API v1 Routes (`/api/v1`)

#### Visualization
- `POST /api/v1/visualization` - Generate charts from natural language queries
- `GET /api/v1/visualization/types` - Get supported chart types

#### Database Management
- `GET /api/v1/databases` - List all available databases
- `POST /api/v1/databases/upload` - Upload files to create new database
- `GET /api/v1/databases/{db_name}/schema` - Get database schema
- `GET /api/v1/databases/{db_name}/schema-json` - Get schema JSON with training data
- `PUT /api/v1/databases/{db_name}/schema-json` - Update schema JSON

#### Schema & Training Data
- `POST /api/v1/schema/{db_name}/sql` - Add SQL training data
- `DELETE /api/v1/schema/{db_name}/sql/{index}` - Delete SQL training data
- `POST /api/v1/schema/{db_name}/generate-sql` - Generate SQL training data with AI

#### Logging & Monitoring
- `GET /api/v1/logs/requests` - Get request logs
- `GET /api/v1/logs/requests/{request_id}` - Get specific request log
- `GET /api/v1/logs/stats` - Get logging statistics

#### System
- `GET /api/v1/health` - Health check
- `GET /api/v1/status` - System status

## Example API Usage

```bash
# Generate visualization (legacy endpoint)
curl -X POST http://localhost:8000/generate \
  -F "query=Create a bar chart showing sales data for 6 months" \
  -F "db_name=mydata"

# Generate visualization (new API)
curl -X POST http://localhost:8000/api/v1/visualization \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me sales by month", "db_name": "mydata", "chart_type": "bar"}'

# Upload data files
curl -X POST http://localhost:8000/api/v1/databases/upload \
  -F "files=@data.csv" \
  -F "db_name=mydata"

# List databases
curl http://localhost:8000/api/v1/databases
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
├── main.py                    # Legacy entry point
├── start.py                   # Easy startup script
├── pyproject.toml             # uv project configuration
├── requirements.txt           # Python dependencies (legacy)
├── uv.lock                   # uv lock file
├── app/
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Application configuration
│   ├── api/
│   │   └── v1/
│   │       ├── routes.py     # API router setup
│   │       ├── database.py   # Database management endpoints
│   │       ├── visualization.py # Chart generation endpoints
│   │       ├── schema.py     # Schema management endpoints
│   │       ├── logs.py       # Logging endpoints
│   │       └── system.py     # System status endpoints
│   ├── core/
│   │   ├── agent.py          # DBAgent with Vanna integration
│   │   ├── database.py       # Database utilities
│   │   ├── sql_generator.py  # AI-powered SQL generation
│   │   ├── logging.py        # Logging utilities
│   │   └── html_generator/   # Chart generation modules
│   │       ├── generator.py  # Main HTML generator
│   │       ├── chart_generator.py # Chart-specific logic
│   │       ├── models.py     # Data models
│   │       └── config.py     # Chart configuration
│   ├── models/
│   │   ├── requests.py       # Request models
│   │   └── responses.py      # Response models
│   ├── services/
│   │   ├── agent_service.py  # Agent service wrapper
│   │   ├── sql_service.py    # SQL generation service
│   │   ├── logging_service.py # Logging service
│   │   └── visualization_service.py # Visualization service
│   └── utils/
│       └── chart_utils.py    # Chart utilities
├── databases/
│   └── [db_name]/
│       ├── [db_name].db      # SQLite database files
│       ├── schema.json       # Schema and training data
│       └── cache/           # Vanna vector store cache
├── logs/
│   └── requests.db          # Request logging database
├── templates/
│   └── index.html           # Main web interface template
└── README.md                # This documentation
```

## How It Works

1. **Input**: Natural language query with database name received via API
2. **AI Processing**: DBAgent (`core/agent.py`) using Vanna framework:
   - Converts natural language to SQL using OpenAI/Qwen models
   - Executes SQL against SQLite database
   - Returns structured data results
3. **Data Processing**: Convert query results to chart-ready format:
   - Handle different data types and structures
   - Smart data type inference and conversion
   - Support for scatter plots, time series, categorical data
4. **Chart Generation**: HTML generator creates:
   - Complete HTML page with embedded ECharts
   - Responsive styling and animations
   - Interactive chart configuration
5. **Output**: Ready-to-display HTML visualization

### Database Management Flow

1. **File Upload**: CSV/Excel files uploaded via API
2. **Database Creation**: Files converted to SQLite database
3. **Schema Generation**: Automatic table schema detection
4. **Training Data**: AI generates question-SQL pairs for better accuracy
5. **Vector Store**: Vanna creates embeddings for semantic matching

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
- **AI Framework**: Vanna + OpenAI/Qwen models
- **Database**: SQLite with pandas integration
- **Vector Store**: ChromaDB for semantic search
- **Web Framework**: FastAPI with CORS middleware
- **Template Engine**: Jinja2 3.1.2
- **Server**: Uvicorn with standard extras
- **Data Processing**: pandas, numpy, openpyxl
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
- `vanna[chromadb,openai]>=0.7.9` - AI-powered SQL generation
- `openai>=1.97.1` - OpenAI API client
- `pandas==2.1.4` - Data manipulation
- `numpy==1.26.4` - Numerical computing
- `openpyxl==3.1.2` - Excel file support
- `tiktoken>=0.9.0` - Token counting for AI models
- `tenacity>=9.1.2` - Retry logic
- `psutil>=7.0.0` - System monitoring

### Configuration

The server runs with:
- Host: `0.0.0.0` (all interfaces)
- Port: `8000`
- CORS enabled for all origins (development)
- Auto-reload in development mode

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key (required)
- `OPENAI_API_BASE` - Custom OpenAI API base URL (optional, defaults to official API)

### Database Storage

- SQLite databases stored in `databases/{db_name}/{db_name}.db`
- Schema and training data in `databases/{db_name}/schema.json`
- Vanna vector store cache in `databases/{db_name}/cache/`
- Request logs in `logs/requests.db`