import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages auth
import SignIn from './pages/auth/SignIn';
import SignUp from './pages/auth/SignUp';
import ForgotPassword from './pages/auth/ForgotPassword';

// Page d'accueil
import Home from './pages/Home';

// Dashboards
import ConsumerDashboard  from './pages/dashbords/ConsumerDashboard';
import ProviderDashboard  from './pages/dashbords/ProviderDashboard';
import AdminDashboard     from './pages/dashbords/AdminDashboard';

// Profils
import ConsumerProfile  from './pages/profiles/ConsumerProfile';
import ProviderProfile  from './pages/profiles/ProviderProfile';
import AdminProfile     from './pages/profiles/AdminProfile';
import ProviderPublicProfile from './pages/ProviderPublicProfile';
import ChatbotWidget from './components/ChatbotWidget'
// Page 404
import NotFound from './pages/NotFound';

// ── Route protégée ────────────────────────────────────────────────────────
function PrivateRoute({ requiredRole, children }) {
  const { isAuthenticated, role, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p>Chargement...</p>
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/signin" replace />;
  if (requiredRole && role !== requiredRole) return <Navigate to="/" replace />;
  return children;
}

// ── Route publique (redirige si déjà connecté) ──────────────────────────────
function PublicRoute({ children }) {
  const { isAuthenticated, role, loading } = useAuth();

  if (loading) return null;

  if (isAuthenticated) {
    const redirects = {
      consumer: '/consumer/dashboard',
      provider: '/provider/dashboard',
      admin: '/admin/dashboard',
    };
    return <Navigate to={redirects[role] || '/'} replace />;
  }

  return children;
}

// ── Routes de l'application ───────────────────────────────────────────────
function AppRoutes() {
  return (
    <>
    <Routes>
      {/* Public */}
      <Route path="/" element={<Home />} />
      <Route path="/providers/:id" element={<ProviderPublicProfile />} />

      <Route path="/signin" element={
        <PublicRoute><SignIn /></PublicRoute>
      } />
      <Route path="/signup" element={
        <PublicRoute><SignUp /></PublicRoute>
      } />
      <Route path="/forgot-password" element={
        <PublicRoute><ForgotPassword /></PublicRoute>
      } />

      {/* Consommateur */}
      <Route path="/consumer/dashboard" element={
        <PrivateRoute requiredRole="consumer"><ConsumerDashboard /></PrivateRoute>
      } />
      <Route path="/consumer/profile" element={
        <PrivateRoute requiredRole="consumer"><ConsumerProfile /></PrivateRoute>
      } />

      {/* Prestataire */}
      <Route path="/provider/dashboard" element={
        <PrivateRoute requiredRole="provider"><ProviderDashboard /></PrivateRoute>
      } />
      <Route path="/provider/profile" element={
        <PrivateRoute requiredRole="provider"><ProviderProfile /></PrivateRoute>
      } />

      {/* Admin */}
      <Route path="/admin/dashboard" element={
        <PrivateRoute requiredRole="admin"><AdminDashboard /></PrivateRoute>
      } />
      <Route path="/admin/profile" element={
        <PrivateRoute requiredRole="admin"><AdminProfile /></PrivateRoute>
      } />

      {/* 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
    <ChatbotWidget />
    </>
    
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
