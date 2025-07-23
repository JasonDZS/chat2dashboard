import { useState, useRef } from 'react'
import ChartComponent from './ChartComponent.jsx'
import './App.css'

function App() {
  const [containers, setContainers] = useState([])
  const [showDialog, setShowDialog] = useState(false)
  const [dialogPosition, setDialogPosition] = useState({ x: 0, y: 0 })
  const [userInput, setUserInput] = useState('')
  const [dragging, setDragging] = useState(null)
  const [resizing, setResizing] = useState(null)
  const [selectedContainer, setSelectedContainer] = useState(null)
  const canvasRef = useRef(null)

  const handleCanvasClick = (e) => {
    if (resizing) return
    if (e.target !== canvasRef.current) return
    
    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    setSelectedContainer(null)
    setDialogPosition({ x, y })
    setShowDialog(true)
  }

  const handleSubmit = async () => {
    if (!userInput.trim()) return
    
    const newContainer = {
      id: Date.now(),
      x: dialogPosition.x,
      y: dialogPosition.y,
      width: 800,
      height: 400,
      userInput: userInput
    }
    
    setContainers([...containers, newContainer])
    setShowDialog(false)
    setUserInput('')
  }

  const handleCloseDialog = () => {
    setShowDialog(false)
    setUserInput('')
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

  const handleMouseMove = (e) => {
    if (dragging) {
      e.preventDefault()
      const rect = canvasRef.current.getBoundingClientRect()
      const newX = e.clientX - rect.left - dragging.offsetX
      const newY = e.clientY - rect.top - dragging.offsetY
      
      setContainers(containers.map(container => 
        container.id === dragging.id 
          ? { ...container, x: Math.max(0, newX), y: Math.max(0, newY) }
          : container
      ))
    }
    
    if (resizing) {
      e.preventDefault()
      const rect = canvasRef.current.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      
      setContainers(containers.map(container => 
        container.id === resizing.id 
          ? { 
              ...container, 
              width: Math.max(200, mouseX - container.x),
              height: Math.max(150, mouseY - container.y)
            }
          : container
      ))
    }
  }

  const handleMouseUp = () => {
    setDragging(null)
    setResizing(null)
  }

  const handleResizeMouseDown = (e, containerId) => {
    e.stopPropagation()
    setResizing({ id: containerId })
  }

  const handleAutoLayout = () => {
    if (containers.length === 0) return

    const canvasRect = canvasRef.current.getBoundingClientRect()
    const canvasWidth = canvasRect.width
    const canvasHeight = canvasRect.height
    
    const containerWidth = 800
    const containerHeight = 400
    const padding = 20
    
    const cols = Math.floor((canvasWidth - padding) / (containerWidth + padding))
    const actualCols = cols > 0 ? cols : 1
    
    const updatedContainers = containers.map((container, index) => {
      const row = Math.floor(index / actualCols)
      const col = index % actualCols
      
      const x = padding + col * (containerWidth + padding)
      const y = padding + row * (containerHeight + padding)
      
      return {
        ...container,
        x: Math.min(x, canvasWidth - containerWidth - padding),
        y: Math.min(y, canvasHeight - containerHeight - padding),
        width: containerWidth,
        height: containerHeight
      }
    })
    
    setContainers(updatedContainers)
  }



  return (
    <div className="app">
      <div 
        ref={canvasRef}
        className="canvas" 
        onClick={handleCanvasClick}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        <div className="canvas-hint">点击画布任意位置创建AI可视化容器 (需要启动后端服务)</div>
        
        {containers.length > 0 && (
          <button 
            className="auto-layout-btn"
            onClick={handleAutoLayout}
            title="自动排版"
          >
            自动排版
          </button>
        )}
        
        {containers.map(container => (
          <div
            key={container.id}
            className={`container ${selectedContainer === container.id ? 'selected' : ''}`}
            style={{
              left: container.x,
              top: container.y,
              width: container.width,
              height: container.height
            }}
            onMouseDown={(e) => handleMouseDown(e, container.id)}
          >
            <div className="container-content">
              <ChartComponent userInput={container.userInput} />
            </div>
            <div 
              className="resize-handle"
              onMouseDown={(e) => handleResizeMouseDown(e, container.id)}
            />
          </div>
        ))}
        
        {showDialog && (
          <div 
            className="dialog"
            style={{
              left: dialogPosition.x,
              top: dialogPosition.y
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="dialog-content">
              <h3>输入您的可视化需求</h3>
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="例如：创建一个显示最近6个月销售数据的柱状图..."
                rows={3}
              />
              <div className="dialog-buttons">
                <button onClick={handleSubmit}>提交</button>
                <button onClick={handleCloseDialog}>取消</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
