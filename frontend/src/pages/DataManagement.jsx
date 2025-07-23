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

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files))
  }

  const handleUpload = async () => {
    if (!files.length || !dbName) return

    setUploading(true)
    setUploadResult(null)

    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('db_name', dbName)

    try {
      const response = await fetch(`${backendUrl}/upload-xlsx`, {
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

  const handlePreviewSchema = async (dbName) => {
    setLoadingSchema(true)
    setSchemaData(null)

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

  return (
    <div className="data-management">
      <div className="data-management-header">
        <h1>数据管理</h1>
        <p>上传 Excel 文件并预览数据结构</p>
      </div>

      <div className="upload-section">
        <div className="upload-card">
          <h2>上传数据文件</h2>
          
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
            <label htmlFor="file-input">选择文件 (.xlsx)</label>
            <input
              id="file-input"
              type="file"
              multiple
              accept=".xlsx"
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
                  <h3>数据库: {schemaData.database_name}</h3>
                  <p>共 {schemaData.tables.length} 个表</p>
                </div>

                {schemaData.tables.map((table, index) => (
                  <div key={index} className="table-schema">
                    <h4>{table.table_name}</h4>
                    <p className="table-meta">{table.row_count} 行数据</p>
                    
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
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default DataManagement