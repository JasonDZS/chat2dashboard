import { useState } from 'react'
import { useBackend } from '../context/BackendContext'
import './DataManagement.css'

function DataManagement() {
  const { backendUrl } = useBackend()
  const [files, setFiles] = useState([])
  const [dbName, setDbName] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [schemaData, setSchemaData] = useState(null)
  const [loadingSchema, setLoadingSchema] = useState(false)
  const [previewDbName, setPreviewDbName] = useState('')
  
  // Document upload states
  const [documentFiles, setDocumentFiles] = useState([])
  const [kbId, setKbId] = useState('')
  const [uploadingDocs, setUploadingDocs] = useState(false)
  const [documentUploadResult, setDocumentUploadResult] = useState(null)
  
  // Table collapse states
  const [collapsedTables, setCollapsedTables] = useState(new Set())

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files))
  }

  const handleDocumentFileChange = (e) => {
    setDocumentFiles(Array.from(e.target.files))
  }

  const handleUpload = async () => {
    if (!files.length || !dbName) return

    setUploading(true)
    setUploadResult(null)

    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('db_name', dbName)

    try {
      const response = await fetch(`${backendUrl}/upload-files`, {
        method: 'POST',
        body: formData
      })

      const result = await response.json()
      
      if (response.ok) {
        setUploadResult(result)
        setFiles([])
        setDbName('')
        document.getElementById('file-input').value = ''
      } else {
        setUploadResult({ error: result.error })
      }
    } catch (error) {
      setUploadResult({ error: error.message })
    } finally {
      setUploading(false)
    }
  }

  const handleDocumentUpload = async () => {
    if (!documentFiles.length || !kbId) return

    setUploadingDocs(true)
    setDocumentUploadResult(null)

    const formData = new FormData()
    documentFiles.forEach(file => formData.append('files', file))
    formData.append('kb_id', kbId)
    formData.append('process_immediately', 'true')

    try {
      const response = await fetch(`${backendUrl}/api/v1/document/upload`, {
        method: 'POST',
        body: formData
      })

      const result = await response.json()
      
      if (response.ok) {
        setDocumentUploadResult(result)
        setDocumentFiles([])
        setKbId('')
        document.getElementById('document-file-input').value = ''
      } else {
        setDocumentUploadResult({ error: result.detail || result.error || '上传失败' })
      }
    } catch (error) {
      setDocumentUploadResult({ error: error.message })
    } finally {
      setUploadingDocs(false)
    }
  }

  const handlePreviewSchema = async (dbName) => {
    setLoadingSchema(true)
    setSchemaData(null)
    setCollapsedTables(new Set()) // Reset collapse state when loading new schema

    try {
      const response = await fetch(`${backendUrl}/schema/${dbName}`)
      const result = await response.json()
      
      if (response.ok) {
        setSchemaData(result)
      } else {
        setSchemaData({ error: result.error })
      }
    } catch (error) {
      setSchemaData({ error: error.message })
    } finally {
      setLoadingSchema(false)
    }
  }

  const toggleTableCollapse = (tableIndex) => {
    const newCollapsedTables = new Set(collapsedTables)
    if (newCollapsedTables.has(tableIndex)) {
      newCollapsedTables.delete(tableIndex)
    } else {
      newCollapsedTables.add(tableIndex)
    }
    setCollapsedTables(newCollapsedTables)
  }

  const toggleAllTables = () => {
    if (!schemaData) return
    
    if (collapsedTables.size === schemaData.tables.length) {
      // All collapsed, expand all
      setCollapsedTables(new Set())
    } else {
      // Some or none collapsed, collapse all
      setCollapsedTables(new Set(schemaData.tables.map((_, index) => index)))
    }
  }

  return (
    <div className="data-management">
      <div className="data-management-header">
        <h1>数据管理</h1>
        <p>上传 Excel/CSV 文件或文档文件并预览数据结构</p>
      </div>

      <div className="upload-sections-grid">
        <div className="upload-card">
          <h2>上传文档文件</h2>
          <p>支持 PDF、Word、文本、表格、图片等文档格式</p>
          
          <div className="form-group">
            <label htmlFor="kb-id">知识库ID</label>
            <input
              id="kb-id"
              type="text"
              value={kbId}
              onChange={(e) => setKbId(e.target.value)}
              placeholder="输入知识库ID"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="document-file-input">选择文档 (.pdf, .docx, .doc, .txt, .md, .html, .csv, .xlsx, .json, .jpg, .png)</label>
            <input
              id="document-file-input"
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.txt,.md,.markdown,.html,.csv,.xlsx,.json,.jpg,.jpeg,.png"
              onChange={handleDocumentFileChange}
              className="form-file-input"
            />
            {documentFiles.length > 0 && (
              <div className="file-list">
                <p>已选择 {documentFiles.length} 个文档：</p>
                <ul>
                  {documentFiles.map((file, index) => (
                    <li key={index}>{file.name}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <button
            onClick={handleDocumentUpload}
            disabled={!documentFiles.length || !kbId || uploadingDocs}
            className="upload-btn"
          >
            {uploadingDocs ? '上传中...' : '上传文档'}
          </button>

          {documentUploadResult && (
            <div className={`upload-result ${documentUploadResult.error ? 'error' : 'success'}`}>
              {documentUploadResult.error ? (
                <div>
                  <h3>上传失败</h3>
                  <p>{documentUploadResult.error}</p>
                </div>
              ) : (
                <div>
                  <h3>上传成功</h3>
                  <p>任务ID: {documentUploadResult.task_id}</p>
                  <p>状态: {documentUploadResult.status}</p>
                  <p>共上传 {documentUploadResult.total_files} 个文档到知识库 "{documentUploadResult.kb_id}"</p>
                  
                  <div className="files-info">
                    <h4>上传的文档：</h4>
                    {documentUploadResult.uploaded_files?.map((file, index) => (
                      <div key={index} className="file-info">
                        <strong>{file.filename}</strong> ({(file.size / 1024).toFixed(1)} KB) - {file.status}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="upload-card">
          <h2>上传数据文件 (Excel/CSV)</h2>
          <p>支持 Excel 和 CSV 格式</p>
          <div className="form-group">
            <label htmlFor="db-name">数据库名称</label>
            <input
              id="db-name"
              type="text"
              value={dbName}
              onChange={(e) => setDbName(e.target.value)}
              placeholder="输入数据库名称"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="file-input">选择文件 (.xlsx, .csv)</label>
            <input
              id="file-input"
              type="file"
              multiple
              accept=".xlsx,.csv"
              onChange={handleFileChange}
              className="form-file-input"
            />
            {files.length > 0 && (
              <div className="file-list">
                <p>已选择 {files.length} 个文件：</p>
                <ul>
                  {files.map((file, index) => (
                    <li key={index}>{file.name}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <button
            onClick={handleUpload}
            disabled={!files.length || !dbName || uploading}
            className="upload-btn"
          >
            {uploading ? '上传中...' : '上传文件'}
          </button>

          {uploadResult && (
            <div className={`upload-result ${uploadResult.error ? 'error' : 'success'}`}>
              {uploadResult.error ? (
                <div>
                  <h3>上传失败</h3>
                  <p>{uploadResult.error}</p>
                </div>
              ) : (
                <div>
                  <h3>上传成功</h3>
                  <p>数据库 "{uploadResult.database_name}" 创建成功</p>
                  <p>共处理 {uploadResult.total_files} 个文件，创建 {uploadResult.tables.length} 个表</p>
                  
                  <div className="tables-info">
                    <h4>创建的表：</h4>
                    {uploadResult.tables.map((table, index) => (
                      <div key={index} className="table-info">
                        <strong>{table.table_name}</strong> ({table.rows} 行, {table.columns.length} 列)
                        <br />
                        <small>来源文件: {table.filename}</small>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={() => handlePreviewSchema(uploadResult.database_name)}
                    className="preview-btn"
                  >
                    预览数据结构
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="preview-section">
        <div className="preview-card">
          <h2>预览现有数据库</h2>
          
          <div className="form-group">
            <label htmlFor="preview-db-name">数据库名称</label>
            <input
              id="preview-db-name"
              type="text"
              value={previewDbName}
              onChange={(e) => setPreviewDbName(e.target.value)}
              placeholder="输入要预览的数据库名称"
              className="form-input"
            />
          </div>

          <button
            onClick={() => handlePreviewSchema(previewDbName)}
            disabled={!previewDbName || loadingSchema}
            className="preview-btn"
          >
            {loadingSchema ? '加载中...' : '预览数据结构'}
          </button>
        </div>
      </div>

      {schemaData && (
        <div className="schema-section">
          <div className="schema-card">
            <h2>数据结构预览</h2>
            
            {loadingSchema ? (
              <p>加载中...</p>
            ) : schemaData.error ? (
              <div className="error">
                <p>获取数据结构失败: {schemaData.error}</p>
              </div>
            ) : (
              <div className="schema-content">
                <div className="schema-header">
                  <div className="schema-header-content">
                    <h3>数据库: {schemaData.database_name}</h3>
                    <p>共 {schemaData.tables.length} 个表</p>
                  </div>
                  <button 
                    className="toggle-all-btn"
                    onClick={toggleAllTables}
                    title={collapsedTables.size === schemaData.tables.length ? "展开所有表格" : "折叠所有表格"}
                  >
                    {collapsedTables.size === schemaData.tables.length ? "📂" : "📁"} 
                    {collapsedTables.size === schemaData.tables.length ? " 全部展开" : " 全部折叠"}
                  </button>
                </div>

                {schemaData.tables.map((table, index) => {
                  const isCollapsed = collapsedTables.has(index)
                  return (
                    <div key={index} className="table-schema">
                      <div 
                        className="table-header" 
                        onClick={() => toggleTableCollapse(index)}
                      >
                        <div className="table-header-content">
                          <h4>{table.table_name}</h4>
                          <p className="table-meta">{table.row_count} 行数据</p>
                        </div>
                        <div className={`collapse-icon ${isCollapsed ? 'collapsed' : ''}`}>
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path 
                              d="M4 6L8 10L12 6" 
                              stroke="currentColor" 
                              strokeWidth="2" 
                              strokeLinecap="round" 
                              strokeLinejoin="round"
                            />
                          </svg>
                        </div>
                      </div>
                      
                      <div className={`columns-container ${isCollapsed ? 'collapsed' : ''}`}>
                        <div className="columns-grid">
                          {table.columns.map((column, colIndex) => (
                            <div key={colIndex} className="column-info">
                              <span className="column-name">{column.name}</span>
                              <span className="column-type">{column.type}</span>
                              {column.primary_key && <span className="column-pk">PK</span>}
                              {column.not_null && <span className="column-nn">NOT NULL</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default DataManagement