import React from 'react';
import { Outlet } from 'react-router-dom';

const AuthLayout = () => {
  return (
    <>
      <div className="background-animation"></div>
      <div className="glass-container" id="authContainer">
        <header>
          <h1>Data Cleaner <span>Auth</span></h1>
          <p>Please login or register to continue</p>
        </header>
        <main>
          <Outlet />
        </main>
      </div>
    </>
  );
};

export default AuthLayout;
