import React, { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const stored = sessionStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback((credentials) => {
    // Mock login — replace with MSAL or real auth
    const mockUser = {
      id: credentials.id || '1',
      name: credentials.username || 'Admin User',
      email: credentials.email || 'admin@company.com',
      role: credentials.role || 'Enterprise Admin',
      provider: credentials.provider || 'Direct Login',
      avatar: credentials.avatar || credentials.username?.[0]?.toUpperCase() || 'A',
    };
    sessionStorage.setItem('user', JSON.stringify(mockUser));
    sessionStorage.setItem('access_token', 'mock-jwt-token');
    setUser(mockUser);
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem('user');
    sessionStorage.removeItem('access_token');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};
