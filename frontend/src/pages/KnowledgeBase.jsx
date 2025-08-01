import { useState, useEffect } from 'react'
import { useBackend } from '../context/BackendContext'
import './KnowledgeBase.css'

function KnowledgeBase() {
  const { backendUrl } = useBackend()
  
  // 知识库列表相关状态
  const [knowledgeBases, setKnowledgeBases] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedKb, setSelectedKb] = useState(null)
  
  // 创建知识库相关状态
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createFormData, setCreateFormData] = useState({
    kb_id: '',
    name: '',
    description: '',
    datasource_id: 'default'
  })
  const [creating, setCreating] = useState(false)
  
  
  // 构建状态
  const [buildingKbs, setBuildingKbs] = useState(new Set())

  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/`)
      const data = await response.json()
      
      if (response.ok) {
        setKnowledgeBases(data.knowledge_bases || [])
      } else {
        console.error('Failed to load knowledge bases:', data)
      }
    } catch (error) {
      console.error('Error loading knowledge bases:', error)
    } finally {
      setLoading(false)
    }
  }

  // 创建知识库
  const handleCreateKb = async (e) => {
    e.preventDefault()
    if (!createFormData.name.trim()) return

    setCreating(true)
    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(createFormData)
      })

      const result = await response.json()
      
      if (response.ok) {
        setCreateFormData({ kb_id: '', name: '', description: '', datasource_id: 'default' })
        setShowCreateForm(false)
        loadKnowledgeBases()
      } else {
        alert(`创建失败: ${result.detail || result.error}`)
      }
    } catch (error) {
      alert(`创建失败: ${error.message}`)
    } finally {
      setCreating(false)
    }
  }

  // 构建知识库
  const handleBuildKb = async (kbId) => {
    setBuildingKbs(prev => new Set([...prev, kbId]))
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/${kbId}/build`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()
      
      if (response.ok) {
        alert(`知识库构建已启动，任务ID: ${result.task_id}`)
        // 可以添加轮询构建状态的逻辑
      } else {
        alert(`构建失败: ${result.detail || result.error}`)
      }
    } catch (error) {
      alert(`构建失败: ${error.message}`)
    } finally {
      setBuildingKbs(prev => {
        const newSet = new Set(prev)
        newSet.delete(kbId)
        return newSet
      })
    }
  }

  // 删除知识库
  const handleDeleteKb = async (kbId, kbName) => {
    if (!confirm(`确定要删除知识库 "${kbName}" 吗？此操作不可恢复。`)) return

    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/${kbId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        loadKnowledgeBases()
        if (selectedKb?.id === kbId) {
          setSelectedKb(null)
        }
      } else {
        const result = await response.json()
        alert(`删除失败: ${result.detail || result.error}`)
      }
    } catch (error) {
      alert(`删除失败: ${error.message}`)
    }
  }


  // 获取知识库详情
  const handleSelectKb = async (kb) => {
    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/${kb.id}`)
      const result = await response.json()
      
      if (response.ok) {
        setSelectedKb(result)
      } else {
        setSelectedKb(kb)
      }
    } catch (error) {
      setSelectedKb(kb)
    }
  }

  // 页面加载时获取知识库列表
  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  return (
    <div className="knowledge-base">
      <div className="knowledge-base-header">
        <h1>知识库管理</h1>
        <p>创建和管理知识库</p>
      </div>

      <div className="knowledge-base-actions">
        <button 
          onClick={() => setShowCreateForm(true)}
          className="create-btn"
        >
          创建知识库
        </button>
        <button 
          onClick={loadKnowledgeBases}
          disabled={loading}
          className="refresh-btn"
        >
          {loading ? '加载中...' : '刷新列表'}
        </button>
      </div>

      {showCreateForm && (
        <div className="create-form-overlay">
          <div className="create-form-modal">
            <h3>创建新知识库</h3>
            <form onSubmit={handleCreateKb}>
              <div className="form-group">
                <label>知识库ID（可选）</label>
                <input
                  type="text"
                  value={createFormData.kb_id}
                  onChange={(e) => setCreateFormData({...createFormData, kb_id: e.target.value})}
                  placeholder="留空自动生成"
                />
              </div>
              <div className="form-group">
                <label>知识库名称</label>
                <input
                  type="text"
                  value={createFormData.name}
                  onChange={(e) => setCreateFormData({...createFormData, name: e.target.value})}
                  placeholder="输入知识库名称"
                  required
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  value={createFormData.description}
                  onChange={(e) => setCreateFormData({...createFormData, description: e.target.value})}
                  placeholder="输入知识库描述（可选）"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>数据源ID</label>
                <input
                  type="text"
                  value={createFormData.datasource_id}
                  onChange={(e) => setCreateFormData({...createFormData, datasource_id: e.target.value})}
                  placeholder="数据源ID"
                />
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowCreateForm(false)}>
                  取消
                </button>
                <button type="submit" disabled={creating}>
                  {creating ? '创建中...' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="knowledge-base-content">
        <div className="kb-list-section">
          <h2>知识库列表</h2>
          {loading ? (
            <div className="loading">加载中...</div>
          ) : knowledgeBases.length === 0 ? (
            <div className="empty-state">
              <p>暂无知识库</p>
              <button onClick={() => setShowCreateForm(true)}>创建第一个知识库</button>
            </div>
          ) : (
            <div className="kb-list">
              {knowledgeBases.map(kb => (
                <div 
                  key={kb.id} 
                  className={`kb-item ${selectedKb?.id === kb.id ? 'selected' : ''}`}
                  onClick={() => handleSelectKb(kb)}
                >
                  <div className="kb-info">
                    <h3>{kb.name}</h3>
                    <p>{kb.description || '无描述'}</p>
                    <div className="kb-meta">
                      <span className={`status ${kb.status}`}>{kb.status}</span>
                      <span className="date">{new Date(kb.created_at).toLocaleDateString()}</span>
                    </div>
                    {kb.metrics && (
                      <div className="kb-metrics">
                        <span>实体: {kb.metrics.entities_count}</span>
                        <span>关系: {kb.metrics.relations_count}</span>
                        <span>文档: {kb.metrics.documents_count}</span>
                      </div>
                    )}
                  </div>
                  <div className="kb-actions">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation()
                        handleBuildKb(kb.id)
                      }}
                      disabled={buildingKbs.has(kb.id)}
                      className="build-btn"
                    >
                      {buildingKbs.has(kb.id) ? '构建中...' : '构建'}
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteKb(kb.id, kb.name)
                      }}
                      className="delete-btn"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedKb && (
          <div className="kb-detail-section">
            <h2>知识库详情</h2>
            <div className="kb-detail">
              <div className="detail-header">
                <h3>{selectedKb.name}</h3>
                <span className={`status ${selectedKb.status}`}>{selectedKb.status}</span>
              </div>
              <p>{selectedKb.description || '无描述'}</p>
              
              {selectedKb.metrics && (
                <div className="metrics-grid">
                  <div className="metric-item">
                    <span className="metric-value">{selectedKb.metrics.entities_count}</span>
                    <span className="metric-label">实体数量</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-value">{selectedKb.metrics.relations_count}</span>
                    <span className="metric-label">关系数量</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-value">{selectedKb.metrics.documents_count}</span>
                    <span className="metric-label">文档数量</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-value">{selectedKb.metrics.build_time?.toFixed(2) || 0}s</span>
                    <span className="metric-label">构建时间</span>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default KnowledgeBase