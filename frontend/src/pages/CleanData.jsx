import React, { useState, useRef } from 'react';
import { UploadCloud } from 'lucide-react';

const API_BASE = "http://localhost:8000";

const CleanData = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null); // { jobId, preview }
  const fileInputRef = useRef(null);
  
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError('');
      setResult(null);
      setLogs([]);
    }
  };

  const handleProcess = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setLogs([]);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await response.json();
      const jobId = data.job_id;

      // Start SSE
      const evtSource = new EventSource(`${API_BASE}/stream/${jobId}?token=${token}`);
      
      evtSource.onmessage = async (e) => {
        const eventData = JSON.parse(e.data);
        if (eventData.event === 'progress') {
          setLogs(prev => [...prev, eventData.data]);
        } else if (eventData.event === 'done') {
          evtSource.close();
          await fetchResults(jobId);
        } else if (eventData.event === 'error') {
          evtSource.close();
          throw new Error(eventData.data);
        }
      };

      evtSource.onerror = () => {
        evtSource.close();
        throw new Error("Connection to progress stream lost.");
      };

    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const fetchResults = async (jobId) => {
    try {
      const response = await fetch(`${API_BASE}/api/jobs/${jobId}/preview`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error("Failed to load preview.");
      const data = await response.json();
      setResult({ jobId, preview: data.preview });
    } catch(err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetPage = () => {
    setFile(null);
    setResult(null);
    setLogs([]);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h2>Clean Data</h2>
        <p>Upload an Excel or CSV file to sanitize and predict missing columns.</p>
      </div>

      {error && <div className="error-area"><p>{error}</p></div>}

      {!result && !loading && (
        <>
          <div 
            className="upload-area" 
            style={{ 
              border: '2px dashed rgba(255, 255, 255, 0.4)', 
              borderRadius: '10px', 
              padding: '40px', 
              textAlign: 'center', 
              background: 'rgba(255, 255, 255, 0.1)',
              marginBottom: '20px'
            }}
          >
            <UploadCloud size={48} style={{ margin: '0 auto', opacity: 0.8 }} />
            <p>Drag and drop your Excel or CSV file here</p>
            <p className="or-text">or</p>
            <label style={{ display: 'inline-block', padding: '10px 20px', background: '#007bff', color: 'white', borderRadius: '5px', cursor: 'pointer' }}>
              Browse File
              <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".csv, .xlsx, .xls" style={{ display: 'none' }} />
            </label>
            {file && <p style={{ marginTop: '15px', fontWeight: 'bold' }}>Selected: {file.name}</p>}
          </div>

          <button onClick={handleProcess} disabled={!file} className="primary-btn" style={{ opacity: file ? 1 : 0.5 }}>
            Clean Data
          </button>
        </>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner" style={{ margin: '0 auto 20px' }}></div>
          <p>Processing data using Hybrid Model...</p>
          <div style={{ marginTop: '20px', textAlign: 'left', background: 'rgba(0,0,0,0.05)', padding: '15px', borderRadius: '5px' }}>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {logs.map((log, i) => <li key={i}>{log}</li>)}
            </ul>
          </div>
        </div>
      )}

      {result && (
        <div>
          <h3 style={{ color: '#28a745' }}>Success!</h3>
          <p>Your dataset has been successfully processed.</p>
          
          <div className="table-container" style={{ maxHeight: '400px', overflow: 'auto', marginBottom: '20px', background: 'rgba(255,255,255,0.8)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', color: '#333' }}>
              <thead>
                <tr style={{ background: '#f8f9fa' }}>
                  {result.preview.length > 0 && Object.keys(result.preview[0]).map(col => (
                    <th key={col} style={{ padding: '8px', border: '1px solid #ddd' }}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.preview.map((row, i) => (
                  <tr key={i}>
                    {Object.keys(row).map(col => <td key={col} style={{ padding: '8px', border: '1px solid #ddd', whiteSpace: 'nowrap' }}>{row[col]}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', gap: '15px' }}>
            <a 
              href={`${API_BASE}/api/jobs/${result.jobId}/download?token=${localStorage.getItem('token')}`} 
              className="primary-btn" 
              style={{ padding: '10px 20px', textDecoration: 'none', textAlign: 'center' }}
            >
              Download Cleaned File
            </a>
            <button onClick={resetPage} className="secondary-btn">Process Another</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CleanData;
