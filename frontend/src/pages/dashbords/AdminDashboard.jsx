import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { adminAPI, reviewsAPI } from '../../api/axios';
import Sidebar from '../../components/Sidebar';
import DashboardStats from '../../components/DashboardStats';
import Messaging from '../../components/Messaging';
import '../../styles/Dashboard.css';

function AdminDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab]     = useState('overview');
  const [users, setUsers]             = useState([]);
  const [stats, setStats]             = useState({});
  const [topProviders, setTopProviders] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [actionMsg, setActionMsg]     = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [usersRes, statsRes, topRes] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getStatistics(),
        reviewsAPI.getTopProviders().catch(() => ({ data: [] })),
      ]);
      setUsers(usersRes.data);
      setStats(statsRes.data);
      setTopProviders(topRes.data || []);
    } catch {
      setUsers(getMockUsers());
      setStats(getMockStats());
      setTopProviders(getMockTopProviders());
    } finally {
      setLoading(false);
    }
  };

  const getMockUsers = () => [
    { id: 1, name: 'Ahmed Ben Ali', email: 'ahmed@uni.tn', role: 'prestataire',  status: 'actif', joined: '2024-01-15', card_status: 'verified' },
    { id: 2, name: 'Leila Hamzi',   email: 'leila@uni.tn', role: 'prestataire',  status: 'actif', joined: '2024-02-20', card_status: 'pending' },
    { id: 3, name: 'Jean Dupont',   email: 'jean@uni.tn',  role: 'consommateur', status: 'actif', joined: '2024-03-10', card_status: 'n/a' },
  ];

  const getMockStats = () => ({
    totalUsers: 245, totalProviders: 87, totalConsumers: 158,
    totalServices: 342, totalOrders: 1250,
  });

  const getMockTopProviders = () => [
    { prestataire_id: 1, nom: 'Mariem Bha',  note_moyenne: 4.8, score_global: 4.7, nb_avis: 14, badge_confiance: true,  nb_services: 3 },
    { prestataire_id: 2, nom: 'Rayen Hammi', note_moyenne: 4.3, score_global: 4.0, nb_avis: 6,  badge_confiance: false, nb_services: 2 },
  ];

  const handleAction = async (action, userId) => {
    try {
      if (action === 'suspend')  await adminAPI.suspendUser(userId);
      if (action === 'activate') await adminAPI.activateUser(userId);
      if (action === 'verify')   await adminAPI.verifyStudentCard(userId, true);
      if (action === 'reject')   await adminAPI.verifyStudentCard(userId, false);
      setActionMsg('Action effectuée avec succès.');
      setTimeout(() => setActionMsg(''), 3000);
      fetchData();
    } catch {
      setActionMsg("Erreur lors de l'action.");
      setTimeout(() => setActionMsg(''), 3000);
    }
  };

  const pendingCards = users.filter(u => u.card_status === 'pending');

  return (
    <div className="dashboard">
      <Sidebar role="admin" />

      <div className="dashboard-content">
        <div className="dashboard-header">
          <div>
            <h1>Administration</h1>
            <p>Bienvenue, {user?.first_name || 'Admin'}. Gérez la plateforme StudiServ.</p>
          </div>
        </div>

        {actionMsg && (
          <div style={{
            background: '#d1fae5', color: '#065f46',
            padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem',
            fontSize: 14,
          }}>
            {actionMsg}
          </div>
        )}

        {/* Onglets */}
        <div className="tab-nav">
          {[
            { key: 'overview',      label: 'Aperçu' },
            { key: 'users',         label: `Utilisateurs (${users.length})` },
            { key: 'verifications', label: `Vérifications (${pendingCards.length})` },
            { key: 'reputation',    label: 'Réputation' },
            { key: 'messages',      label: 'Messages' },
          ].map(({ key, label }) => (
            <button
              key={key}
              className={`tab-btn ${activeTab === key ? 'active' : ''}`}
              onClick={() => setActiveTab(key)}
            >
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loading-state">Chargement...</div>
        ) : (
          <>
            {/* ── APERÇU ── */}
            {activeTab === 'overview' && (
              <div>
                <DashboardStats stats={[
                  { label: 'Utilisateurs totaux', value: stats.totalUsers || 0,     icon: '👥' },
                  { label: 'Prestataires',        value: stats.totalProviders || 0, icon: '🎓' },
                  { label: 'Consommateurs',       value: stats.totalConsumers || 0, icon: '🛒' },
                  { label: 'Services actifs',     value: stats.totalServices || 0,  icon: '📦' },
                  { label: 'Commandes totales',   value: stats.totalOrders || 0,    icon: '🧾' },
                ]} />

                <h2 style={{ margin: '2rem 0 1rem' }}>Top prestataires</h2>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Prestataire</th><th>Note moyenne</th><th>Score</th><th>Avis</th><th>Services</th><th>Badge</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topProviders.slice(0, 5).map(p => (
                      <tr key={p.prestataire_id}>
                        <td>{p.nom}</td>
                        <td>⭐ {p.note_moyenne?.toFixed(1) ?? '—'}</td>
                        <td>{p.score_global?.toFixed(1) ?? '—'}/5</td>
                        <td>{p.nb_avis}</td>
                        <td>{p.nb_services}</td>
                        <td>
                          {p.badge_confiance ? (
                            <span className="status-badge completed">✓ Confiance</span>
                          ) : '—'}
                        </td>
                      </tr>
                    ))}
                    {topProviders.length === 0 && (
                      <tr><td colSpan={6} style={{ textAlign: 'center', color: '#94a3b8' }}>
                        Aucune donnée de réputation pour le moment.
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* ── UTILISATEURS ── */}
            {activeTab === 'users' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Gestion des utilisateurs</h2>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Nom</th><th>Email</th><th>Rôle</th><th>Statut</th><th>Carte étudiante</th><th>Inscrit le</th><th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id}>
                        <td>{u.name}</td>
                        <td>{u.email}</td>
                        <td>{u.role}</td>
                        <td>
                          <span className={`status-badge ${u.status === 'actif' ? 'completed' : 'cancelled'}`}>
                            {u.status === 'actif' ? 'Actif' : 'Suspendu'}
                          </span>
                        </td>
                        <td>
                          {u.card_status === 'verified' && <span className="status-badge completed">Vérifiée</span>}
                          {u.card_status === 'pending'  && <span className="status-badge pending">En attente</span>}
                          {u.card_status === 'n/a'       && '—'}
                        </td>
                        <td>{u.joined?.slice(0, 10)}</td>
                        <td>
                          {u.status === 'actif' ? (
                            <button className="btn-action" onClick={() => handleAction('suspend', u.id)}>
                              Suspendre
                            </button>
                          ) : (
                            <button className="btn-action approve" onClick={() => handleAction('activate', u.id)}>
                              Activer
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr><td colSpan={7} style={{ textAlign: 'center', color: '#94a3b8' }}>
                        Aucun utilisateur trouvé.
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* ── VÉRIFICATIONS CARTES ÉTUDIANTES ── */}
            {activeTab === 'verifications' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Cartes étudiantes en attente</h2>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Nom</th><th>Email</th><th>Inscrit le</th><th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingCards.map(u => (
                      <tr key={u.id}>
                        <td>{u.name}</td>
                        <td>{u.email}</td>
                        <td>{u.joined?.slice(0, 10)}</td>
                        <td style={{ display: 'flex', gap: 8 }}>
                          <button className="btn-action approve" onClick={() => handleAction('verify', u.id)}>
                            ✓ Approuver
                          </button>
                          <button className="btn-action" onClick={() => handleAction('reject', u.id)}>
                            ✕ Refuser
                          </button>
                        </td>
                      </tr>
                    ))}
                    {pendingCards.length === 0 && (
                      <tr><td colSpan={4} style={{ textAlign: 'center', color: '#94a3b8' }}>
                        Aucune carte en attente de validation.
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* ── RÉPUTATION ── */}
            {activeTab === 'reputation' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Classement des prestataires</h2>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th><th>Prestataire</th><th>Note moyenne</th><th>Taux complétion</th><th>Score global</th><th>Avis</th><th>Badge confiance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topProviders.map((p, i) => (
                      <tr key={p.prestataire_id}>
                        <td>{i + 1}</td>
                        <td>{p.nom}</td>
                        <td>⭐ {p.note_moyenne?.toFixed(1) ?? '—'}</td>
                        <td>{p.taux_completion != null ? `${Math.round(p.taux_completion * 100)}%` : '—'}</td>
                        <td>{p.score_global?.toFixed(1) ?? '—'}/5</td>
                        <td>{p.nb_avis}</td>
                        <td>
                          {p.badge_confiance ? (
                            <span className="status-badge completed">✓ Prestataire de confiance</span>
                          ) : (
                            <span style={{ color: '#94a3b8' }}>—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {topProviders.length === 0 && (
                      <tr><td colSpan={7} style={{ textAlign: 'center', color: '#94a3b8' }}>
                        Aucune donnée de réputation disponible. Lance <code>python manage.py init_reputation</code>.
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* ── MESSAGES ── */}
            {activeTab === 'messages' && (
              <Messaging currentUserId={user?.id} />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
