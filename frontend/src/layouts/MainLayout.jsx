import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileSpreadsheet, BookA, LogOut } from 'lucide-react';

const MainLayout = ({ setToken }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    navigate('/auth/login');
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)' }}>
      
      {/* Sidebar */}
      <aside style={{ width: '250px', background: 'rgba(255, 255, 255, 0.1)', backdropFilter: 'blur(10px)', borderRight: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', flexDirection: 'column', color: 'white' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>Data Cleaner <span style={{ color: '#4facfe' }}>Pro</span></h2>
        </div>
        
        <nav style={{ flex: 1, padding: '20px 0', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <NavLink to="/dashboard" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} style={navLinkStyle}>
            <LayoutDashboard size={20} />
            Dashboard
          </NavLink>
          <NavLink to="/clean" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} style={navLinkStyle}>
            <FileSpreadsheet size={20} />
            Clean Data
          </NavLink>
          <NavLink to="/dictionary" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} style={navLinkStyle}>
            <BookA size={20} />
            Dictionary
          </NavLink>
        </nav>
        
        <div style={{ padding: '20px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <button onClick={handleLogout} style={{ ...navLinkStyle, background: 'transparent', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', color: '#ff6b6b' }}>
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '40px', position: 'relative' }}>
        <div className="glass-container" style={{ margin: '0 auto', maxWidth: '1000px', width: '100%' }}>
          <Outlet />
        </div>
      </main>
    </div>
  );
};

const navLinkStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  padding: '12px 20px',
  color: 'white',
  textDecoration: 'none',
  fontSize: '1rem',
  transition: 'background 0.2s',
};

export default MainLayout;
