import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ordersAPI } from '../api/axios';
import '../styles/Components.css';

function ServiceCard({ service }) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const handleBooking = async () => {
    if (!isAuthenticated) {
      navigate('/signin');
      return;
    }
    try {
      await ordersAPI.create(service.id, { titre: service.titre });
      alert(`✅ Commande passée pour : ${service.titre}`);
    } catch (err) {
      alert(err.response?.data?.message || 'Erreur lors de la commande.');
    }
  };

  const rating  = service.rating  ?? 0;
  const reviews = service.reviews_count ?? 0;

  return (
    <div className="service-card">
      <div className="service-image">
        <div className="image-placeholder">{service.image || '📋'}</div>
        {rating >= 4.7 && <div className="badge-featured">⭐ Top</div>}
      </div>

      <div className="service-content">
        <h3 className="service-title">{service.titre}</h3>
        <p className="service-provider">👤 {service.provider_name}</p>
        <p className="service-description">{service.description}</p>

        <div className="service-rating">
          <span className="stars">⭐ {rating}</span>
          <span className="reviews">({reviews} avis)</span>
        </div>

        <div className="service-footer">
          <div className="service-price">
            <span className="price-value">{service.prix} TND</span>
            <span className="price-label">par service</span>
          </div>
          <button className="btn-book" onClick={handleBooking}>
            Réserver →
          </button>
        </div>
      </div>
    </div>
  );
}

export default ServiceCard;
