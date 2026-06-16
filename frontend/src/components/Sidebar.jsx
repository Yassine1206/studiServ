import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Sidebar.css';

function Sidebar({ role }) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const menuItems = {
    consumer: [
      { icon: '📊', label: 'Tableau de bord', path: '/consumer/dashboard?tab=overview' },
      { icon: '🔍', label: 'Rechercher services', path: '/' },
      { icon: '📦', label: 'Mes commandes', path: '/consumer/dashboard?tab=orders' },
      { icon: '⭐', label: 'Mes avis', path: '/consumer/dashboard?tab=reviews' },
      { icon: '💬', label: 'Messages', path: '/consumer/dashboard?tab=messages' },
      { icon: '👤', label: 'Mon profil', path: '/consumer/profile' },
    ],
    provider: [
      { icon: '📊', label: 'Tableau de bord', path: '/provider/dashboard?tab=overview' },
      { icon: '📦', label: 'Mes services', path: '/provider/dashboard?tab=services' },
      { icon: '📋', label: 'Mes commandes', path: '/provider/dashboard?tab=orders' },
      { icon: '📈', label: 'Statistiques', path: '/provider/dashboard?tab=statistics' },
      { icon: '⭐', label: 'Mes avis', path: '/provider/dashboard?tab=reviews' },
      { icon: '💬', label: 'Messages', path: '/provider/dashboard?tab=messages' },
      { icon: '👤', label: 'Mon profil', path: '/provider/profile' },
    ],
    admin: [
      { icon: '📊', label: 'Tableau de bord', path: '/admin/dashboard?tab=overview' },
      { icon: '👥', label: 'Utilisateurs', path: '/admin/dashboard?tab=users' },
      { icon: '📦', label: 'Services', path: '/admin/dashboard?tab=overview' },
      { icon: '⚠️', label: 'Signalements', path: '/admin/dashboard?tab=overview' },
      { icon: '✓',  label: 'Vérifications', path: '/admin/dashboard?tab=verifications' },
      { icon: '📈', label: 'Statistiques', path: '/admin/dashboard?tab=reputation' },
      { icon: '👤', label: 'Mon profil', path: '/admin/profile' },
    ],
  };

  const items = menuItems[role] || [];

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">StudiServ</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {items.map((item, idx) => (
          <button
            key={idx}
            className="nav-item"
            onClick={() => navigate(item.path)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="btn-logout" onClick={handleLogout}>
          🚪 Déconnexion
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
