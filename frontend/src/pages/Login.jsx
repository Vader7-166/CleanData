import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Login = ({ setToken }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const formParams = new URLSearchParams();
      formParams.append('username', username);
      formParams.append('password', password);
      
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formParams
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Authentication failed');
      }
      
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      navigate('/');
    } catch(err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ marginTop: '20px' }}>
      {error && <div className="error-area"><p>{error}</p></div>}
      <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <input 
          type="text" 
          placeholder="Username" 
          required 
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <input 
          type="password" 
          placeholder="Password" 
          required 
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <button type="submit" className="primary-btn">Login</button>
        <p style={{ textAlign: 'center', marginTop: '10px', fontSize: '14px' }}>
          Don't have an account? <Link to="/auth/register" style={{ color: '#007bff', textDecoration: 'none' }}>Register</Link>
        </p>
      </form>
    </div>
  );
};

export default Login;
