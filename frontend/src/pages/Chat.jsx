import { useState, useEffect, useRef } from 'react'
import { useBackend } from '../context/BackendContext'
import ReactMarkdown from 'react-markdown'
import './Chat.css'

function Chat() {
  const { backendUrl } = useBackend()
  
  // 知识库相关状态
  const [knowledgeBases, setKnowledgeBases] = useState([])
  const [selectedKbId, setSelectedKbId] = useState('')
  const [loadingKbs, setLoadingKbs] = useState(false)
  const [backendError, setBackendError] = useState(null)
  
  // 聊天相关状态
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchType, setSearchType] = useState('hybrid')
  
  // 引用
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // 滚动到消息底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    setLoadingKbs(true)
    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/`)
      
      // 检查响应是否为 JSON
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('后端服务器返回了非JSON响应，请检查后端服务是否正在运行')
      }
      
      const data = await response.json()
      
      if (response.ok) {
        const readyKbs = data.knowledge_bases?.filter(kb => kb.status === 'ready') || []
        setKnowledgeBases(readyKbs)
        setBackendError(null) // 清除错误状态
        if (readyKbs.length > 0 && !selectedKbId) {
          setSelectedKbId(readyKbs[0].id)
        }
      } else {
        console.error('Failed to load knowledge bases:', data)
      }
    } catch (error) {
      console.error('Error loading knowledge bases:', error)
      // 如果是网络错误或服务器没有运行，显示友好的错误信息
      setKnowledgeBases([])
      setBackendError(error.message || '无法连接到后端服务器')
    } finally {
      setLoadingKbs(false)
    }
  }

  // 发送消息到知识库
  const handleSendMessage = async (e) => {
    e.preventDefault()
    
    if (!inputMessage.trim() || !selectedKbId || isSearching) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsSearching(true)

    try {
      const response = await fetch(`${backendUrl}/api/v1/knowledge-base/${selectedKbId}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: userMessage.content,
          search_type: searchType,
          top_k: 5
        })
      })

      const result = await response.json()
      
      if (response.ok && result.results && result.results.length > 0) {
        const botMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: result.results[0].content,
          timestamp: new Date(),
          metadata: {
            search_type: result.search_type,
            search_time: result.search_time,
            total_results: result.total_count,
            confidence: result.results[0].confidence || 0.95
          }
        }
        setMessages(prev => [...prev, botMessage])
      } else {
        const errorMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: '抱歉，我在知识库中没有找到相关信息。请尝试换个问题或检查知识库是否已正确构建。',
          timestamp: new Date(),
          isError: true
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error('Search failed:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: '抱歉，查询过程中出现了错误。请稍后重试。',
        timestamp: new Date(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsSearching(false)
      inputRef.current?.focus()
    }
  }

  // 清空对话
  const clearChat = () => {
    setMessages([])
  }

  // 切换知识库时清空对话
  const handleKbChange = (kbId) => {
    setSelectedKbId(kbId)
    setMessages([])
  }

  // 页面加载时获取知识库列表
  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  return (
    <div className="chat-page">
      <div className="chat-page-content">
        <div className="chat-header">
          <h1>知识库对话</h1>
          <p>与知识库进行智能对话，基于您的知识库内容获取精准答案</p>
        </div>

        <div className="chat-main-layout">
          {/* 左侧对话区域 */}
          <div className="chat-left-panel">
            {backendError ? (
              <div className="error-section">
                <div className="error-card">
                  <h2>连接错误</h2>
                  <div className="error-content">
                    <div className="error-icon">⚠️</div>
                    <div className="error-details">
                      <p className="error-message">{backendError}</p>
                      <p className="error-suggestion">请确保后端服务器正在运行，然后点击重新连接。</p>
                      <button 
                        onClick={() => {
                          setBackendError(null)
                          loadKnowledgeBases()
                        }}
                        className="retry-btn"
                      >
                        重新连接
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : !selectedKbId ? (
              <div className="welcome-section">
                <div className="welcome-card">
                  <h2>开始对话</h2>
                  <div className="welcome-content">
                    <div className="welcome-icon">💬</div>
                    <div className="welcome-text">
                      <p>请先选择一个知识库开始对话</p>
                      {knowledgeBases.length === 0 && (
                        <p className="welcome-hint">
                          当前没有可用的知识库，请先在右侧
                          <strong>知识库管理</strong>区域创建并构建知识库。
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="chat-section">
                <div className="chat-card">
                  <div className="chat-header-info">
                    <h2>对话窗口</h2>
                    <div className="kb-info">
                      <span className="kb-label">当前知识库:</span>
                      <span className="kb-name">{knowledgeBases.find(kb => kb.id === selectedKbId)?.name}</span>
                      <span className="kb-stats">
                        {knowledgeBases.find(kb => kb.id === selectedKbId)?.metrics?.documents_count || 0} 文档
                      </span>
                    </div>
                  </div>
                  
                  <div className="messages-container">
                    {messages.length === 0 ? (
                      <div className="empty-chat">
                        <div className="empty-icon">🤖</div>
                        <h3>开始您的智能对话</h3>
                        <p>您可以向知识库提问，我会基于知识库内容为您提供精准答案。</p>
                        <div className="example-questions">
                          <p className="example-title">试试这些问题:</p>
                          <div className="example-tags">
                            <span className="example-tag">这个知识库包含什么内容？</span>
                            <span className="example-tag">请总结一下主要信息</span>
                            <span className="example-tag">有什么关键数据？</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                    messages.map(message => (
                      <div key={message.id} className={`message-wrapper ${message.type}`}>
                        <div className="message-avatar">
                          {message.type === 'user' ? '👤' : '🤖'}
                        </div>
                        <div className="message-bubble">
                          <div className="message-content">
                            {message.type === 'bot' ? (
                              <div className="markdown-content">
                                {(() => {
                                  try {
                                    return (
                                      <ReactMarkdown>
                                        {message.content || ''}
                                      </ReactMarkdown>
                                    )
                                  } catch (error) {
                                    console.error('Markdown rendering error:', error)
                                    return <div>{message.content}</div>
                                  }
                                })()}
                              </div>
                            ) : (
                              <div className="plain-content">{message.content}</div>
                            )}
                          </div>
                          <div className="message-meta">
                            <span className="timestamp">
                              {message.timestamp.toLocaleTimeString()}
                            </span>
                            {message.metadata && (
                              <div className="metadata-details">
                                <span className="meta-item">⏱️ {message.metadata.search_time?.toFixed(2) || 0}s</span>
                                <span className="meta-item">🎯 {(message.metadata.confidence * 100).toFixed(1)}%</span>
                                <span className="meta-item">🔍 {message.metadata.search_type}</span>
                              </div>
                            )}
                            {message.isError && (
                              <span className="error-badge">错误</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                  {isSearching && (
                    <div className="message-wrapper bot">
                      <div className="message-avatar">🤖</div>
                      <div className="message-bubble typing">
                        <div className="typing-indicator">
                          <div className="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                          </div>
                          <span className="typing-text">正在搜索知识库...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="input-section">
                  <form onSubmit={handleSendMessage} className="input-form">
                    <div className="input-container">
                      <div className="input-wrapper">
                        <input
                          ref={inputRef}
                          type="text"
                          value={inputMessage}
                          onChange={(e) => setInputMessage(e.target.value)}
                          placeholder="输入您的问题，按 Enter 发送..."
                          disabled={isSearching}
                          className="message-input"
                        />
                        <button 
                          type="submit" 
                          disabled={!inputMessage.trim() || isSearching}
                          className="send-button"
                        >
                          {isSearching ? (
                            <span className="loading-spinner">⏳</span>
                          ) : (
                            <span className="send-icon">➤</span>
                          )}
                        </button>
                      </div>
                    </div>
                  </form>
                </div>
              </div>
            </div>
            )}
          </div>

          {/* 右侧设置面板 */}
          <div className="chat-right-panel">
            <div className="controls-card">
              <h2>对话设置</h2>
              
              <div className="controls-grid">
                <div className="form-group">
                  <label>选择知识库</label>
                  <select 
                    value={selectedKbId} 
                    onChange={(e) => handleKbChange(e.target.value)}
                    disabled={loadingKbs}
                    className="form-select"
                  >
                    <option value="">请选择知识库</option>
                    {knowledgeBases.map(kb => (
                      <option key={kb.id} value={kb.id}>
                        {kb.name} ({kb.metrics?.documents_count || 0} 文档)
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>搜索模式</label>
                  <select 
                    value={searchType} 
                    onChange={(e) => setSearchType(e.target.value)}
                    className="form-select"
                  >
                    <option value="hybrid">混合搜索</option>
                    <option value="naive">基础搜索</option>
                    <option value="local">本地搜索</option>
                    <option value="global">全局搜索</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>操作</label>
                  <div className="button-group">
                    <button 
                      onClick={loadKnowledgeBases} 
                      disabled={loadingKbs} 
                      className="control-btn refresh-btn"
                    >
                      {loadingKbs ? '刷新中...' : '刷新列表'}
                    </button>
                    <button 
                      onClick={clearChat} 
                      className="control-btn clear-btn" 
                      disabled={messages.length === 0}
                    >
                      清空对话
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Chat