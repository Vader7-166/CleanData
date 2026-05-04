import React, { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Dictionary = () => {
  const [dictionaries, setDictionaries] = useState([]);
  const [stats, setStats] = useState({});
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const fetchDictionaries = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setDictionaries(data.dictionaries);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        const statsMap = {};
        data.stats.forEach(s => {
          statsMap[s.dictionary_id] = s.usage_count;
        });
        setStats(statsMap);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDictionaries();
    fetchStats();
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setUploading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setFile(null);
        // Reset file input
        document.getElementById('dict-upload').value = '';
        fetchDictionaries();
      } else {
        setError(data.detail || 'Upload failed');
      }
    } catch (err) {
      setError('An error occurred during upload.');
    } finally {
      setUploading(false);
    }
  };

  const handleActivate = async (id) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/${id}/activate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        fetchDictionaries();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this dictionary?")) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        fetchDictionaries();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h2>Dictionary Management</h2>
        <p>Manage your custom dictionaries and view usage statistics.</p>
      </div>

      {/* Upload Section */}
      <div className="upload-area" style={{ textAlign: 'center' }}>
        <h3 style={{ marginBottom: '15px' }}>Upload New Dictionary</h3>
        <p style={{ color: '#aaa', marginBottom: '15px' }}>Supported format: CSV</p>
        
        <div className="file-input-wrapper" style={{ margin: '20px 0' }}>
          <label style={{ display: 'inline-block', padding: '10px 20px', background: '#007bff', color: 'white', borderRadius: '5px', cursor: 'pointer' }}>
            Browse File
            <input 
              type="file" 
              id="dict-upload" 
              accept=".csv"
              onChange={handleFileChange}
              disabled={uploading}
              style={{ display: 'none' }}
            />
          </label>
          {file && <div className="file-name" style={{ marginTop: '10px' }}>Selected: {file.name}</div>}
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        <button 
          className="primary-btn"
          onClick={handleUpload}
          disabled={!file || uploading}
          style={{ marginTop: '15px' }}
        >
          {uploading ? 'Uploading...' : 'Upload Dictionary'}
        </button>
      </div>

      {/* List Section */}
      <div style={{ marginTop: '30px' }}>
        <h3>Available Dictionaries</h3>
        {dictionaries.length === 0 ? (
          <p style={{ marginTop: '10px', color: '#aaa' }}>No dictionaries uploaded yet.</p>
        ) : (
          <div style={{ display: 'grid', gap: '15px', marginTop: '15px' }}>
            {dictionaries.map(dict => (
              <div key={dict.id} style={{ 
                padding: '20px', 
                background: dict.is_active ? 'rgba(74, 144, 226, 0.15)' : 'rgba(255,255,255,0.05)', 
                border: dict.is_active ? '1px solid #4a90e2' : '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <h4 style={{ margin: '0 0 5px 0', color: dict.is_active ? '#4a90e2' : '#fff' }}>
                    {dict.filename} {dict.is_active && '(Active)'}
                  </h4>
                  <div style={{ fontSize: '0.9em', color: '#aaa', display: 'flex', gap: '20px' }}>
                    <span>Uploaded: {new Date(dict.created_at).toLocaleDateString()}</span>
                    <span>Used: {stats[dict.id] || 0} times</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  {!dict.is_active && (
                    <button 
                      onClick={() => handleActivate(dict.id)}
                      style={{ padding: '8px 15px', background: 'transparent', border: '1px solid #4a90e2', color: '#4a90e2', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      Activate
                    </button>
                  )}
                  <button 
                    onClick={() => handleDelete(dict.id)}
                    style={{ padding: '8px 15px', background: 'transparent', border: '1px solid #e74c3c', color: '#e74c3c', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dictionary;
