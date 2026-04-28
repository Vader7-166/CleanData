import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Registration failed');
      }
      
      // Auto redirect to login
      navigate('/auth/login');
    } catch(err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ marginTop: '20px' }}>
      {error && <div className="error-area"><p>{error}</p></div>}
      <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <input 
          type="text" 
          placeholder="New Username" 
          required 
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <input 
          type="password" 
          placeholder="New Password" 
          required 
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <button type="submit" className="secondary-btn">Register</button>
        <p style={{ textAlign: 'center', marginTop: '10px', fontSize: '14px' }}>
          Already have an account? <Link to="/auth/login" style={{ color: '#007bff', textDecoration: 'none' }}>Login</Link>
        </p>
      </form>
    </div>
  );
};

export default Register;
