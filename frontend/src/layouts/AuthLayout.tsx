import React from 'react';
import { Outlet } from 'react-router-dom';

const AuthLayout = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <div className="max-w-md w-full bg-card border border-border rounded-xl shadow-lg p-8">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-2">Data Cleaner <span className="text-primary">Auth</span></h1>
          <p className="text-muted-foreground">Please login or register to continue</p>
        </header>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AuthLayout;
