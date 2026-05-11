import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Navbar.css';

function Navbar() {
  const navigate = useNavigate();
  const { isAuthenticated, role, user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const dashboardPath = {
    consumer: '/consumer/dashboard',
    provider: '/provider/dashboard',
    admin: '/admin/dashboard',
  }[role] || '/';

  const profilePath = {
    consumer: '/consumer/profile',
    provider: '/provider/profile',
    admin: '/admin/profile',
  }[role] || '/';

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand" onClick={() => navigate('/')}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">StudiServ</span>
        </div>

        <div className="navbar-center">
          <div className="search-bar">
            <input type="text" placeholder="Rechercher un service..." />
            <button>🔍</button>
          </div>
        </div>

        <div className="navbar-right">
          {isAuthenticated ? (
            <>
              <span className="nav-greeting">
                Bonjour, {user?.first_name || 'Utilisateur'}
              </span>
              <button className="nav-link" onClick={() => navigate(dashboardPath)}>
                📊 Tableau de bord
              </button>
              <button className="nav-link" onClick={() => navigate(profilePath)}>
                👤 Mon profil
              </button>
              <button className="btn-secondary" onClick={handleLogout}>
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <button className="btn-link" onClick={() => navigate('/signin')}>
                Connexion
              </button>
              <button className="btn-primary" onClick={() => navigate('/signup')}>
                S&apos;inscrire
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
