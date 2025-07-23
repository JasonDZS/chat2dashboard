# Chat2Dashboard

A powerful web application that converts natural language queries into beautiful, interactive data visualizations through AI. Create multiple charts on a canvas, arrange them as needed, and build comprehensive dashboards through simple conversation.


<video src="https://github.com/user-attachments/assets/c2ec5d9e-17bd-4404-b215-a06e6ef79e00"></video>


## 🚀 Features

### 🎯 Core Features
- **Natural Language Processing**: Convert plain text requests into stunning visualizations
- **Interactive Canvas**: Click anywhere to create new visualization containers
- **Multi-Container Support**: Display multiple charts simultaneously on one canvas
- **Drag & Drop**: Move containers around the canvas freely
- **Resizable Containers**: Adjust container sizes with mouse interactions
- **Auto Layout**: Automatically organize multiple containers with smart positioning
- **Real-time Generation**: Instant chart creation powered by AI backend

### 📊 Supported Chart Types
- **Bar Charts**: Column/bar visualizations with gradients
- **Line Charts**: Smooth trend lines with area fills
- **Pie Charts**: Donut-style circular data distribution
- **Scatter Plots**: X/Y coordinate plotting with custom styling
- **Area Charts**: Filled area under curves
- **Radar Charts**: Multi-dimensional data visualization

### ✨ Visual Features
- Beautiful, responsive design
- Smooth animations and transitions
- Professional chart styling with ECharts
- Mobile-friendly interface
- Modern React UI components

## 🏗️ Architecture

```
Chat2Dashboard/
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx          # Main canvas application
│   │   ├── ChartComponent.jsx # Individual chart container
│   │   ├── App.css          # Main styles
│   │   └── ...
│   ├── public/
│   │   └── examples/        # Sample chart HTML files
│   └── package.json
├── backend/                  # FastAPI backend
│   ├── src/
│   │   ├── nlp_processor.py # Natural language processing
│   │   └── html_generator.py # ECharts HTML generation
│   ├── templates/
│   │   └── index.html       # Backend web interface
│   ├── main.py              # FastAPI application
│   ├── start.py             # Easy startup script
│   └── pyproject.toml       # Dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites
- **Frontend**: Node.js 18+ and npm
- **Backend**: Python 3.11+ and uv package manager

### 1. Backend Setup

```bash
cd backend
uv sync
uv run python start.py
```

Backend will start at: `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will start at: `http://localhost:5173`

### 3. Start Creating!

1. Open `http://localhost:5173` in your browser
2. Click anywhere on the canvas
3. Enter a natural language query like:
   - "Create a bar chart showing monthly sales data"
   - "Generate a pie chart for market share analysis"
   - "Show a line chart of temperature trends"
4. Watch your visualization appear instantly!
5. Drag, resize, and arrange containers as needed
6. Use "Auto Layout" button for automatic layout

## 💡 Example Queries

### Business Analytics
- "Create a bar chart showing quarterly revenue for the last year"
- "Generate a pie chart displaying market share by company"
- "Show a line chart of customer growth over 12 months"

### Performance Metrics
- "Create a radar chart for team performance metrics"
- "Generate a scatter plot showing price vs quality ratings"
- "Show an area chart of website traffic trends"

### Data Analysis
- "Create a histogram of user age distribution"
- "Generate a time series chart for stock prices"
- "Show a correlation matrix as a heatmap"

## 📚 API Reference

### Backend Endpoints

- **GET** `/` - Web interface for testing
- **POST** `/generate` - Generate visualization from natural language
  - **Content-Type**: `multipart/form-data`
  - **Body**: `query` (string) - Natural language description
  - **Response**: HTML page with ECharts visualization

### Example API Call

```bash
curl -X POST http://localhost:8000/generate \
  -F "query=Create a bar chart showing sales data for 6 months"
```

## 🛠️ Development

### Frontend Development

```bash
cd frontend
npm run dev      # Start development server
npm run build    # Build for production
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

**Tech Stack:**
- React 19.1.0
- Vite 7.0.4
- ECharts 5.6.0
- Modern ES modules

### Backend Development

```bash
cd backend
uv sync                    # Install dependencies
uv run python main.py      # Start FastAPI server
uv run python start.py     # Start with auto-install
```

**Tech Stack:**
- FastAPI 0.104.1
- Python 3.11+
- Jinja2 templates
- Uvicorn server
- ECharts 5.4+

### Project Structure Details

#### Frontend Components
- **`App.jsx`**: Main canvas component with container management
- **`ChartComponent.jsx`**: Individual chart rendering with API integration
- **Canvas Features**: Click-to-create, drag-and-drop, resize handles
- **State Management**: React hooks for container positioning and sizing

#### Backend Modules
- **`nlp_processor.py`**: Extracts chart type, data requirements, and styling from natural language
- **`html_generator.py`**: Creates complete HTML pages with ECharts configurations
- **Template System**: Jinja2 templates for consistent HTML generation

## ⚙️ How It Works

### 1. User Interaction
- User clicks on canvas → Dialog appears
- User enters natural language query
- Frontend sends request to backend API

### 2. AI Processing
- Backend processes natural language with NLP
- Extracts chart type, data patterns, and styling preferences
- Generates sample data based on query context

### 3. Visualization Generation
- Creates ECharts configuration object
- Generates complete HTML page with embedded chart
- Applies responsive styling and animations

### 4. Frontend Display
- Receives HTML content from backend
- Extracts ECharts configuration
- Renders chart in resizable container
- Enables drag-and-drop positioning

## 🎨 Advanced Features

### Container Management
- **Selection**: Click containers to select/deselect
- **Multi-container**: Unlimited containers on one canvas
- **Persistence**: Containers maintain state during session
- **Responsive**: Charts automatically resize with containers

### Auto Layout System
- **Smart Positioning**: Automatically arranges containers in grid
- **Collision Avoidance**: Prevents container overlap
- **Responsive Grid**: Adapts to canvas size
- **One-click Organization**: "Auto Layout" button for instant arrangement

### Chart Customization
- **Dynamic Sizing**: Charts adapt to container dimensions
- **Professional Styling**: Consistent color schemes and typography
- **Interactive Elements**: Hover effects, click handlers, animations
- **Mobile Optimization**: Touch-friendly interactions

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 💬 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/JasonDZS/chat2dashboard/issues) page
2. Create a new issue with detailed description
3. Include steps to reproduce any bugs

## 🙏 Acknowledgments

- **ECharts** for powerful visualization library
- **FastAPI** for excellent API framework
- **React** for modern frontend development
- **Vite** for lightning-fast development experience

---

**Built with ❤️ for the future of data visualization**