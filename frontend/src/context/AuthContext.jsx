import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import {
  getCurrentSession,
  loginWithCredentials,
  logoutFromSession,
} from '../auth/session';

const AuthContext = createContext(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    let mounted = true;
    getCurrentSession()
      .then((sessionUser) => {
        if (mounted) {
          setUser({
            ...sessionUser,
            email: sessionUser.username,
            provider: 'Shared development login',
            avatar: (sessionUser.name || 'U')[0].toUpperCase(),
          });
        }
      })
      .catch((error) => {
        if (error.response?.status !== 401) {
          console.error('LicenseHub session could not be restored:', error);
          if (mounted) setAuthError('Login status could not be checked. Please try again.');
        }
      })
      .finally(() => {
        if (mounted) setAuthReady(true);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const login = useCallback(async (username, password) => {
    const sessionUser = await loginWithCredentials(username, password);
    setUser({
      ...sessionUser,
      email: sessionUser.username,
      provider: 'Shared development login',
      avatar: (sessionUser.name || 'U')[0].toUpperCase(),
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutFromSession();
    } catch (error) {
      console.error('Unable to revoke the LicenseHub session on the server:', error);
    } finally {
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      authReady,
      authError,
      isAuthenticated: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
