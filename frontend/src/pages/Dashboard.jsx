import { useState, useRef, useCallback, useEffect } from 'react'
import ChartComponent from '../ChartComponent.jsx'
import { useBackend } from '../context/BackendContext'
import './Dashboard.css'

const Dashboard = () => {
  const [containers, setContainers] = useState([])
  const [showDialog, setShowDialog] = useState(false)
  const [dialogPosition, setDialogPosition] = useState({ x: 0, y: 0 })
  const [userInput, setUserInput] = useState('')
  const [selectedDatabase, setSelectedDatabase] = useState('')
  const [selectedChartType, setSelectedChartType] = useState('')
  const [availableDatabases, setAvailableDatabases] = useState([])
  const [dragging, setDragging] = useState(null)
  const [resizing, setResizing] = useState(null)
  const [selectedContainer, setSelectedContainer] = useState(null)
  const [canvasPanning, setCanvasPanning] = useState(false)
  const [canvasTransform, setCanvasTransform] = useState({ x: 0, y: 0, scale: 1 })
  const canvasRef = useRef(null)
  const canvasContainerRef = useRef(null)
  const { backendUrl } = useBackend()

  // Fetch available databases
  const fetchDatabases = async () => {
    try {
      const response = await fetch(`${backendUrl}/databases`)
      if (response.ok) {
        const data = await response.json()
        setAvailableDatabases(data.databases || [])
        // Set first database as default if available
        if (data.databases && data.databases.length > 0 && !selectedDatabase) {
          setSelectedDatabase(data.databases[0].name)
        }
      }
    } catch (error) {
      console.error('Failed to fetch databases:', error)
    }
  }

  // Load cached dashboard data on mount
  useEffect(() => {
    const loadDashboardData = () => {
      try {
        const cachedContainers = localStorage.getItem('dashboardContainers')
        const cachedTransform = localStorage.getItem('dashboardTransform')
        
        if (cachedContainers) {
          const parsedContainers = JSON.parse(cachedContainers)
          setContainers(parsedContainers)
        }
        
        if (cachedTransform) {
          const parsedTransform = JSON.parse(cachedTransform)
          setCanvasTransform(parsedTransform)
        }
      } catch (error) {
        console.error('Failed to load cached dashboard data:', error)
      }
    }
    
    loadDashboardData()
    fetchDatabases()
  }, [backendUrl, selectedDatabase])

  // Auto-save dashboard data whenever containers or transform changes
  useEffect(() => {
    const saveDashboardData = () => {
      try {
        localStorage.setItem('dashboardContainers', JSON.stringify(containers))
        localStorage.setItem('dashboardTransform', JSON.stringify(canvasTransform))
      } catch (error) {
        console.error('Failed to save dashboard data:', error)
      }
    }
    
    // Only save if we have data (avoid saving empty state on initial load)
    if (containers.length > 0 || canvasTransform.x !== 0 || canvasTransform.y !== 0 || canvasTransform.scale !== 1) {
      saveDashboardData()
    }
  }, [containers, canvasTransform])

  const handleCanvasClick = (e) => {
    if (resizing || canvasPanning) return
    if (e.target !== canvasRef.current) return
    
    const rect = canvasRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left - canvasTransform.x) / canvasTransform.scale
    const y = (e.clientY - rect.top - canvasTransform.y) / canvasTransform.scale
    
    setSelectedContainer(null)
    setDialogPosition({ x, y })
    setShowDialog(true)
  }

  const handleCanvasMouseDown = (e) => {
    if (e.target === canvasRef.current) {
      setCanvasPanning(true)
      e.preventDefault()
    }
  }

  const handleSubmit = async () => {
    if (!userInput.trim() || !selectedDatabase) return
    
    const newContainer = {
      id: Date.now(),
      x: dialogPosition.x,
      y: dialogPosition.y,
      width: 800,
      height: 400,
      userInput: userInput,
      dbName: selectedDatabase,
      chartType: selectedChartType
    }
    
    setContainers([...containers, newContainer])
    setShowDialog(false)
    setUserInput('')
    setSelectedChartType('')
  }

  const handleCloseDialog = () => {
    setShowDialog(false)
    setUserInput('')
    setSelectedChartType('')
  }

  const handleMouseDown = (e, containerId) => {
    e.stopPropagation()
    const container = containers.find(c => c.id === containerId)
    const rect = e.currentTarget.getBoundingClientRect()
    const offsetX = e.clientX - rect.left
    const offsetY = e.clientY - rect.top
    
    setSelectedContainer(containerId)
    setDragging({ 
      id: containerId, 
      offsetX, 
      offsetY,
      startX: container.x,
      startY: container.y
    })
  }

  const handleMouseMove = useCallback((e) => {
    if (dragging) {
      e.preventDefault()
      const rect = canvasRef.current.getBoundingClientRect()
      const newX = (e.clientX - rect.left - canvasTransform.x) / canvasTransform.scale - dragging.offsetX
      const newY = (e.clientY - rect.top - canvasTransform.y) / canvasTransform.scale - dragging.offsetY
      
      setContainers(containers.map(container => 
        container.id === dragging.id 
          ? { ...container, x: newX, y: newY }
          : container
      ))
    }
    
    if (resizing) {
      e.preventDefault()
      const rect = canvasRef.current.getBoundingClientRect()
      const mouseX = (e.clientX - rect.left - canvasTransform.x) / canvasTransform.scale
      const mouseY = (e.clientY - rect.top - canvasTransform.y) / canvasTransform.scale
      
      const container = containers.find(c => c.id === resizing.id)
      if (container) {
        setContainers(containers.map(c => 
          c.id === resizing.id 
            ? { 
                ...c, 
                width: Math.max(200, mouseX - container.x),
                height: Math.max(150, mouseY - container.y)
              }
            : c
        ))
      }
    }
    
    if (canvasPanning) {
      e.preventDefault()
      const deltaX = e.movementX
      const deltaY = e.movementY
      
      setCanvasTransform(prev => ({
        ...prev,
        x: prev.x + deltaX,
        y: prev.y + deltaY
      }))
    }
  }, [dragging, resizing, canvasPanning, containers, canvasTransform])

  const handleMouseUp = useCallback(() => {
    setDragging(null)
    setResizing(null)
    setCanvasPanning(false)
  }, [])

  const handleResizeMouseDown = (e, containerId) => {
    e.stopPropagation()
    setResizing({ id: containerId })
  }

  const handleZoomIn = () => {
    setCanvasTransform(prev => ({ ...prev, scale: Math.min(prev.scale * 1.2, 3) }))
  }

  const handleZoomOut = () => {
    setCanvasTransform(prev => ({ ...prev, scale: Math.max(prev.scale / 1.2, 0.1) }))
  }

  const handleResetView = () => {
    setCanvasTransform({ x: 0, y: 0, scale: 1 })
  }

  const handleWheel = useCallback((e) => {
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    const rect = canvasRef.current.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    
    setCanvasTransform(prev => {
      const newScale = Math.min(Math.max(prev.scale * delta, 0.1), 3)
      const scaleDiff = newScale - prev.scale
      
      return {
        x: prev.x - (mouseX - prev.x) * scaleDiff / prev.scale,
        y: prev.y - (mouseY - prev.y) * scaleDiff / prev.scale,
        scale: newScale
      }
    })
  }, [])

  const handleAutoLayout = () => {
    if (containers.length === 0) return

    const containerWidth = 800
    const containerHeight = 400
    const padding = 50
    const cols = Math.ceil(Math.sqrt(containers.length))
    
    const updatedContainers = containers.map((container, index) => {
      const row = Math.floor(index / cols)
      const col = index % cols
      
      const x = col * (containerWidth + padding)
      const y = row * (containerHeight + padding)
      
      return {
        ...container,
        x,
        y,
        width: containerWidth,
        height: containerHeight
      }
    })
    
    setContainers(updatedContainers)
  }

  const handleClearCache = () => {
    if (confirm('确定要清除所有缓存的图表吗？此操作不可撤销。')) {
      localStorage.removeItem('dashboardContainers')
      localStorage.removeItem('dashboardTransform')
      setContainers([])
      setCanvasTransform({ x: 0, y: 0, scale: 1 })
    }
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-toolbar">
        <div className="toolbar-group">
          <button className="toolbar-btn" onClick={handleZoomIn} title="放大">
            🔍+
          </button>
          <button className="toolbar-btn" onClick={handleZoomOut} title="缩小">
            🔍-
          </button>
          <button className="toolbar-btn" onClick={handleResetView} title="重置视图">
            🎯
          </button>
          <span className="zoom-indicator">{Math.round(canvasTransform.scale * 100)}%</span>
        </div>
        <div className="toolbar-group">
          {containers.length > 0 && (
            <>
              <button className="toolbar-btn" onClick={handleAutoLayout} title="自动排版">
                📐 自动排版
              </button>
              <button className="toolbar-btn clear-btn" onClick={handleClearCache} title="清除缓存">
                🗑️ 清除缓存
              </button>
            </>
          )}
        </div>
      </div>
      
      <div 
        ref={canvasContainerRef}
        className="dashboard-canvas-container"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
      >
        <div 
          ref={canvasRef}
          className="dashboard-canvas"
          style={{
            transform: `translate(${canvasTransform.x}px, ${canvasTransform.y}px) scale(${canvasTransform.scale})`,
            transformOrigin: '0 0',
            cursor: canvasPanning ? 'grabbing' : 'grab'
          }}
          onClick={handleCanvasClick}
          onMouseDown={handleCanvasMouseDown}
        >
          <div className="canvas-grid"></div>
          
          <div className="canvas-hint">
            {containers.length === 0 ? (
              <div>
                <div style={{ fontSize: '20px', marginBottom: '10px' }}>📊</div>
                <div>点击画布任意位置创建AI可视化容器</div>
                <div style={{ fontSize: '12px', marginTop: '5px', opacity: 0.7 }}>(需要启动后端服务)</div>
              </div>
            ) : (
              <div style={{ fontSize: '14px', opacity: 0.5 }}>
                已缓存 {containers.length} 个图表
              </div>
            )}
          </div>
          
          {containers.map(container => (
            <div
              key={container.id}
              className={`chart-container ${selectedContainer === container.id ? 'selected' : ''}`}
              style={{
                left: container.x,
                top: container.y,
                width: container.width,
                height: container.height
              }}
            >
              <div 
                className="container-header"
                onMouseDown={(e) => handleMouseDown(e, container.id)}
                title="拖拽移动容器"
              >
                <div className="container-title">
                  📊 图表
                </div>
                <div className="drag-indicator">
                  ⋮⋮
                </div>
              </div>
              <div className="container-content">
                <ChartComponent 
                  userInput={container.userInput} 
                  dbName={container.dbName || selectedDatabase}
                  chartType={container.chartType}
                />
              </div>
              <div 
                className="resize-handle"
                onMouseDown={(e) => handleResizeMouseDown(e, container.id)}
              />
            </div>
          ))}
          
          {showDialog && (
            <div 
              className="input-dialog apple-style"
              style={{
                left: dialogPosition.x,
                top: dialogPosition.y,
                transform: `scale(${1 / canvasTransform.scale})`
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="dialog-header">
                <button className="dialog-close-btn" onClick={handleCloseDialog}>
                  ✕
                </button>
                <div className="dialog-title">AI 可视化助手</div>
                <div className="dialog-header-spacer"></div>
              </div>
              <div className="dialog-content">
                <div className="chat-messages">
                  <div className="assistant-message">
                    <div className="message-avatar">🤖</div>
                    <div className="message-content">
                      <div className="message-bubble assistant">
                        你好！我是你的AI可视化助手。请告诉我你想要创建什么样的图表？
                      </div>
                    </div>
                  </div>
                </div>
                <div className="database-selection" style={{ 
                  padding: '10px 20px', 
                  borderTop: '1px solid #e0e0e0',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <label style={{ fontSize: '12px', color: '#666', minWidth: '60px' }}>数据库:</label>
                    <select
                      value={selectedDatabase}
                      onChange={(e) => setSelectedDatabase(e.target.value)}
                      style={{
                        flex: 1,
                        padding: '4px 8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                    >
                      <option value="">选择数据库</option>
                      {availableDatabases.map(db => (
                        <option key={db.name} value={db.name}>
                          {db.name} ({db.table_count || 0} 表)
                        </option>
                      ))}
                    </select>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <label style={{ fontSize: '12px', color: '#666', minWidth: '60px' }}>图表类型:</label>
                    <select
                      value={selectedChartType}
                      onChange={(e) => setSelectedChartType(e.target.value)}
                      style={{
                        flex: 1,
                        padding: '4px 8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                    >
                      <option value="">自动推断</option>
                      <option value="bar">柱状图</option>
                      <option value="line">折线图</option>
                      <option value="pie">饼图</option>
                      <option value="scatter">散点图</option>
                      <option value="area">面积图</option>
                    </select>
                  </div>
                </div>
                <div className="chat-input-container">
                  <div className="chat-input-wrapper">
                    <textarea
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      placeholder="描述你想要的图表，例如：创建一个显示最近6个月销售数据的柱状图..."
                      rows={3}
                      className="chat-input"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                          handleSubmit()
                        }
                      }}
                    />
                    <button 
                      className="send-button" 
                      onClick={handleSubmit}
                      disabled={!userInput.trim() || !selectedDatabase}
                      title={!selectedDatabase ? "请先选择数据库" : "发送"}
                    >
                      ➤
                    </button>
                  </div>
                  <div className="input-hint">按 ⌘+Enter 发送</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard