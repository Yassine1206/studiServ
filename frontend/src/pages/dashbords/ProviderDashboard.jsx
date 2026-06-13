import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { providersAPI } from '../../api/axios';
import Sidebar from '../../components/Sidebar';
import DashboardStats from '../../components/DashboardStats';
import '../../styles/Dashboard.css';
import Messaging from '../../components/Messaging';

function ProviderDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab]       = useState('overview');
  const [services, setServices]         = useState([]);
  const [orders, setOrders]             = useState([]);
  const [statistics, setStatistics]     = useState({});
  const [loading, setLoading]           = useState(true);
  const [showCreate, setShowCreate]     = useState(false);
  const [newService, setNewService]     = useState({ titre: '', description: '', categorie: '', prix: '', delai_livraison: '' });
  const [createError, setCreateError]   = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [svcRes, ordRes, statRes] = await Promise.all([
        providersAPI.getServices(),
        providersAPI.getOrders(),
        providersAPI.getStatistics(),
      ]);
      setServices(svcRes.data);
      setOrders(ordRes.data);
      setStatistics(statRes.data);
    } catch {
      setServices(getMockServices());
      setOrders(getMockOrders());
      setStatistics(getMockStats());
    } finally {
      setLoading(false);
    }
  };

  const getMockServices = () => [
    { id: 1, titre: 'Cours de Mathématiques', categorie: 'tutoring', prix: 25, actif: true, rating: 4.8, reviews_count: 12 },
    { id: 2, titre: 'Aide aux devoirs', categorie: 'tutoring', prix: 20, actif: true, rating: 4.7, reviews_count: 8 },
  ];
  const getMockOrders = () => [
    { id: 1, service_titre: 'Cours de Math', provider_name: 'Jean Dupont', statut: 'in_progress', date_creation: '2024-05-07' },
    { id: 2, service_titre: 'Aide devoirs',  provider_name: 'Marie Leblanc', statut: 'completed',  date_creation: '2024-05-06' },
  ];
  const getMockStats = () => ({ totalEarnings: 450, totalOrders: 20, completionRate: 95, reputation: 4.8, totalReviews: 24, totalServices: 2 });

  const handleCreateService = async (e) => {
    e.preventDefault();
    setCreateError('');
    try {
      await providersAPI.createService(newService);
      setShowCreate(false);
      setNewService({ titre: '', description: '', categorie: '', prix: '', delai_livraison: '' });
      fetchData();
    } catch (err) {
      setCreateError(err.response?.data?.message || 'Erreur lors de la création.');
    }
  };

  const statusLabel = { completed: 'Terminée', in_progress: 'En cours', pending: 'En attente' };

  return (
    <div className="dashboard">
      <Sidebar role="provider" />

      <div className="dashboard-content">
        <div className="dashboard-header">
          <div>
            <h1>Tableau de bord Prestataire</h1>
            <p>Bonjour {user?.first_name} ! Gérez vos services et commandes.</p>
          </div>
          <button className="btn-primary" onClick={() => setShowCreate(true)}>
            + Nouveau service
          </button>
        </div>

        {/* Modal création service */}
        {showCreate && (
          <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem' }}>
            <h3 style={{ marginTop: 0 }}>Créer un service</h3>
            {createError && <div className="error-message" style={{ background: '#fef2f2', color: '#dc2626', padding: '0.6rem', borderRadius: '6px', marginBottom: '1rem' }}>{createError}</div>}
            <form onSubmit={handleCreateService} style={{ display: 'grid', gap: '0.75rem' }}>
              <input placeholder="Titre du service" value={newService.titre} onChange={e => setNewService({...newService, titre: e.target.value})} required style={{ padding: '0.6rem', border: '1.5px solid #d1d5db', borderRadius: '8px' }} />
              <textarea placeholder="Description" value={newService.description} onChange={e => setNewService({...newService, description: e.target.value})} required rows={3} style={{ padding: '0.6rem', border: '1.5px solid #d1d5db', borderRadius: '8px' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                <input placeholder="Catégorie (ex: tutoring)" value={newService.categorie} onChange={e => setNewService({...newService, categorie: e.target.value})} required style={{ padding: '0.6rem', border: '1.5px solid #d1d5db', borderRadius: '8px' }} />
                <input type="number" placeholder="Prix (TND)" value={newService.prix} onChange={e => setNewService({...newService, prix: e.target.value})} required style={{ padding: '0.6rem', border: '1.5px solid #d1d5db', borderRadius: '8px' }} />
                <input type="number" placeholder="Délai (jours)" value={newService.delai_livraison} onChange={e => setNewService({...newService, delai_livraison: e.target.value})} required style={{ padding: '0.6rem', border: '1.5px solid #d1d5db', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.6rem 1.5rem' }}>Créer</button>
                <button type="button" onClick={() => setShowCreate(false)} style={{ padding: '0.6rem 1.5rem', background: 'white', border: '1.5px solid #d1d5db', borderRadius: '8px', cursor: 'pointer' }}>Annuler</button>
              </div>
            </form>
          </div>
        )}

        {/* Onglets */}
        <div className="tab-nav">
          {[
            { key: 'overview',    label: 'Aperçu' },
            { key: 'services',    label: `Mes services (${services.length})` },
            { key: 'orders',      label: `Commandes (${orders.length})` },
            { key: 'statistics',  label: 'Statistiques' },
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
                { label: 'Revenus totaux',   value: `${statistics.totalEarnings || 0} TND`, icon: '💰' },
                { label: 'Commandes',        value: statistics.totalOrders || 0, icon: '📦' },
                { label: 'Taux complétion',  value: `${statistics.completionRate || 0}%`, icon: '✅' },
                { label: 'Réputation',       value: `${statistics.reputation || 0}/5`, icon: '⭐' },
              ]} />
            )}

            {activeTab === 'services' && (
              <table className="data-table">
                <thead><tr><th>Service</th><th>Catégorie</th><th>Prix</th><th>Note</th><th>Statut</th></tr></thead>
                <tbody>
                  {services.map(s => (
                    <tr key={s.id}>
                      <td>{s.titre}</td>
                      <td>{s.categorie}</td>
                      <td>{s.prix} TND</td>
                      <td>⭐ {s.rating || 0}</td>
                      <td><span className={`status-badge ${s.actif ? 'active' : 'suspended'}`}>{s.actif ? 'Actif' : 'Inactif'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'orders' && (
              <table className="data-table">
                <thead><tr><th>Service</th><th>Consommateur</th><th>Statut</th><th>Date</th></tr></thead>
                <tbody>
                  {orders.map(o => (
                    <tr key={o.id}>
                      <td>{o.service_titre}</td>
                      <td>{o.provider_name}</td>
                      <td><span className={`status-badge ${o.statut}`}>{statusLabel[o.statut] || o.statut}</span></td>
                      <td>{o.date_creation?.slice(0, 10)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'statistics' && (
              <DashboardStats stats={[
                { label: 'Revenus totaux',   value: `${statistics.totalEarnings || 0} TND`, icon: '💰' },
                { label: 'Avis reçus',       value: statistics.totalReviews || 0, icon: '💬' },
                { label: 'Services actifs',  value: statistics.totalServices || 0, icon: '📋' },
                { label: 'Réputation',       value: `${statistics.reputation || 0}/5`, icon: '⭐' },
              ]} />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ProviderDashboard;
