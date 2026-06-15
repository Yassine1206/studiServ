// frontend/src/components/OrderTracking.jsx
// Suivi d'une commande côté consommateur : statut, deadline (compte à rebours),
// état du paiement et disponibilité du livrable.
// Usage :
//   <OrderTracking orderId={order.id} onPayClick={(order) => ...} />

import { useEffect, useState } from 'react';
import { trackingAPI, deliverablesAPI, saveBlob } from '../api/addons';

const STEP_ORDER = ['pending', 'in_progress', 'completed'];

function formatDeadline(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  const diffMs = d - new Date();
  const days = Math.floor(diffMs / 86400000);
  const txt = d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  if (diffMs <= 0) return { txt, badge: 'Échéance dépassée', late: true };
  return { txt, badge: days <= 0 ? "Aujourd'hui" : `${days} j restant${days > 1 ? 's' : ''}`, late: false };
}

export default function OrderTracking({ orderId, onPayClick }) {
  const [t, setT] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  const load = async () => {
    try {
      const { data } = await trackingAPI.one(orderId);
      setT(data);
      if (data.deliverable_available || data.is_paid) {
        try {
          const f = await deliverablesAPI.list(orderId);
          setFiles(f.data || []);
        } catch { /* ignore */ }
      }
    } catch {
      setMsg("Impossible de charger le suivi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [orderId]);

  const download = async (livrableId, name) => {
    try {
      const res = await deliverablesAPI.download(orderId, livrableId);
      saveBlob(res.data, name || 'livrable.zip');
    } catch (err) {
      if (err.response?.status === 402) setMsg('Paiement requis pour télécharger.');
      else setMsg('Téléchargement impossible.');
    }
  };

  if (loading) return <div style={{ padding: 16 }}>Chargement du suivi…</div>;
  if (!t) return <div style={{ padding: 16 }}>{msg || 'Indisponible.'}</div>;

  const dl = formatDeadline(t.deadline);
  const activeStep = STEP_ORDER.indexOf(t.statut);

  return (
    <div style={S.card}>
      <div style={S.headRow}>
        <strong>{t.service_titre || t.titre}</strong>
        <span style={S.providerRef}>{t.provider_ref}</span>
      </div>

      {/* Stepper */}
      <div style={S.stepper}>
        {['En attente', 'En cours', 'Terminée'].map((label, i) => (
          <div key={label} style={S.step}>
            <div style={{ ...S.dot, ...(i <= activeStep ? S.dotOn : {}) }}>{i + 1}</div>
            <span style={{ fontSize: 12, color: i <= activeStep ? '#4338ca' : '#999' }}>{label}</span>
          </div>
        ))}
      </div>

      <div style={S.meta}>
        <div>
          <span style={S.metaLabel}>Statut</span>
          <div>{t.statut_label}</div>
        </div>
        <div>
          <span style={S.metaLabel}>Paiement</span>
          <div>{t.is_paid ? '✅ Payé' : '⏳ Non payé'}</div>
        </div>
        <div>
          <span style={S.metaLabel}>Montant</span>
          <div>{t.montant != null ? `${t.montant} TND` : '—'}</div>
        </div>
        <div>
          <span style={S.metaLabel}>Échéance</span>
          <div style={dl?.late ? { color: '#b3261e' } : {}}>
            {dl ? `${dl.txt} · ${dl.badge}` : '— (après paiement)'}
          </div>
        </div>
      </div>

      {!t.is_paid && (
        <button style={S.payBtn} onClick={() => onPayClick?.(t)}>
          Payer maintenant
        </button>
      )}

      {/* Livrable */}
      <div style={S.deliverBox}>
        <span style={S.metaLabel}>Livrable</span>
        {!t.is_paid ? (
          <div style={{ color: '#999', fontSize: 13 }}>🔒 Disponible après paiement.</div>
        ) : files.length === 0 ? (
          <div style={{ color: '#999', fontSize: 13 }}>
            Le prestataire n'a pas encore déposé de fichier.
          </div>
        ) : (
          files.map((f) => (
            <button key={f.id} style={S.dlBtn}
                    onClick={() => download(f.id, f.nom_original)}>
              ⬇ {f.nom_original || 'livrable.zip'}
            </button>
          ))
        )}
      </div>

      {msg && <div style={S.msg}>{msg}</div>}
    </div>
  );
}

const S = {
  card: { border: '1px solid #ececf3', borderRadius: 12, padding: 16, background: '#fff' },
  headRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  providerRef: { fontSize: 12, color: '#666', background: '#f3f3fb', padding: '3px 8px', borderRadius: 20 },
  stepper: { display: 'flex', justifyContent: 'space-between', margin: '16px 0' },
  step: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, flex: 1 },
  dot: { width: 26, height: 26, borderRadius: '50%', background: '#e6e6ef', color: '#999',
         display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 600 },
  dotOn: { background: '#4338ca', color: '#fff' },
  meta: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 6 },
  metaLabel: { display: 'block', fontSize: 11, color: '#999', textTransform: 'uppercase', letterSpacing: .4 },
  payBtn: { marginTop: 14, padding: '10px 14px', border: 'none', borderRadius: 9,
            background: '#4338ca', color: '#fff', fontWeight: 600, cursor: 'pointer' },
  deliverBox: { marginTop: 14, paddingTop: 12, borderTop: '1px dashed #e6e6ef' },
  dlBtn: { display: 'block', marginTop: 6, padding: '8px 12px', border: '1px solid #4338ca',
           borderRadius: 8, background: '#fff', color: '#4338ca', cursor: 'pointer', textAlign: 'left' },
  msg: { marginTop: 10, fontSize: 13, color: '#b3261e' },
};
