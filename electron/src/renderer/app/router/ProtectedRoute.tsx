import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { isAuthenticated, getStoredUser } from '../../lib/api/auth';

interface ProtectedRouteProps {
  children: React.ReactElement;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation();
  const authed = isAuthenticated() && !!getStoredUser();

  if (!authed) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
