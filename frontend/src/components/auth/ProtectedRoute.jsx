import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from '../ui';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, authReady } = useAuth();
  const location = useLocation();

  if (!authReady) return <Spinner />;
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
