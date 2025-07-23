import './Settings.css'

const Settings = () => {
  return (
    <div className="settings-page">
      <div className="page-header">
        <h2>系统设置</h2>
        <p>配置您的应用偏好设置</p>
      </div>
      
      <div className="settings-content">
        <div className="coming-soon">
          <div className="icon">⚙️</div>
          <h3>功能开发中</h3>
          <p>设置功能正在开发中，敬请期待！</p>
        </div>
      </div>
    </div>
  )
}

export default Settings