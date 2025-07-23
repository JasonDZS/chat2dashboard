import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { useBackend } from './context/BackendContext'

const ChartComponent = ({ userInput }) => {
  const chartRef = useRef(null)
  const [chartOption, setChartOption] = useState(null)
  const [chartTitle, setChartTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { backendUrl } = useBackend()

  useEffect(() => {
    const generateChart = async () => {
      if (!userInput.trim()) return
      
      setLoading(true)
      setError(null)
      
      try {
        // Call backend API to generate visualization
        const formData = new FormData()
        formData.append('query', userInput)
        
        const response = await fetch(`${backendUrl}/generate`, {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const htmlContent = await response.text()
        
        // Extract ECharts option from generated HTML
        const optionMatch = htmlContent.match(/var option = ({[\s\S]*?});/)
        if (optionMatch) {
          const optionString = optionMatch[1]
          
          try {
            // Safely parse the option object
            const option = JSON.parse(optionString)
            
            // Adjust styling for container size
            if (option.legend && !option.legend.textStyle) {
              option.legend.textStyle = { fontSize: 10 }
            }
            if (option.xAxis) {
              if (Array.isArray(option.xAxis)) {
                option.xAxis.forEach(axis => {
                  if (!axis.axisLabel) axis.axisLabel = { fontSize: 10 }
                  else axis.axisLabel.fontSize = 10
                })
              } else {
                if (!option.xAxis.axisLabel) option.xAxis.axisLabel = { fontSize: 10 }
                else option.xAxis.axisLabel.fontSize = 10
              }
            }
            if (option.yAxis) {
              if (Array.isArray(option.yAxis)) {
                option.yAxis.forEach(axis => {
                  if (!axis.axisLabel) axis.axisLabel = { fontSize: 10 }
                  else axis.axisLabel.fontSize = 10
                })
              } else {
                if (!option.yAxis.axisLabel) option.yAxis.axisLabel = { fontSize: 10 }
                else option.yAxis.axisLabel.fontSize = 10
              }
            }
            if (option.grid) {
              option.grid = {
                ...option.grid,
                top: '15%',
                bottom: '8%'
              }
            }
            
            // Remove title from option since we show it separately
            if (option.title) {
              setChartTitle(option.title.text || '图表')
              delete option.title
            } else {
              setChartTitle('AI生成图表')
            }
            
            setChartOption(option)
          } catch (parseError) {
            console.error('Failed to parse chart option:', parseError)
            throw parseError
          }
        } else {
          throw new Error('Failed to extract chart configuration from response')
        }
      } catch (error) {
        console.error('Failed to generate chart:', error)
        setError(error.message)
        setChartTitle('错误')
        setChartOption({
          title: { text: '生成失败', left: 'center', textStyle: { color: '#ff4757' } },
          series: [{ type: 'pie', data: [] }]
        })
      } finally {
        setLoading(false)
      }
    }

    generateChart()
  }, [userInput, backendUrl])

  useEffect(() => {
    if (!chartRef.current || !chartOption) return

    const myChart = echarts.init(chartRef.current)
    myChart.setOption(chartOption)

    const resizeObserver = new ResizeObserver(() => {
      myChart.resize()
    })
    resizeObserver.observe(chartRef.current)

    return () => {
      resizeObserver.disconnect()
      myChart.dispose()
    }
  }, [chartOption])

  return (
    <div style={{ padding: '10px', background: 'white', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 10px 0', color: '#333', fontSize: '14px', textAlign: 'center' }}>
        {chartTitle} - {userInput}
      </h3>
      
      {loading && (
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#666',
          fontSize: '14px'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              width: '20px', 
              height: '20px', 
              border: '2px solid #f3f3f3',
              borderTop: '2px solid #007bff',
              borderRadius: '50%',
              margin: '0 auto 10px',
              animation: 'spin 1s linear infinite'
            }} />
            正在生成可视化...
          </div>
        </div>
      )}
      
      {error && (
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#ff4757',
          fontSize: '12px',
          textAlign: 'center',
          padding: '20px'
        }}>
          <div>
            <div style={{ marginBottom: '10px' }}>❌</div>
            <div>生成失败: {error}</div>
            <div style={{ marginTop: '5px', color: '#999' }}>请检查后端服务是否运行</div>
          </div>
        </div>
      )}
      
      {!loading && !error && (
        <div ref={chartRef} style={{ flex: 1, minHeight: 0 }} />
      )}
    </div>
  )
}

export default ChartComponent