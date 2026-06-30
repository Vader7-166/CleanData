import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

interface MainLayoutProps {
  setToken: (token: string | null) => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ setToken }) => {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 relative">
      {/* Background ambient gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-400/20 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-400/20 blur-[120px]" />
      </div>

      {/* Sidebar wrapper */}
      <div className="z-20 shadow-2xl relative">
        <Sidebar setToken={setToken} />
      </div>
      
      <main className="flex-1 overflow-y-auto relative z-10 p-8 scroll-smooth">
        <div className="container mx-auto max-w-7xl animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
