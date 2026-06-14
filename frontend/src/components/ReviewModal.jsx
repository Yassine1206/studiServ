// frontend/src/components/ReviewModal.jsx
// Modal pour laisser un avis (1-5 étoiles + commentaire) après une commande terminée

import { useState } from 'react';
import { reviewsAPI } from '../api/axios';

export default function ReviewModal({ order, onClose, onSuccess }) {
  const [rating, setRating]       = useState(0);
  const [hoverRating, setHover]   = useState(0);
  const [comment, setComment]     = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]         = useState('');

  const serviceId = order?.service_id || order?.service || order?.id;
  const serviceTitle = order?.service_titre || order?.titre || 'ce service';

  const handleSubmit = async () => {
    if (rating === 0) {
      setError('Sélectionne une note avant de valider.');
      return;
    }
    setSubmitting(true);
    setError('');

    try {
      await reviewsAPI.leaveReview(serviceId, rating, comment.trim());
      onSuccess?.();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.error || 'Impossible d\'enregistrer ton avis pour le moment.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const labels = ['', 'Décevant', 'Moyen', 'Correct', 'Très bien', 'Excellent'];
  const displayed = hoverRating || rating;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={e => e.stopPropagation()}>

        <div style={styles.header}>
          <h3 style={styles.title}>Laisser un avis</h3>
          <button style={styles.closeBtn} onClick={onClose} aria-label="Fermer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <p style={styles.subtitle}>
          Comment s'est passée ta prestation pour <strong>{serviceTitle}</strong> ?
        </p>

        {/* Étoiles */}
        <div style={styles.starsRow}>
          {[1, 2, 3, 4, 5].map(star => (
            <button
              key={star}
              type="button"
              style={styles.starBtn}
              onClick={() => setRating(star)}
              onMouseEnter={() => setHover(star)}
              onMouseLeave={() => setHover(0)}
              aria-label={`${star} étoile${star > 1 ? 's' : ''}`}
            >
              <svg width="36" height="36" viewBox="0 0 24 24"
                   fill={star <= displayed ? '#FBBF24' : 'none'}
                   stroke={star <= displayed ? '#FBBF24' : '#CBD5E1'}
                   strokeWidth="1.5">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </button>
          ))}
        </div>

        {/* Label sous les étoiles */}
        <div style={styles.ratingLabel}>
          {displayed > 0 ? labels[displayed] : 'Choisis une note'}
        </div>

        {/* Commentaire */}
        <textarea
          style={styles.textarea}
          placeholder="Décris ton expérience (optionnel)..."
          value={comment}
          onChange={e => setComment(e.target.value)}
          rows={4}
        />

        {error && <div style={styles.error}>{error}</div>}

        {/* Actions */}
        <div style={styles.actions}>
          <button style={styles.cancelBtn} onClick={onClose} disabled={submitting}>
            Annuler
          </button>
          <button
            style={{ ...styles.submitBtn, opacity: rating === 0 || submitting ? 0.6 : 1 }}
            onClick={handleSubmit}
            disabled={rating === 0 || submitting}
          >
            {submitting ? 'Envoi...' : 'Publier l\'avis'}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed', inset: 0,
    background: 'rgba(15, 23, 42, 0.45)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 9999, padding: '1rem',
  },
  modal: {
    background: '#fff', borderRadius: 18,
    padding: '24px', width: '100%', maxWidth: 380,
    boxShadow: '0 24px 60px rgba(0,0,0,0.2)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    fontSize: 17, fontWeight: 700, color: '#1e293b', margin: 0,
  },
  closeBtn: {
    background: 'none', border: 'none', cursor: 'pointer',
    color: '#94a3b8', padding: 4, display: 'flex',
  },
  subtitle: {
    fontSize: 13, color: '#64748b', marginTop: 4, marginBottom: 18, lineHeight: 1.5,
  },
  starsRow: {
    display: 'flex', justifyContent: 'center', gap: 6, marginBottom: 6,
  },
  starBtn: {
    background: 'none', border: 'none', cursor: 'pointer',
    padding: 2, transition: 'transform 0.1s',
  },
  ratingLabel: {
    textAlign: 'center', fontSize: 13, fontWeight: 600,
    color: '#6C63FF', marginBottom: 16, minHeight: 18,
  },
  textarea: {
    width: '100%', border: '1.5px solid #e2e8f0',
    borderRadius: 12, padding: '10px 12px',
    fontSize: 14, resize: 'vertical', fontFamily: 'inherit',
    outline: 'none', boxSizing: 'border-box', minHeight: 80,
  },
  error: {
    marginTop: 10, fontSize: 12.5, color: '#dc2626',
    background: '#fef2f2', padding: '8px 10px', borderRadius: 8,
  },
  actions: {
    display: 'flex', gap: 8, marginTop: 18,
  },
  cancelBtn: {
    flex: 1, padding: '10px', border: '1px solid #e2e8f0',
    borderRadius: 10, background: '#fff', cursor: 'pointer',
    fontSize: 14, fontWeight: 500, color: '#475569',
  },
  submitBtn: {
    flex: 1, padding: '10px', border: 'none',
    borderRadius: 10, background: '#6C63FF', color: '#fff',
    cursor: 'pointer', fontSize: 14, fontWeight: 600,
    transition: 'opacity 0.2s',
  },
};
