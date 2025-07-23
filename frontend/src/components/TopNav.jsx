import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import './TopNav.css'

const TopNav = () => {
  const location = useLocation()
  const [backendStatus, setBackendStatus] = useState('loading')
  const [backendUrl, setBackendUrl] = useState('')

  useEffect(() => {
    const savedUrl = localStorage.getItem('backendUrl') || 'http://localhost:8000'
    setBackendUrl(savedUrl)

    const handleBackendUrlChange = (event) => {
      setBackendUrl(event.detail.url)
    }

    window.addEventListener('backendUrlChanged', handleBackendUrlChange)
    return () => window.removeEventListener('backendUrlChanged', handleBackendUrlChange)
  }, [])

  useEffect(() => {
    if (!backendUrl) return

    const checkBackendStatus = async () => {
      try {
        const response = await fetch(`${backendUrl}/health`)
        if (response.ok) {
          setBackendStatus('healthy')
        } else {
          setBackendStatus('error')
        }
      } catch (error) {
        setBackendStatus('error')
      }
    }

    checkBackendStatus()
    const interval = setInterval(checkBackendStatus, 30000)
    return () => clearInterval(interval)
  }, [backendUrl])

  return (
    <nav className="top-nav">
      <div className="nav-brand">
        <h1>
          <span style={{color: '#E2E8F0'}}>Chat</span>
          <span style={{color: '#00FFAB'}}>2</span>
          <span style={{color: '#E2E8F0'}}>DashBoard</span>
        </h1>
        <div className="backend-status">
          <span 
            className={`status-indicator ${backendStatus}`}
            title={backendStatus === 'healthy' ? '后端服务正常' : backendStatus === 'error' ? '后端服务异常' : '检查中...'}
          ></span>
          <span className="status-text">
            {backendStatus === 'healthy' ? '服务正常' : backendStatus === 'error' ? '服务异常' : '检查中...'}
          </span>
        </div>
      </div>
      <div className="nav-links">
        <Link 
          to="/dashboard" 
          className={location.pathname === '/dashboard' ? 'active' : ''}
        >
          仪表板
        </Link>
        {/*<Link */}
        {/*  to="/analytics" */}
        {/*  className={location.pathname === '/analytics' ? 'active' : ''}*/}
        {/*>*/}
        {/*  分析*/}
        {/*</Link>*/}
        <Link 
          to="/settings" 
          className={location.pathname === '/settings' ? 'active' : ''}
        >
          设置
        </Link>
      </div>
    </nav>
  )
}

export default TopNav