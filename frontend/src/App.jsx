import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AuthLayout from './layouts/AuthLayout';
import MainLayout from './layouts/MainLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import CleanData from './pages/CleanData';
import Dictionary from './pages/Dictionary';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    const handleStorageChange = () => setToken(localStorage.getItem('token'));
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/auth" element={token ? <Navigate to="/" replace /> : <AuthLayout />}>
          <Route path="login" element={<Login setToken={setToken} />} />
          <Route path="register" element={<Register />} />
          <Route index element={<Navigate to="login" replace />} />
        </Route>

        <Route path="/" element={token ? <MainLayout setToken={setToken} /> : <Navigate to="/auth/login" replace />}>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="clean" element={<CleanData />} />
          <Route path="dictionary" element={<Dictionary />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
