import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/axios';

function Star({ filled }) {
  return <span style={{ color: filled ? '#fbbf24' : '#e5e7eb', fontSize: '1.3rem' }}>★</span>;
}

export default function ProviderPublicProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiClient.get(`/providers/${id}/`)
      .then(res => setData(res.data))
      .catch(() => setError('Profil introuvable.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: '3rem', textAlign: 'center' }}>Chargement…</div>;
  if (error)   return <div style={{ padding: '3rem', textAlign: 'center', color: '#dc2626' }}>{error}</div>;
  if (!data)   return null;

  const note = data.reputation?.note_moyenne || 0;
  const filledStars = Math.round(note);

  return (
    <div style={{ maxWidth: '900px', margin: '2rem auto', padding: '1rem' }}>
      <button
        onClick={() => navigate(-1)}
        style={{ background:'none', border:'none', color:'#6C63FF', cursor:'pointer', fontSize:'0.9rem', marginBottom:'1rem' }}
      >← Retour</button>

      <div style={{
        background:'#fff', borderRadius:'16px', padding:'2rem',
        boxShadow:'0 4px 20px rgba(0,0,0,0.05)', marginBottom:'1.5rem'
      }}>
        <div style={{ display:'flex', gap:'1.5rem', alignItems:'flex-start', flexWrap:'wrap' }}>
          <div style={{
            width:'100px', height:'100px', borderRadius:'50%',
            background:'linear-gradient(135deg, #6C63FF, #3ECFCF)',
            display:'flex', alignItems:'center', justifyContent:'center',
            color:'#fff', fontSize:'2.5rem', fontWeight:700, flexShrink:0
          }}>
            {data.prenom?.[0] || '?'}
          </div>

          <div style={{ flex:1, minWidth:'200px' }}>
            <h1 style={{ margin:0, fontSize:'1.8rem' }}>
              {data.prenom} {data.nom}
              {data.reputation?.badge_confiance && (
                <span
                  title="Prestataire de confiance"
                  style={{
                    marginLeft:'0.8rem', fontSize:'0.9rem', verticalAlign:'middle',
                    background:'linear-gradient(135deg, #fbbf24, #f59e0b)',
                    color:'#fff', padding:'0.3rem 0.7rem', borderRadius:'20px',
                    fontWeight:600
                  }}
                >🏅 Badge de confiance</span>
              )}
            </h1>
            <p style={{ color:'#64748b', margin:'0.4rem 0' }}>
              🎓 {data.universite || 'Université non renseignée'}
            </p>
            <p style={{ color:'#475569', margin:'0.8rem 0', fontStyle:'italic' }}>
              {data.biographie || 'Aucune biographie.'}
            </p>
            <div style={{ display:'flex', gap:'1rem', alignItems:'center', marginTop:'1rem' }}>
              <div>
                {[1,2,3,4,5].map(i => <Star key={i} filled={i <= filledStars} />)}
                <span style={{ marginLeft:'0.5rem', color:'#475569', fontSize:'0.9rem' }}>
                  ({note.toFixed(1)}/5 — {data.reputation?.nb_avis || 0} avis)
                </span>
              </div>
            </div>
          </div>

          <div style={{
            background:'#f8fafc', borderRadius:'12px', padding:'1rem 1.2rem',
            textAlign:'center', minWidth:'140px'
          }}>
            <div style={{ fontSize:'0.8rem', color:'#64748b' }}>Score réputation</div>
            <div style={{ fontSize:'2rem', fontWeight:700, color:'#6C63FF', margin:'0.3rem 0' }}>
              {(data.reputation?.score_global || 0).toFixed(1)}
            </div>
            <div style={{ fontSize:'0.75rem', color:'#94a3b8' }}>
              Taux complétion : {Math.round((data.reputation?.taux_completion || 0) * 100)}%
            </div>
            <div style={{ fontSize:'0.75rem', color:'#94a3b8' }}>
              {data.reputation?.nb_commandes_total || 0} commandes
            </div>
          </div>
        </div>
      </div>

      <h2 style={{ fontSize:'1.3rem', marginBottom:'1rem' }}>Services proposés</h2>
      {(data.services || []).length === 0 ? (
        <p style={{ color:'#94a3b8' }}>Aucun service publié pour le moment.</p>
      ) : (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(280px, 1fr))', gap:'1rem' }}>
          {data.services.map(s => (
            <div key={s.id} style={{
              background:'#fff', borderRadius:'12px', padding:'1rem',
              boxShadow:'0 2px 8px rgba(0,0,0,0.04)', cursor:'pointer'
            }} onClick={() => navigate(`/?service=${s.id}`)}>
              <h3 style={{ margin:'0 0 0.5rem', fontSize:'1rem' }}>{s.titre}</h3>
              <p style={{ color:'#64748b', fontSize:'0.85rem', margin:0 }}>{s.categorie}</p>
              <div style={{ marginTop:'0.8rem', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <span style={{ fontWeight:700, color:'#6C63FF' }}>{s.prix} TND</span>
                <span style={{ fontSize:'0.8rem', color:'#64748b' }}>★ {s.rating || 0} ({s.reviews_count || 0})</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <h2 style={{ fontSize:'1.3rem', marginTop:'2rem', marginBottom:'1rem' }}>Derniers avis</h2>
      {(data.recent_reviews || []).length === 0 ? (
        <p style={{ color:'#94a3b8' }}>Aucun avis pour le moment.</p>
      ) : (
        <div style={{ display:'grid', gap:'0.8rem' }}>
          {data.recent_reviews.map(r => (
            <div key={r.id} style={{
              background:'#fff', borderRadius:'10px', padding:'1rem',
              boxShadow:'0 1px 4px rgba(0,0,0,0.04)'
            }}>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'0.5rem' }}>
                <strong>{r.consumer_name || 'Consommateur'}</strong>
                <span>{[1,2,3,4,5].map(i => <Star key={i} filled={i <= r.score} />)}</span>
              </div>
              <p style={{ margin:0, color:'#475569' }}>{r.commentaire || '—'}</p>
              <p style={{ margin:'0.4rem 0 0', fontSize:'0.75rem', color:'#94a3b8' }}>
                {r.date_creation?.slice(0,10)} — {r.service_titre}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
