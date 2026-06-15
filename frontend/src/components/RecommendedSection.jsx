// frontend/src/components/RecommendedSection.jsx
// Section "Recommandé" pour la page d'accueil (publique).
// Affiche les meilleurs prestataires + les services les mieux notés.
// Usage dans Home.jsx :  <RecommendedSection />

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { homeAPI } from '../api/addons';

export default function RecommendedSection() {
  const navigate = useNavigate();
  const [data, setData] = useState({ top_providers: [], top_services: [], personalized: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    homeAPI.recommended()
      .then((res) => { if (alive) setData(res.data); })
      .catch(() => {})
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  if (loading) return null;

  const { top_providers = [], top_services = [], personalized = [] } = data;
  if (!top_providers.length && !top_services.length && !personalized.length) return null;

  return (
    <section style={S.wrap}>
      <div style={S.container}>

        {personalized.length > 0 && (
          <>
            <h2 style={S.h2}>Recommandé pour vous</h2>
            <div style={S.grid}>
              {personalized.map((s) => (
                <div key={`p-${s.id}`} style={S.card} onClick={() => navigate(`/services/${s.id}`)}>
                  <div style={S.cat}>{s.categorie}</div>
                  <div style={S.title}>{s.titre}</div>
                  <div style={S.provider}>{s.provider_name}</div>
                  <div style={S.price}>{s.prix} TND</div>
                </div>
              ))}
            </div>
          </>
        )}

        {top_providers.length > 0 && (
          <>
            <h2 style={S.h2}>Top prestataires</h2>
            <div style={S.row}>
              {top_providers.map((p) => (
                <div key={`tp-${p.prestataire_id}`} style={S.provCard}>
                  <div style={S.avatar}>{(p.nom || '?').charAt(0).toUpperCase()}</div>
                  <div style={S.provName}>
                    {p.nom} {p.badge_confiance && <span title="Badge de confiance">✔️</span>}
                  </div>
                  <div style={S.stars}>⭐ {Number(p.note_moyenne || 0).toFixed(1)} · {p.nb_avis} avis</div>
                  <div style={S.muted}>{p.nb_services} service(s)</div>
                </div>
              ))}
            </div>
          </>
        )}

        {top_services.length > 0 && (
          <>
            <h2 style={S.h2}>Services les mieux notés</h2>
            <div style={S.grid}>
              {top_services.map((s) => (
                <div key={`ts-${s.id}`} style={S.card} onClick={() => navigate(`/services/${s.id}`)}>
                  <div style={S.cat}>{s.categorie}</div>
                  <div style={S.title}>{s.titre}</div>
                  <div style={S.provider}>{s.provider_name}</div>
                  <div style={S.starsSm}>⭐ {Number(s.note_moyenne || 0).toFixed(1)} ({s.nb_avis})</div>
                  <div style={S.price}>{s.prix} TND</div>
                </div>
              ))}
            </div>
          </>
        )}

      </div>
    </section>
  );
}

const S = {
  wrap: { padding: '32px 0', background: '#fafaff' },
  container: { maxWidth: 1100, margin: '0 auto', padding: '0 16px' },
  h2: { fontSize: 20, margin: '22px 0 12px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(210px,1fr))', gap: 14 },
  row: { display: 'flex', gap: 14, flexWrap: 'wrap' },
  card: { background: '#fff', border: '1px solid #ececf3', borderRadius: 12, padding: 14, cursor: 'pointer' },
  cat: { fontSize: 11, color: '#7c3aed', textTransform: 'uppercase', letterSpacing: .4 },
  title: { fontWeight: 600, margin: '6px 0' },
  provider: { fontSize: 13, color: '#666' },
  price: { marginTop: 8, fontWeight: 700, color: '#4338ca' },
  starsSm: { fontSize: 12, color: '#b8860b', marginTop: 4 },
  provCard: { background: '#fff', border: '1px solid #ececf3', borderRadius: 12, padding: 16, width: 170, textAlign: 'center' },
  avatar: { width: 48, height: 48, borderRadius: '50%', background: '#4338ca', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, margin: '0 auto 8px' },
  provName: { fontWeight: 600, fontSize: 14 },
  stars: { fontSize: 12, color: '#b8860b', marginTop: 4 },
  muted: { fontSize: 12, color: '#999', marginTop: 2 },
};
