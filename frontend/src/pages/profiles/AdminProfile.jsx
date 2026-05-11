import { useAuth } from '../../context/AuthContext';
import Sidebar from '../../components/Sidebar';
import '../../styles/Dashboard.css';
import '../../styles/Profile.css';

function AdminProfile() {
  const { user } = useAuth();

  return (
    <div className="dashboard">
      <Sidebar role="admin" />
      <div className="dashboard-content">
        <div className="dashboard-header"><h1>Profil Administrateur</h1></div>
        <div className="profile-container">
          <div className="profile-card">
            <div className="profile-header-section">
              <div className="avatar-large">🛡️</div>
              <div className="profile-header-info">
                <h2>{user?.first_name} {user?.last_name}</h2>
                <p className="email">{user?.email}</p>
                <p style={{ color: '#6366f1', fontWeight: 600 }}>Administrateur StudiServ</p>
              </div>
            </div>
            <div className="profile-section">
              <h3>Informations du compte</h3>
              <div className="info-grid">
                <div className="info-item"><label>Rôle</label><p>Administrateur</p></div>
                <div className="info-item"><label>Email</label><p>{user?.email}</p></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminProfile;
