import React, { useState, useEffect, useRef } from 'react'
import { useBackend } from '../context/BackendContext'
import * as echarts from 'echarts/core'
import {
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import { GraphChart } from 'echarts/charts'
import { LabelLayout } from 'echarts/features'
import { CanvasRenderer } from 'echarts/renderers'
import './KnowledgeGraph.css'

echarts.use([
  TooltipComponent,
  LegendComponent,
  GraphChart,
  CanvasRenderer,
  LabelLayout
])

const KnowledgeGraph = () => {
  const { backendUrl } = useBackend()
  const [knowledgeBases, setKnowledgeBases] = useState([])
  const [selectedKbId, setSelectedKbId] = useState('')
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)
  const [activeTab, setActiveTab] = useState('nodes') // 'nodes' or 'edges'

  useEffect(() => {
    if (backendUrl) {
      fetchKnowledgeBases()
    }
  }, [backendUrl])

  useEffect(() => {
    const initChart = () => {
      if (chartRef.current && !chartInstance.current) {
        console.log('Initializing ECharts instance')
        chartInstance.current = echarts.init(chartRef.current)
        
        // Resize chart when window resizes
        const handleResize = () => {
          if (chartInstance.current) {
            chartInstance.current.resize()
          }
        }
        window.addEventListener('resize', handleResize)
        
        return () => {
          window.removeEventListener('resize', handleResize)
        }
      }
    }

    const cleanup = initChart()

    return () => {
      cleanup && cleanup()
      if (chartInstance.current) {
        chartInstance.current.dispose()
        chartInstance.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (graphData) {
      // Initialize chart if not already initialized
      if (chartRef.current && !chartInstance.current) {
        console.log('Late initializing ECharts instance')
        chartInstance.current = echarts.init(chartRef.current)
      }
      
      if (chartInstance.current) {
        // Small delay to ensure DOM is ready
        setTimeout(() => {
          renderGraph()
        }, 100)
      }
    }
  }, [graphData])

  const fetchKnowledgeBases = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/`)
      if (!response.ok) throw new Error('Failed to fetch knowledge bases')
      
      const data = await response.json()
      setKnowledgeBases(data.knowledge_bases || [])
      
      if (data.knowledge_bases && data.knowledge_bases.length > 0) {
        const readyKb = data.knowledge_bases.find(kb => kb.status === 'ready')
        if (readyKb) {
          setSelectedKbId(readyKb.id)
        }
      }
    } catch (err) {
      setError('Failed to load knowledge bases: ' + err.message)
    }
  }

  const fetchGraphData = async (kbId) => {
    if (!kbId) return
    
    setLoading(true)
    setError('')
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/${kbId}/graph`)
      if (!response.ok) {
        if (response.status === 400) {
          throw new Error('Knowledge base not ready. Please build it first.')
        }
        throw new Error('Failed to fetch graph data')
      }
      
      const data = await response.json()
      console.log('Received graph data:', data.graph_data)
      
      // Validate and fix data format if needed
      const graphData = data.graph_data
      if (graphData && graphData.nodes && graphData.links && graphData.categories) {
        // Ensure all nodes have required properties
        graphData.nodes = graphData.nodes.map(node => ({
          id: node.id,
          name: node.name || node.id,
          category: node.category || 0,
          symbolSize: node.symbolSize || 15,
          value: node.value || 10,
          ...node
        }))
        
        // Ensure all links have required properties
        graphData.links = graphData.links.map(link => ({
          source: link.source,
          target: link.target,
          ...link
        }))
        
        console.log('Processed graph data:', {
          nodes: graphData.nodes.length,
          links: graphData.links.length,
          categories: graphData.categories.length,
          sampleNode: graphData.nodes[0],
          sampleLink: graphData.links[0]
        })
        
        setGraphData(graphData)
      } else {
        throw new Error('Invalid graph data format')
      }
    } catch (err) {
      setError(err.message)
      setGraphData(null)
    } finally {
      setLoading(false)
    }
  }

  const handleKbSelect = (kbId) => {
    setSelectedKbId(kbId)
    setError('')
    
    // Clear existing chart data and display
    if (chartInstance.current) {
      chartInstance.current.clear()
      console.log('Cleared existing chart data')
    }
    setGraphData(null)
    
    if (kbId) {
      fetchGraphData(kbId)
    }
  }

  const renderGraph = () => {
    if (!chartInstance.current || !graphData) {
      console.log('renderGraph: Missing chart instance or graph data', {
        hasChartInstance: !!chartInstance.current,
        hasGraphData: !!graphData,
        graphData
      })
      return
    }

    console.log('renderGraph: Rendering graph with data', {
      nodes: graphData.nodes?.length,
      links: graphData.links?.length,
      categories: graphData.categories?.length
    })

    const option = {
      title: {
        text: '知识图谱',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: function (params) {
          if (params.dataType === 'node') {
            return `<strong>${params.data.name}</strong><br/>
                    类别: ${graphData.categories[params.data.category]?.name || 'Unknown'}<br/>
                    节点大小: ${params.data.symbolSize || 'N/A'}`
          } else if (params.dataType === 'edge') {
            return `${params.data.source} → ${params.data.target}`
          }
          return params.name
        }
      },
      legend: {
        data: graphData.categories.map(cat => cat.name),
        top: 'bottom',
        left: 'center'
      },
      series: [{
        name: '知识图谱',
        type: 'graph',
        layout: 'force',
        data: graphData.nodes,
        links: graphData.links,
        categories: graphData.categories,
        roam: true,
        focusNodeAdjacency: true,
        force: {
          repulsion: 100,
          gravity: 0.02,
          edgeLength: 50,
          layoutAnimation: true
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{b}'
        },
        labelLayout: {
          hideOverlap: true
        },
        scaleLimit: {
          min: 0.4,
          max: 2
        },
        lineStyle: {
          color: 'source',
          curveness: 0.3,
          opacity: 0.7
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 10
          }
        }
      }]
    }

    try {
      // Clear existing chart before setting new option
      chartInstance.current.clear()
      
      // Set new option with notMerge=true to completely replace
      chartInstance.current.setOption(option, true)
      console.log('ECharts setOption completed successfully')
      
      // Add click event listeners
      chartInstance.current.off('click')
      chartInstance.current.on('click', function (params) {
        if (params.dataType === 'node') {
          setSelectedNode(params.data)
          setSelectedEdge(null)
          setActiveTab('nodes')
          console.log('Selected node:', params.data)
        } else if (params.dataType === 'edge') {
          setSelectedEdge(params.data)
          setSelectedNode(null)
          setActiveTab('edges')
          console.log('Selected edge:', params.data)
        }
      })
      
      // Force chart resize to ensure proper display
      setTimeout(() => {
        if (chartInstance.current) {
          chartInstance.current.resize()
        }
      }, 200)
      
    } catch (error) {
      console.error('Error setting ECharts option:', error)
      setError('Failed to render knowledge graph: ' + error.message)
    }
  }

  const getKbStatusColor = (status) => {
    switch (status) {
      case 'ready': return '#52c41a'
      case 'building': return '#1890ff'
      case 'error': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  return (
    <div className="knowledge-graph">
      <div className="page-header">
        <h1>知识图谱</h1>
        <p>选择知识库查看其知识图谱结构</p>
      </div>

      <div className="kb-selector">
        <label htmlFor="kb-select">选择知识库:</label>
        <div className="select-with-status">
          <select 
            id="kb-select"
            value={selectedKbId} 
            onChange={(e) => handleKbSelect(e.target.value)}
            disabled={loading}
          >
            <option value="">请选择知识库</option>
            {knowledgeBases.map(kb => (
              <option key={kb.id} value={kb.id}>
                {kb.name}
                {kb.metrics && ` - ${kb.metrics.entities_count} 实体`}
              </option>
            ))}
          </select>
          {selectedKbId && (
            <div className="kb-status">
              <span 
                className="status-indicator"
                style={{ backgroundColor: getKbStatusColor(knowledgeBases.find(kb => kb.id === selectedKbId)?.status) }}
              ></span>
              <span className="status-text">
                {knowledgeBases.find(kb => kb.id === selectedKbId)?.status}
              </span>
            </div>
          )}
        </div>
        
        {selectedKbId && (
          <button 
            onClick={() => fetchGraphData(selectedKbId)}
            disabled={loading}
            className="refresh-btn"
          >
            {loading ? '加载中...' : '刷新'}
          </button>
        )}
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>正在加载知识图谱...</p>
        </div>
      )}

      {graphData && !loading && (
        <div className="graph-layout">
          {/* 左侧图谱区域 */}
          <div className="graph-section">
            <div className="graph-stats">
              <div className="stat-item">
                <span className="stat-value">{graphData.nodes?.length || 0}</span>
                <span className="stat-label">节点</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{graphData.links?.length || 0}</span>
                <span className="stat-label">关系</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{graphData.categories?.length || 0}</span>
                <span className="stat-label">类别</span>
              </div>
            </div>
            <div ref={chartRef} className="graph-chart"></div>
          </div>
          
          {/* 右侧数据面板 */}
          <div className="data-panel">
            <div className="panel-header">
              <div className="panel-tabs">
                <button 
                  className={`tab-btn ${activeTab === 'nodes' ? 'active' : ''}`}
                  onClick={() => setActiveTab('nodes')}
                >
                  节点数据 ({graphData.nodes?.length || 0})
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'edges' ? 'active' : ''}`}
                  onClick={() => setActiveTab('edges')}
                >
                  边数据 ({graphData.links?.length || 0})
                </button>
              </div>
            </div>
            
            <div className="panel-content">
              {activeTab === 'nodes' && (
                <div className="nodes-table">
                  <div className="table-header">
                    <div className="header-cell">节点ID</div>
                    <div className="header-cell">名称</div>
                    <div className="header-cell">类别</div>
                    <div className="header-cell">大小</div>
                  </div>
                  <div className="table-body">
                    {graphData.nodes?.map((node, index) => (
                      <div 
                        key={node.id || index}
                        className={`table-row ${selectedNode?.id === node.id ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedNode(node)
                          setSelectedEdge(null)
                        }}
                      >
                        <div className="table-cell" title={node.id}>{node.id}</div>
                        <div className="table-cell" title={node.name}>{node.name}</div>
                        <div className="table-cell">
                          {graphData.categories[node.category]?.name || 'Unknown'}
                        </div>
                        <div className="table-cell">{node.symbolSize || 'N/A'}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {activeTab === 'edges' && (
                <div className="edges-table">
                  <div className="table-header">
                    <div className="header-cell">源节点</div>
                    <div className="header-cell">目标节点</div>
                    <div className="header-cell">关系类型</div>
                  </div>
                  <div className="table-body">
                    {graphData.links?.map((link, index) => (
                      <div 
                        key={`${link.source}-${link.target}-${index}`}
                        className={`table-row ${selectedEdge?.source === link.source && selectedEdge?.target === link.target ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedEdge(link)
                          setSelectedNode(null)
                        }}
                      >
                        <div className="table-cell" title={link.source}>{link.source}</div>
                        <div className="table-cell" title={link.target}>{link.target}</div>
                        <div className="table-cell">{link.relationshipType || '关系'}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!graphData && !loading && selectedKbId && !error && (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>暂无图谱数据</h3>
          <p>请确保知识库已构建完成</p>
        </div>
      )}

      {!selectedKbId && !loading && (
        <div className="empty-state">
          <div className="empty-icon">🧠</div>
          <h3>选择知识库</h3>
          <p>请从上方下拉菜单中选择一个知识库来查看其知识图谱</p>
        </div>
      )}
    </div>
  )
}

export default KnowledgeGraph