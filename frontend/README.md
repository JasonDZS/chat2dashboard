# Chat to Dashboard 🎨

A React application that creates interactive AI-powered dashboards. Users can click on the canvas to create chart containers that generate visualizations from natural language descriptions using the backend AI service.

## Features

- 🖱️ Click-to-create interactive dashboard containers
- 🤖 AI-powered visualization generation from natural language
- 📊 Multiple chart types (bar, line, pie, scatter, area)
- 🔄 Real-time chart generation and updates
- 📏 Draggable and resizable containers
- 📐 Auto-layout functionality
- ⚡ Built with React + Vite for fast development

## Prerequisites

Make sure the backend AI service is running before using the frontend:

1. **Start the backend service:**
   ```bash
   cd ../data-vis-agent
   python start.py
   ```
   Backend will be available at `http://localhost:8000`

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   - Navigate to the URL shown in terminal (usually `http://localhost:5173`)
   - Click anywhere on the canvas to create a new container
   - Enter your visualization request in natural language
   - Watch as the AI generates your chart!

## Usage Examples

Click on the canvas and try these natural language requests:

- "Create a bar chart showing sales data for 6 months"
- "Generate a pie chart displaying market share by company"
- "Show a line chart of temperature trends over time"
- "Make a scatter plot of price vs quality ratings"
- "Create an area chart showing revenue growth"

## Project Structure

```
src/
├── App.jsx           # Main application with canvas logic
├── ChartComponent.jsx # AI-powered chart generation
├── App.css          # Styling and animations
├── main.jsx         # React entry point
└── assets/          # Static assets
```

## How It Works

1. **User Interaction**: Click on canvas to create container
2. **Input**: Enter natural language description of desired visualization
3. **API Call**: Frontend sends request to FastAPI backend (`http://localhost:8000/generate`)
4. **AI Processing**: Backend processes natural language and generates ECharts configuration
5. **Rendering**: Frontend displays the AI-generated interactive chart

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

## Technologies Used

- **Frontend**: React 19, Vite, ECharts
- **Styling**: Modern CSS with animations
- **Backend Integration**: Fetch API calls to FastAPI service
- **Charts**: ECharts for interactive visualizations

## Features

### Interactive Canvas
- Click anywhere to create new containers
- Drag containers to reposition
- Resize containers using handles
- Auto-layout button for organized arrangement

### AI-Powered Charts
- Natural language processing
- Multiple chart type support
- Loading states with animations
- Error handling and user feedback
- Real-time generation

### Responsive Design
- Modern glassmorphism UI
- Smooth animations and transitions
- Mobile-friendly interactions