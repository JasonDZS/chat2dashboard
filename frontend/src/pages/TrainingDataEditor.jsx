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
                  <h3>{tableName}</h3>
                  <pre className="sql-code">{createSql}</pre>
                </div>
              ))}
            </div>
          </div>

          {/* SQL Training Data */}
          <div className="schema-section">
            <div className="section-header">
              <h2>SQL Training Data ({(schemaData.sql || []).length})</h2>
              <button
                className="btn btn-primary"
                onClick={() => setIsAddingNew(!isAddingNew)}
                disabled={isLoading}
              >
                {isAddingNew ? 'Cancel' : 'Add New'}
              </button>
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
                    <button
                      className="btn btn-danger btn-small"
                      onClick={() => handleDeleteSqlTraining(index)}
                      disabled={isLoading}
                    >
                      Delete
                    </button>
                  </div>
                  <div className="training-content">
                    <div className="question">
                      <label>Question:</label>
                      <p>{item.question}</p>
                    </div>
                    <div className="sql">
                      <label>SQL:</label>
                      <pre className="sql-code">{item.sql}</pre>
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