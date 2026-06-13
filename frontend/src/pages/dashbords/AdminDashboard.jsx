import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../api/axios';
import Sidebar from '../../components/Sidebar';
import DashboardStats from '../../components/DashboardStats';
import '../../styles/Dashboard.css';
import Messaging from '../../components/Messaging';

function AdminDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab]       = useState('overview');
  const [users, setUsers]               = useState([]);
  const [stats, setStats]               = useState({});
  const [loading, setLoading]           = useState(true);
  const [actionMsg, setActionMsg]       = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [usersRes, statsRes] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getStatistics(),
      ]);
      setUsers(usersRes.data);
      setStats(statsRes.data);
    } catch {
      setUsers(getMockUsers());
      setStats(getMockStats());
    } finally {
      setLoading(false);
    }
  };

  const getMockUsers = () => [
    { id: 1, name: 'Ahmed Ben Ali', email: 'ahmed@uni.tn', role: 'prestataire', status: 'actif', joined: '2024-01-15', card_status: 'verified' },
    { id: 2, name: 'Leila Hamzi',   email: 'leila@uni.tn', role: 'prestataire', status: 'actif', joined: '2024-02-20', card_status: 'pending' },
    { id: 3, name: 'Jean Dupont',   email: 'jean@uni.tn',  role: 'consommateur', status: 'actif', joined: '2024-03-10', card_status: 'n/a' },
  ];
  const getMockStats = () => ({ totalUsers: 245, totalProviders: 87, totalConsumers: 158, totalServices: 342, totalOrders: 1250 });

  const handleAction = async (action, userId) => {
    try {
      if (action === 'suspend')  await adminAPI.suspendUser(userId);
      if (action === 'activate') await adminAPI.activateUser(userId);
      if (action === 'verify')   await adminAPI.verifyStudentCard(userId, true);
      setActionMsg('Action effectuée avec succès.');
      setTimeout(() => setActionMsg(''), 3000);
      fetchData();
    } catch {
      setActionMsg('Erreur lors de l\'action.');
    }
  };

  return (
    <div className="dashboard">
      <Sidebar role="admin" />

      <div className="dashboard-content">
        <div className="dashboard-header">
          <div>
            <h1>Administration</h1>
            <p>Bienvenue, {user?.first_name}. Gérez la plateforme StudiServ.</p>
          </div>
        </div>

        {actionMsg && (
          <div style={{ background: '#d1fae5', color: '#065f46', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem' }}>
            {actionMsg}
          </div>
        )}

        <div className="tab-nav">
          {[
            { key: 'overview',  label: 'Aperçu' },
            { key: 'users',     label: `Utilisateurs (${users.length})` },
            { key: 'verifications', label: 'Vérifications' },
          ].map(({ key, label }) => (
            <button key={key} className={`tab-btn ${activeTab === key ? 'active' : ''}`} onClick={() => setActiveTab(key)}>
              {label}
            </button>
          ))}
        </div>

        {loading ? <div className="loading-state">Chargement...</div> : (
          <>
            {activeTab === 'overview' && (
              <DashboardStats stats={[
                { label: 'Utilisateurs totaux', value: stats.totalUsers || 0, icon: '👥' },
                { label: 'Prestataires',        value: stats.totalProviders || 0, icon: '⭐' },
                { label: 'Consommateurs',       value: stats.totalConsumers || 0, icon: '👤' },
                { label: 'Services actifs',     value: stats.totalServices || 0, icon: '📦' },
                { label: 'Commandes totales',   value: stats.totalOrders || 0, icon: '📋' },
              ]} />
            )}

            {activeTab === 'users' && (
              <table className="data-table">
                <thead>
                  <tr><th>Nom</th><th>Email</th><th>Rôle</th><th>Statut</th><th>Inscrit le</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>{u.name}</td>
                      <td>{u.email}</td>
                      <td>{u.role}</td>
                      <td><span className={`status-badge ${u.status}`}>{u.status}</span></td>
                      <td>{u.joined}</td>
                      <td>
                        {u.status !== 'suspendu' ? (
                          <button className="btn-action suspend" onClick={() => handleAction('suspend', u.id)}>Suspendre</button>
                        ) : (
                          <button className="btn-action activate" onClick={() => handleAction('activate', u.id)}>Activer</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'verifications' && (
              <table className="data-table">
                <thead>
                  <tr><th>Nom</th><th>Email</th><th>Carte étudiant</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {users.filter(u => u.role === 'prestataire' || u.role === 'provider').map(u => (
                    <tr key={u.id}>
                      <td>{u.name}</td>
                      <td>{u.email}</td>
                      <td>
                        <span className={`status-badge ${u.card_status === 'verified' ? 'active' : 'pending'}`}>
                          {u.card_status === 'verified' ? '✓ Vérifiée' : u.card_status === 'pending' ? '⏳ En attente' : '—'}
                        </span>
                      </td>
                      <td>
                        {u.card_status === 'pending' && (
                          <button className="btn-action approve" onClick={() => handleAction('verify', u.id)}>
                            ✓ Approuver
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
