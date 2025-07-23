import React, { useState, useEffect } from 'react';
import { useBackend } from '../context/BackendContext';
import './TrainingDataEditor.css';

const TrainingDataEditor = () => {
  const { backendUrl } = useBackend();
  const [databases, setDatabases] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState('');
  const [schemaData, setSchemaData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  
  // Form states for adding new SQL training data
  const [newQuestion, setNewQuestion] = useState('');
  const [newSql, setNewSql] = useState('');
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Form states for adding new document
  const [newDocTitle, setNewDocTitle] = useState('');
  const [newDocContent, setNewDocContent] = useState('');
  const [isAddingNewDoc, setIsAddingNewDoc] = useState(false);
  
  // Editing states
  const [editingTable, setEditingTable] = useState(null);
  const [editingSql, setEditingSql] = useState(null);
  const [editingDocument, setEditingDocument] = useState(null);

  // Load databases on component mount
  useEffect(() => {
    fetchDatabases();
  }, []);

  // Load schema data when database changes
  useEffect(() => {
    if (selectedDatabase) {
      fetchSchemaData();
    }
  }, [selectedDatabase]);

  const fetchDatabases = async () => {
    try {
      const response = await fetch(`${backendUrl}/databases`);
      const data = await response.json();
      setDatabases(data);
      
      // Auto-select first database if available
      if (data.length > 0 && !selectedDatabase) {
        setSelectedDatabase(data[0].name);
      }
    } catch (err) {
      setError('Failed to fetch databases: ' + err.message);
    }
  };

  const fetchSchemaData = async () => {
    if (!selectedDatabase) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${backendUrl}/schema-json/${selectedDatabase}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setSchemaData(data);
    } catch (err) {
      setError('Failed to fetch schema data: ' + err.message);
      setSchemaData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddSqlTraining = async () => {
    if (!newQuestion.trim() || !newSql.trim()) {
      setError('Both question and SQL are required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${backendUrl}/schema-json/${selectedDatabase}/sql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: newQuestion.trim(),
          sql: newSql.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setSuccessMessage(result.message);
      setNewQuestion('');
      setNewSql('');
      setIsAddingNew(false);
      
      // Refresh schema data
      await fetchSchemaData();
    } catch (err) {
      setError('Failed to add training data: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSqlTraining = async (index) => {
    if (!confirm('Are you sure you want to delete this training data?')) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${backendUrl}/schema-json/${selectedDatabase}/sql/${index}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setSuccessMessage(result.message);
      
      // Refresh schema data
      await fetchSchemaData();
    } catch (err) {
      setError('Failed to delete training data: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAISql = async (numQuestions = 10) => {
    if (!selectedDatabase) {
      setError('Please select a database first');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${backendUrl}/generate-sql/${selectedDatabase}?num_questions=${numQuestions}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setSuccessMessage(`${result.message}. Added ${result.validated_records} new SQL records.`);
      
      // Refresh schema data
      await fetchSchemaData();
    } catch (err) {
      setError('Failed to generate AI SQL: ' + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAddDocument = () => {
    if (!newDocContent.trim()) {
      setError('Document content is required');
      return;
    }

    const newDoc = {
      title: newDocTitle.trim() || undefined,
      content: newDocContent.trim()
    };

    const updatedDocuments = [...(schemaData.documents || []), newDoc];
    setSchemaData({ ...schemaData, documents: updatedDocuments });
    
    setNewDocTitle('');
    setNewDocContent('');
    setIsAddingNewDoc(false);
    setSuccessMessage('Document added successfully');
  };

  const handleDeleteDocument = (index) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    const updatedDocuments = [...(schemaData.documents || [])];
    updatedDocuments.splice(index, 1);
    setSchemaData({ ...schemaData, documents: updatedDocuments });
    setSuccessMessage('Document deleted successfully');
  };

  const handleUpdateSchema = async () => {
    if (!schemaData) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${backendUrl}/schema-json/${selectedDatabase}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(schemaData),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setSuccessMessage(result.message);
      
      // Refresh schema data
      await fetchSchemaData();
    } catch (err) {
      setError('Failed to update schema: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear messages after 3 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <div className="training-data-editor">
      <div className="page-header">
        <h1>Training Data Editor</h1>
        <p>Manage SQL training data for database agents</p>
      </div>

      {/* Database Selection */}
      <div className="database-selection">
        <label htmlFor="database-select">Select Database:</label>
        <select
          id="database-select"
          value={selectedDatabase}
          onChange={(e) => setSelectedDatabase(e.target.value)}
          disabled={isLoading}
        >
          <option value="">Choose a database...</option>
          {databases.map((db) => (
            <option key={db.name} value={db.name}>
              {db.name} ({db.table_count} tables)
            </option>
          ))}
        </select>
      </div>

      {/* Messages */}
      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}

      {/* Loading */}
      {isLoading && <div className="loading">Loading...</div>}

      {/* Schema Data Display */}
      {schemaData && (
        <div className="schema-content">
          {/* Database Info */}
          <div className="schema-section">
            <h2>Database Information</h2>
            <div className="info-grid">
              <div className="info-item">
                <label>Database Name:</label>
                <span>{schemaData.database_name}</span>
              </div>
              <div className="info-item">
                <label>Created:</label>
                <span>{schemaData.created_at ? new Date(schemaData.created_at).toLocaleString() : 'N/A'}</span>
              </div>
              <div className="info-item">
                <label>Last Updated:</label>
                <span>{schemaData.updated_at ? new Date(schemaData.updated_at).toLocaleString() : 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Tables Info */}
          <div className="schema-section">
            <h2>Tables ({Object.keys(schemaData.tables || {}).length})</h2>
            <div className="tables-list">
              {Object.entries(schemaData.tables || {}).map(([tableName, createSql]) => (
                <div key={tableName} className="table-item">
                  <div className="table-header">
                    <h3>{tableName}</h3>
                    <button
                      className="btn btn-small btn-secondary"
                      onClick={() => setEditingTable(editingTable === tableName ? null : tableName)}
                      disabled={isLoading}
                    >
                      {editingTable === tableName ? 'Cancel' : 'Edit'}
                    </button>
                  </div>
                  {editingTable === tableName ? (
                    <div className="edit-form">
                      <textarea
                        value={createSql}
                        onChange={(e) => {
                          const updatedTables = { ...schemaData.tables };
                          updatedTables[tableName] = e.target.value;
                          setSchemaData({ ...schemaData, tables: updatedTables });
                        }}
                        rows="8"
                        className="sql-editor"
                      />
                      <div className="edit-actions">
                        <button
                          className="btn btn-success btn-small"
                          onClick={() => setEditingTable(null)}
                          disabled={isLoading}
                        >
                          Save
                        </button>
                      </div>
                    </div>
                  ) : (
                    <pre className="sql-code">{createSql}</pre>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Documents */}
          <div className="schema-section">
            <div className="section-header">
              <h2>Documents ({(schemaData.documents || []).length})</h2>
              <button
                className="btn btn-primary"
                onClick={() => setIsAddingNewDoc(!isAddingNewDoc)}
                disabled={isLoading}
              >
                {isAddingNewDoc ? 'Cancel' : 'Add New'}
              </button>
            </div>

            {/* Add New Document Form */}
            {isAddingNewDoc && (
              <div className="add-document-form">
                <div className="form-group">
                  <label htmlFor="new-doc-title">Title (optional):</label>
                  <input
                    id="new-doc-title"
                    type="text"
                    value={newDocTitle}
                    onChange={(e) => setNewDocTitle(e.target.value)}
                    placeholder="Enter document title..."
                    disabled={isLoading}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="new-doc-content">Content:</label>
                  <textarea
                    id="new-doc-content"
                    value={newDocContent}
                    onChange={(e) => setNewDocContent(e.target.value)}
                    placeholder="Enter document content..."
                    rows="6"
                    disabled={isLoading}
                  />
                </div>
                <div className="form-actions">
                  <button
                    className="btn btn-success"
                    onClick={handleAddDocument}
                    disabled={isLoading || !newDocContent.trim()}
                  >
                    Add Document
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      setIsAddingNewDoc(false);
                      setNewDocTitle('');
                      setNewDocContent('');
                    }}
                    disabled={isLoading}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            <div className="documents-list">
                {(schemaData.documents || []).map((doc, index) => (
                  <div key={index} className="document-item">
                    <div className="document-header">
                      <h3>Document #{index + 1}</h3>
                      {doc.title && <span className="document-title">{doc.title}</span>}
                      <div className="document-actions">
                        <button
                          className="btn btn-small btn-secondary"
                          onClick={() => setEditingDocument(editingDocument === index ? null : index)}
                          disabled={isLoading}
                        >
                          {editingDocument === index ? 'Cancel' : 'Edit'}
                        </button>
                        <button
                          className="btn btn-small btn-danger"
                          onClick={() => handleDeleteDocument(index)}
                          disabled={isLoading}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                    <div className="document-content">
                      {editingDocument === index ? (
                        <div className="edit-form">
                          {doc.title !== undefined && (
                            <div className="form-group">
                              <label>Title:</label>
                              <input
                                type="text"
                                value={doc.title || ''}
                                onChange={(e) => {
                                  const updatedDocuments = [...schemaData.documents];
                                  updatedDocuments[index] = { ...updatedDocuments[index], title: e.target.value };
                                  setSchemaData({ ...schemaData, documents: updatedDocuments });
                                }}
                                className="title-editor"
                              />
                            </div>
                          )}
                          <div className="form-group">
                            <label>Content:</label>
                            <textarea
                              value={doc.content || doc.text || JSON.stringify(doc, null, 2)}
                              onChange={(e) => {
                                const updatedDocuments = [...schemaData.documents];
                                if (doc.content !== undefined) {
                                  updatedDocuments[index] = { ...updatedDocuments[index], content: e.target.value };
                                } else if (doc.text !== undefined) {
                                  updatedDocuments[index] = { ...updatedDocuments[index], text: e.target.value };
                                } else {
                                  try {
                                    updatedDocuments[index] = JSON.parse(e.target.value);
                                  } catch {
                                    // Keep as string if JSON parsing fails
                                  }
                                }
                                setSchemaData({ ...schemaData, documents: updatedDocuments });
                              }}
                              rows="8"
                              className="document-editor"
                            />
                          </div>
                          <div className="edit-actions">
                            <button
                              className="btn btn-success btn-small"
                              onClick={() => setEditingDocument(null)}
                              disabled={isLoading}
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      ) : (
                        <pre className="document-text">{doc.content || doc.text || JSON.stringify(doc, null, 2)}</pre>
                      )}
                    </div>
                  </div>
                ))}
                {(!schemaData.documents || schemaData.documents.length === 0) && (
                  <p className="no-data">No documents available. Add some to get started!</p>
                )}
              </div>
            </div>

          {/* SQL Training Data */}
          <div className="schema-section">
            <div className="section-header">
              <h2>SQL Training Data ({(schemaData.sql || []).length})</h2>
              <div className="section-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => handleGenerateAISql(10)}
                  disabled={isLoading || isGenerating}
                  style={{ marginRight: '8px' }}
                >
                  {isGenerating ? 'Gen...' : '🌟'}
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => setIsAddingNew(!isAddingNew)}
                  disabled={isLoading}
                >
                  {isAddingNew ? 'Cancel' : 'Add New'}
                </button>
              </div>
            </div>

            {/* Add New Form */}
            {isAddingNew && (
              <div className="add-training-form">
                <div className="form-group">
                  <label htmlFor="new-question">Question:</label>
                  <input
                    id="new-question"
                    type="text"
                    value={newQuestion}
                    onChange={(e) => setNewQuestion(e.target.value)}
                    placeholder="Enter natural language question..."
                    disabled={isLoading}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="new-sql">SQL:</label>
                  <textarea
                    id="new-sql"
                    value={newSql}
                    onChange={(e) => setNewSql(e.target.value)}
                    placeholder="Enter corresponding SQL query..."
                    rows="4"
                    disabled={isLoading}
                  />
                </div>
                <div className="form-actions">
                  <button
                    className="btn btn-success"
                    onClick={handleAddSqlTraining}
                    disabled={isLoading || !newQuestion.trim() || !newSql.trim()}
                  >
                    Add Training Data
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      setIsAddingNew(false);
                      setNewQuestion('');
                      setNewSql('');
                    }}
                    disabled={isLoading}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Training Data List */}
            <div className="training-data-list">
              {(schemaData.sql || []).map((item, index) => (
                <div key={index} className="training-item">
                  <div className="training-header">
                    <span className="training-index">#{index + 1}</span>
                    <span className="training-date">
                      {item.added_at ? new Date(item.added_at).toLocaleDateString() : 'N/A'}
                    </span>
                    <div className="training-actions">
                      <button
                        className="btn btn-secondary btn-small"
                        onClick={() => setEditingSql(editingSql === index ? null : index)}
                        disabled={isLoading}
                      >
                        {editingSql === index ? 'Cancel' : 'Edit'}
                      </button>
                      <button
                        className="btn btn-danger btn-small"
                        onClick={() => handleDeleteSqlTraining(index)}
                        disabled={isLoading}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="training-content">
                    <div className="question">
                      <label>Question:</label>
                      {editingSql === index ? (
                        <input
                          type="text"
                          value={item.question}
                          onChange={(e) => {
                            const updatedSql = [...schemaData.sql];
                            updatedSql[index] = { ...updatedSql[index], question: e.target.value };
                            setSchemaData({ ...schemaData, sql: updatedSql });
                          }}
                          className="question-editor"
                        />
                      ) : (
                        <p>{item.question}</p>
                      )}
                    </div>
                    <div className="sql">
                      <label>SQL:</label>
                      {editingSql === index ? (
                        <div className="edit-form">
                          <textarea
                            value={item.sql}
                            onChange={(e) => {
                              const updatedSql = [...schemaData.sql];
                              updatedSql[index] = { ...updatedSql[index], sql: e.target.value };
                              setSchemaData({ ...schemaData, sql: updatedSql });
                            }}
                            rows="4"
                            className="sql-editor"
                          />
                          <div className="edit-actions">
                            <button
                              className="btn btn-success btn-small"
                              onClick={() => setEditingSql(null)}
                              disabled={isLoading}
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      ) : (
                        <pre className="sql-code">{item.sql}</pre>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {(!schemaData.sql || schemaData.sql.length === 0) && (
                <p className="no-data">No training data available. Add some to get started!</p>
              )}
            </div>
          </div>

          {/* Update Button */}
          <div className="schema-actions">
            <button
              className="btn btn-primary"
              onClick={handleUpdateSchema}
              disabled={isLoading}
            >
              Save Changes
            </button>
          </div>
        </div>
      )}

      {/* No Database Selected */}
      {!selectedDatabase && !isLoading && (
        <div className="no-selection">
          <p>Please select a database to view and edit its training data.</p>
        </div>
      )}
    </div>
  );
};

export default TrainingDataEditor;