import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import { Login, Register, Profile } from '../pages';
import Dashboard from '../pages/Dashboard';
import Product from '../pages/Product';
import Inventory from '../pages/Inventory';
import StockRecord from '../pages/StockRecord';
import Order from '../pages/Order';
import Alert from '../pages/Alert';
import Permission from '../pages/Permission';

const AppRoutes = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<any>(token ? JSON.parse(localStorage.getItem('user') || '{}') : null);

  const handleLogin = (token: string, user: any) => {
    setToken(token);
    setUser(user);
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/profile"
          element={token ? (
            <MainLayout>
              <Profile user={user} />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
        <Route
          path="/"
          element={token ? (
            <MainLayout>
              <Dashboard user={user} />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
        <Route
          path="/product"
          element={token ? (
            <MainLayout>
              <Product />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
        <Route
          path="/inventory"
          element={token ? (
            <MainLayout>
              <Inventory />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
        <Route
          path="/stock-record"
          element={token ? (
            <MainLayout>
              <StockRecord />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
        <Route
          path="/order"
          element={token ? (
            <MainLayout>
              <Order />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
        <Route
          path="/alert"
          element={token ? (
            <MainLayout>
              <Alert />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
        <Route
          path="/permission"
          element={token ? (
            <MainLayout>
              <Permission />
            </MainLayout>
          ) : (
            <Navigate to="/login" />
          )}
        />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRoutes; 