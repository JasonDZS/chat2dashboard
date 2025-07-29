import { Link, useLocation } from 'react-router-dom'
import './SideNav.css'

const SideNav = () => {
  const location = useLocation()

  const menuItems = [
    { path: '/dashboard', label: '仪表板', icon: '📊' },
    // { path: '/analytics', label: '数据分析', icon: '📈' },
    // { path: '/reports', label: '报表', icon: '📋' },
    { path: '/data', label: '数据管理', icon: '💾' },
    { path: '/training', label: '训练数据', icon: '🎓' },
    { path: '/knowledge-base', label: '知识库管理', icon: '🧠' },
    { path: '/chat', label: '知识库对话', icon: '💬' },
    { path: '/settings', label: '设置', icon: '⚙️' }
  ]

  return (
    <nav className="side-nav">
      <div className="nav-menu">
        {menuItems.map(item => (
          <Link 
            key={item.path}
            to={item.path} 
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  )
}

export default SideNav