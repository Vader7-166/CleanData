import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

interface MainLayoutProps {
  setToken: (token: string | null) => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ setToken }) => {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar setToken={setToken} />
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto py-8 px-4">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
