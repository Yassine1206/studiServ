import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]               = useState(null);   // { id, email, first_name, last_name }
  const [role, setRole]               = useState(null);   // 'consumer' | 'provider' | 'admin'
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading]         = useState(true);   // vrai pendant la vérification initiale

  // ── Restaurer la session depuis localStorage ──────────────────
  useEffect(() => {
    const token    = localStorage.getItem('token');
    const savedRole = localStorage.getItem('userRole');
    const savedUser = localStorage.getItem('userData');

    if (token && savedRole) {
      setIsAuthenticated(true);
      setRole(savedRole);
      if (savedUser) setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  // ── login : appelé après signup ou signin réussi ──────────────
  const login = useCallback((token, role, userData = null) => {
    localStorage.setItem('token', token);
    localStorage.setItem('userRole', role);
    if (userData) localStorage.setItem('userData', JSON.stringify(userData));
    setIsAuthenticated(true);
    setRole(role);
    setUser(userData);
  }, []);

  // ── logout ────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout/');
    } catch (_) {
      // silencieux si le serveur est down
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userData');
      setIsAuthenticated(false);
      setRole(null);
      setUser(null);
    }
  }, []);

  // ── refreshUser : recharge le profil depuis l'API ─────────────
  const refreshUser = useCallback(async () => {
    try {
      const res = await apiClient.get('/auth/profile/');
      setUser(res.data);
      localStorage.setItem('userData', JSON.stringify(res.data));
    } catch (_) {}
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, role, isAuthenticated, loading, login, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth doit être utilisé dans un <AuthProvider>');
  return ctx;
}
