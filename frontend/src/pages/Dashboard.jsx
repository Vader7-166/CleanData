import React, { useState, useEffect } from 'react';
import { RefreshCw, Trash2, Download } from 'lucide-react';

const API_BASE = "http://localhost:8000";

const Dashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Modal states
  const [selectedJob, setSelectedJob] = useState(null);
  const [preview, setPreview] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchJobs = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/api/jobs`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) {
        if (response.status !== 401) throw new Error('Failed to fetch jobs');
      } else {
        const data = await response.json();
        setJobs(data.jobs);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const openJobDetails = async (job) => {
    setSelectedJob(job);
    setPreview([]);
    setModalOpen(true);
    
    if (job.status === 'done') {
      try {
        const response = await fetch(`${API_BASE}/api/jobs/${job.id}/preview?limit=50`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (response.ok) {
          const data = await response.json();
          setPreview(data.preview);
        }
      } catch (err) {
        // ignore preview error silently
      }
    }
  };

  const deleteJob = async (jobId) => {
    if (!window.confirm("Are you sure you want to delete this job and its file?")) return;
    try {
      const response = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error("Delete failed");
      fetchJobs();
      if (selectedJob && selectedJob.id === jobId) setModalOpen(false);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>Your Processing History</h2>
          <button onClick={fetchJobs} className="secondary-btn" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
        
        <div style={{ background: '#fff3cd', color: '#856404', padding: '10px', borderRadius: '5px', marginBottom: '15px', fontSize: '14px' }}>
          <strong>Notice:</strong> We only retain your 10 most recent files. Older files are automatically deleted.
        </div>

        {error && <div className="error-area"><p>{error}</p></div>}
        
        {loading ? <p>Loading...</p> : (
          <div className="table-container">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'rgba(0,0,0,0.05)', textAlign: 'left' }}>
                  <th style={{ padding: '12px' }}>Filename</th>
                  <th style={{ padding: '12px' }}>Status</th>
                  <th style={{ padding: '12px' }}>Size</th>
                  <th style={{ padding: '12px' }}>Duration</th>
                  <th style={{ padding: '12px' }}>Date</th>
                  <th style={{ padding: '12px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr key={job.id} style={{ borderBottom: '1px solid #ddd' }}>
                    <td style={{ padding: '12px' }}>{job.filename}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ 
                        padding: '4px 8px', borderRadius: '12px', fontSize: '12px', 
                        background: job.status==='done'?'#d4edda':job.status==='error'?'#f8d7da':'#fff3cd', 
                        color: job.status==='done'?'#155724':job.status==='error'?'#721c24':'#856404'
                      }}>
                        {job.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px' }}>{job.total_rows ? `${job.total_rows}x${job.total_columns}` : '-'}</td>
                    <td style={{ padding: '12px' }}>{job.processing_time_ms ? `${(job.processing_time_ms/1000).toFixed(1)}s` : '-'}</td>
                    <td style={{ padding: '12px' }}>{new Date(job.created_at).toLocaleString()}</td>
                    <td style={{ padding: '12px', display: 'flex', gap: '8px' }}>
                      <button className="secondary-btn" style={{ padding: '5px 10px', fontSize: '12px' }} onClick={() => openJobDetails(job)}>Info</button>
                      {job.status === 'done' && (
                        <a 
                          href={`${API_BASE}/api/jobs/${job.id}/download?token=${localStorage.getItem('token')}`} 
                          className="primary-btn" 
                          style={{ padding: '5px 10px', fontSize: '12px', textDecoration: 'none', display: 'flex', alignItems: 'center' }}
                        >
                          <Download size={14} />
                        </a>
                      )}
                      <button 
                        className="secondary-btn" 
                        style={{ padding: '5px 10px', fontSize: '12px', background: '#dc3545', color: 'white', border: 'none' }} 
                        onClick={() => deleteJob(job.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
                {jobs.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ padding: '20px', textAlign: 'center', color: '#666' }}>No jobs found. Go to Clean Data to upload a file.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalOpen && selectedJob && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.95)', borderRadius: '10px', padding: '20px', width: '90%', maxHeight: '90vh', overflowY: 'auto', backdropFilter: 'blur(10px)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3 style={{ margin: 0 }}>Details: {selectedJob.filename}</h3>
              <button className="secondary-btn" onClick={() => setModalOpen(false)}>Close</button>
            </div>
            
            <div style={{ lineHeight: 1.6, marginBottom: '20px' }}>
              <strong>Status:</strong> {selectedJob.status} <br/>
              <strong>Date:</strong> {new Date(selectedJob.created_at).toLocaleString()} <br/>
              <strong>Rows:</strong> {selectedJob.total_rows || '-'} | <strong>Columns:</strong> {selectedJob.total_columns || '-'} <br/>
              <strong>Duration:</strong> {selectedJob.processing_time_ms ? (selectedJob.processing_time_ms/1000).toFixed(1) + 's' : '-'} <br/>
              {selectedJob.error_message && <><strong style={{ color: 'red' }}>Error:</strong> {selectedJob.error_message}</>}
            </div>

            {preview.length > 0 && (
              <div className="table-container" style={{ maxHeight: '50vh', overflow: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      {Object.keys(preview[0]).map(col => <th key={col} style={{ padding: '8px', border: '1px solid #ddd' }}>{col}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.map((row, i) => (
                      <tr key={i}>
                        {Object.keys(row).map(col => <td key={col} style={{ padding: '8px', border: '1px solid #ddd', whiteSpace: 'nowrap' }}>{row[col]}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default Dashboard;
