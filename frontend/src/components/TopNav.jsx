import { Link, useLocation } from 'react-router-dom'
import './TopNav.css'

const TopNav = () => {
  const location = useLocation()

  return (
    <nav className="top-nav">
      <div className="nav-brand">
        <h1>Chat2Dashboard</h1>
      </div>
      <div className="nav-links">
        <Link 
          to="/dashboard" 
          className={location.pathname === '/dashboard' ? 'active' : ''}
        >
          仪表板
        </Link>
        <Link 
          to="/analytics" 
          className={location.pathname === '/analytics' ? 'active' : ''}
        >
          分析
        </Link>
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