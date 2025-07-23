import { useState, useEffect } from 'react'
import './Settings.css'

const Settings = () => {
  const [backendUrl, setBackendUrl] = useState('')
  const [testingConnection, setTestingConnection] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState(null)
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    // Load saved backend URL from localStorage
    const savedUrl = localStorage.getItem('backendUrl') || 'http://localhost:8000'
    setBackendUrl(savedUrl)
  }, [])

  const handleSave = () => {
    try {
      // Validate URL format
      new URL(backendUrl)
      
      // Save to localStorage
      localStorage.setItem('backendUrl', backendUrl)
      
      // Dispatch custom event to notify other components
      window.dispatchEvent(new CustomEvent('backendUrlChanged', { 
        detail: { url: backendUrl } 
      }))
      
      setSavedMessage('设置已保存！')
      setTimeout(() => setSavedMessage(''), 3000)
    } catch {
      alert('请输入有效的URL地址')
    }
  }

  const handleTestConnection = async () => {
    if (!backendUrl) {
      alert('请先输入后端服务地址')
      return
    }

    setTestingConnection(true)
    setConnectionStatus(null)

    try {
      // Test connection by sending a simple request
      const response = await fetch(`${backendUrl}/health`, {
        method: 'GET',
        timeout: 5000
      })
      
      if (response.ok) {
        setConnectionStatus('success')
      } else {
        setConnectionStatus('error')
      }
    } catch (error) {
      console.error('Connection test failed:', error)
      setConnectionStatus('error')
    } finally {
      setTestingConnection(false)
    }
  }

  const handleReset = () => {
    const defaultUrl = 'http://localhost:8000'
    setBackendUrl(defaultUrl)
    localStorage.setItem('backendUrl', defaultUrl)
    window.dispatchEvent(new CustomEvent('backendUrlChanged', { 
      detail: { url: defaultUrl } 
    }))
    setSavedMessage('已重置为默认设置！')
    setTimeout(() => setSavedMessage(''), 3000)
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <h2>系统设置</h2>
        <p>配置您的应用偏好设置</p>
      </div>
      
      <div className="settings-content">
        <div className="settings-section">
          <div className="section-header">
            <h3>🔗 后端服务配置</h3>
            <p>配置AI可视化服务的后端地址</p>
          </div>
          
          <div className="setting-item">
            <label htmlFor="backend-url">后端服务地址</label>
            <div className="input-group">
              <input
                id="backend-url"
                type="url"
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="url-input"
              />
              <button 
                className="test-btn"
                onClick={handleTestConnection}
                disabled={testingConnection || !backendUrl}
              >
                {testingConnection ? '测试中...' : '测试连接'}
              </button>
            </div>
            
            {connectionStatus && (
              <div className={`connection-status ${connectionStatus}`}>
                {connectionStatus === 'success' ? (
                  <span>✅ 连接成功！后端服务正常运行</span>
                ) : (
                  <span>❌ 连接失败，请检查服务地址和服务状态</span>
                )}
              </div>
            )}
            
            <div className="setting-description">
              <p>💡 默认地址为 <code>http://localhost:8000</code></p>
              <p>请确保后端服务已启动并可访问</p>
            </div>
          </div>
          
          <div className="setting-actions">
            <button className="save-btn" onClick={handleSave}>
              💾 保存设置
            </button>
            <button className="reset-btn" onClick={handleReset}>
              🔄 重置默认
            </button>
          </div>
          
          {savedMessage && (
            <div className="save-message">
              {savedMessage}
            </div>
          )}
        </div>
        
        <div className="settings-section">
          <div className="section-header">
            <h3>ℹ️ 使用说明</h3>
          </div>
          
          <div className="usage-info">
            <ul>
              <li>修改后端地址后，请点击"测试连接"确认服务可用</li>
              <li>设置会自动保存到本地，下次访问时会自动加载</li>
              <li>如果连接失败，请检查：
                <ul>
                  <li>后端服务是否已启动</li>
                  <li>地址和端口是否正确</li>
                  <li>网络连接是否正常</li>
                </ul>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings