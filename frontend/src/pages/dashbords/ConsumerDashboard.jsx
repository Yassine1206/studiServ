import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import apiClient, { consumersAPI, reviewsAPI } from '../../api/axios';
import Sidebar from '../../components/Sidebar';
import DashboardStats from '../../components/DashboardStats';
import ServiceCard from '../../components/ServiceCard';
import '../../styles/Dashboard.css';
import Messaging from '../../components/Messaging';
import ReviewModal from '../../components/ReviewModal';
import PaymentModal from '../../components/PaymentModal';

function ConsumerDashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  
  const activeTab = searchParams.get('tab') || 'overview';
  const setActiveTab = (tab) => setSearchParams({ tab });

  const [orders, setOrders]                 = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [reviews, setReviews]               = useState([]);
  const [loading, setLoading]               = useState(true);
  const [reviewOrder, setReviewOrder]       = useState(null);
  const [paymentOrder, setPaymentOrder]     = useState(null);
  useEffect(() => { fetchDashboardData(); }, []);

  const fetchDashboardData = async () => {
    try {
     const [ordersRes, recsRes, reviewsRes] = await Promise.all([
       consumersAPI.getOrders(),
       reviewsAPI.getSmartRecommendations(),
       consumersAPI.getRecommendations().catch(() => ({ data: [] })),
     ]);
     setOrders(ordersRes.data);
     setRecommendations(recsRes.data.recommendations);
     setReviews(reviewsRes.data || []);
    } catch {
      setOrders(getMockOrders());
      setRecommendations(getMockRecommendations());
    } finally {
      setLoading(false);
    }
  };

  const handleContactProvider = async (order) => {
    const recipientId = order.provider_user_id;
    if (!recipientId) {
      alert("Identifiant du prestataire indisponible.");
      return;
    }
    try {
      await apiClient.post('/messaging/conversations/create/', { recipient_id: recipientId });
    } catch (e) {
      // Conversation existe peut-être déjà — pas grave, on passe à l'onglet
    }
    setActiveTab('messages');
  };

  const getMockOrders = () => [
    { id: 1, titre: 'Cours de Mathématiques', provider_name: 'Ahmed Ben Ali', statut: 'completed', date_creation: '2024-05-08', service_titre: 'Cours de Maths' },
    { id: 2, titre: 'Design Graphique',        provider_name: 'Leila Hamzi',   statut: 'in_progress', date_creation: '2024-05-07', service_titre: 'Design Logo' },
    { id: 3, titre: 'Traduction Anglais',      provider_name: 'Mohamed Zain',  statut: 'pending', date_creation: '2024-05-06', service_titre: 'Traduction CV' },
  ];

  const getMockRecommendations = () => [
    { id: 10, titre: 'Développement Web React', provider_name: 'Sofia Bouaziz', categorie: 'development', prix: 50, rating: 4.9, reviews_count: 15, image: '💻', description: 'Sites web modernes et performants' },
    { id: 11, titre: 'Montage Vidéo TikTok',    provider_name: 'Karim Mansour', categorie: 'video',       prix: 35, rating: 4.8, reviews_count: 12, image: '🎬', description: 'Montage vidéo pour réseaux sociaux' },
  ];

  const statusLabel = { completed: 'Terminée', in_progress: 'En cours', pending: 'En attente', cancelled: 'Annulée' };

  return (
    <div className="dashboard">
      <Sidebar role="consumer" />

      <div className="dashboard-content">
        <div className="dashboard-header">
          <div>
            <h1>Tableau de bord</h1>
            <p>Bienvenue, {user?.first_name || 'utilisateur'} ! Retrouvez vos commandes et services.</p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/')}>
            🔍 Rechercher un service
          </button>
        </div>

        <div className="tab-nav">
          {[
            { key: 'overview',         label: 'Aperçu' },
            { key: 'orders',           label: `Commandes (${orders.length})` },
            { key: 'recommendations',  label: 'Recommandations' },
            { key: 'reviews',          label: 'Mes avis' },
            { key: 'messages',         label: 'Messages' },
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
            {activeTab === 'overview' && (
              <div>
                <DashboardStats stats={[
                  { label: 'Commandes totales', value: orders.length, icon: '📦' },
                  { label: 'En cours', value: orders.filter(o => o.statut === 'in_progress').length, icon: '⏳' },
                  { label: 'Terminées', value: orders.filter(o => o.statut === 'completed').length, icon: '✅' },
                  { label: 'En attente', value: orders.filter(o => o.statut === 'pending').length, icon: '🕐' },
                ]} />

                <h2 style={{ marginBottom: '1rem' }}>Commandes récentes</h2>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Service</th><th>Prestataire</th><th>Statut</th><th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.slice(0, 5).map(o => (
                      <tr key={o.id}>
                        <td>{o.service_titre || o.titre}</td>
                        <td>{o.provider_name || '—'}</td>
                        <td>
                          <span className={`status-badge ${o.statut}`}>
                            {statusLabel[o.statut] || o.statut}
                          </span>
                        </td>
                        <td>{o.date_creation?.slice(0, 10)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <h2 style={{ margin: '2rem 0 1rem' }}>Recommandé pour vous</h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(250px,1fr))', gap: '1rem' }}>
                  {recommendations.slice(0, 4).map(s => (
                    <ServiceCard key={s.id} service={s} />
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'orders' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Toutes mes commandes</h2>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Service</th><th>Prestataire</th><th>Statut</th><th>Date</th><th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map(o => (
                      <tr key={o.id}>
                        <td>{o.service_titre || o.titre}</td>
                        <td>{o.provider_name || '—'}</td>
                        <td>
                          <span className={`status-badge ${o.statut}`}>
                            {statusLabel[o.statut] || o.statut}
                          </span>
                        </td>
                        <td>{o.date_creation?.slice(0, 10)}</td>
                        <td>
                          {o.statut === 'pending' && (
                            <button
                              className="btn-sm"
                              style={{ background:'#6C63FF', color:'#fff', border:'none', padding:'0.4rem 0.8rem', borderRadius:'6px', cursor:'pointer' }}
                              onClick={() => setPaymentOrder(o)}
                            >
                              💳 Payer
                            </button>
                          )}
                          {o.statut === 'completed' && (
                            <button className="btn-sm" onClick={() => setReviewOrder(o)}>
                              ⭐ Laisser un avis
                            </button>
                          )}
                          <button
                            className="btn-sm"
                            style={{ background:'#0ea5e9', color:'#fff', border:'none', padding:'0.4rem 0.8rem', borderRadius:'6px', cursor:'pointer', marginLeft:'0.4rem' }}
                            onClick={() => handleContactProvider(o)}
                          >
                            💬 Contacter
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {reviewOrder && (
                  <ReviewModal
                    order={reviewOrder}
                    onClose={() => setReviewOrder(null)}
                    onSuccess={() => {
                      alert('Merci pour ton avis !');
                      fetchDashboardData();
                    }}
                  />
                )}
                {paymentOrder && (
                  <PaymentModal
                    order={{ ...paymentOrder, montant: paymentOrder.prix || paymentOrder.service?.prix }}
                    onPaid={() => {
                      alert('Paiement réussi !');
                      setPaymentOrder(null);
                      fetchDashboardData();
                    }}
                    onClose={() => setPaymentOrder(null)}
                  />
                )}
              </div>
            )}

            {activeTab === 'recommendations' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Services recommandés</h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(250px,1fr))', gap: '1rem' }}>
                  {recommendations.map(s => <ServiceCard key={s.id} service={s} />)}
                </div>
              </div>
            )}

            {activeTab === 'reviews' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Mes avis laissés</h2>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Service</th><th>Score</th><th>Commentaire</th><th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reviews.map(r => (
                      <tr key={r.id}>
                        <td>{r.service_titre}</td>
                        <td>⭐ {r.score}/5</td>
                        <td>{r.commentaire || '—'}</td>
                        <td>{r.date_creation?.slice(0, 10)}</td>
                      </tr>
                    ))}
                    {reviews.length === 0 && (
                      <tr>
                        <td colSpan={4} style={{ textAlign: 'center', color: '#94a3b8' }}>
                          Tu n'as pas encore laissé d'avis.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'messages' && (
              <Messaging currentUserId={user?.id} />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ConsumerDashboard;
