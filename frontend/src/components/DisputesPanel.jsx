// frontend/src/components/DisputesPanel.jsx
// Côté ADMIN : lister et résoudre les litiges.
// À placer dans un onglet "Litiges" de AdminDashboard.jsx :  <DisputesPanel />

import { useEffect, useState } from 'react';
import { disputesAPI } from '../api/addons';

const RESOLUTIONS = [
  { v: 'refund', label: 'Rembourser' },
  { v: 'completed', label: 'Valider la prestation' },
  { v: 'partial', label: 'Résolution partielle' },
  { v: 'dismissed', label: 'Rejeter' },
];

export default function DisputesPanel() {
  const [disputes, setDisputes] = useState([]);
  const [tab, setTab] = useState('open');
  const [note, setNote] = useState({});
  const [msg, setMsg] = useState('');

  const load = (status) => {
    disputesAPI.adminList(status)
      .then((r) => setDisputes(r.data || []))
      .catch(() => setDisputes([]));
  };
  useEffect(() => { load(tab); }, [tab]);

  const resolve = async (id, resolution) => {
    setMsg('');
    try {
      await disputesAPI.adminResolve(id, resolution, note[id] || '');
      setMsg('Litige résolu.');
      load(tab);
    } catch (e) {
      setMsg(e.response?.data?.error || 'Erreur.');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {['open', 'resolved'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
                  style={{ ...S.tab, ...(tab === t ? S.tabOn : {}) }}>
            {t === 'open' ? 'Ouverts' : 'Résolus'}
          </button>
        ))}
      </div>
      {msg && <div style={S.msg}>{msg}</div>}
      {disputes.length === 0 ? (
        <div style={{ color: '#999' }}>Aucun litige.</div>
      ) : disputes.map((d) => (
        <div key={d.id} style={S.card}>
          <div style={S.head}>
            <strong>Litige #{d.id} · Commande #{d.order_id}</strong>
            <span style={S.badge}>{d.status}</span>
          </div>
          {d.service && <div style={S.svc}>Service : {d.service}</div>}
          <div style={S.by}>Ouvert par {d.opened_by}</div>
          <p style={S.desc}>{d.description}</p>
          {d.status !== 'resolved' && d.status !== 'closed' ? (
            <>
              <input style={S.note} placeholder="Note de l'admin (optionnel)"
                     value={note[d.id] || ''}
                     onChange={(e) => setNote({ ...note, [d.id]: e.target.value })} />
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                {RESOLUTIONS.map((r) => (
                  <button key={r.v} style={S.action} onClick={() => resolve(d.id, r.v)}>
                    {r.label}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div style={S.resolved}>Résolution : {d.resolution || '—'}
              {d.admin_note ? ` · ${d.admin_note}` : ''}</div>
          )}
        </div>
      ))}
    </div>
  );
}

const S = {
  tab: { padding: '6px 14px', borderRadius: 20, border: '1px solid #d6d6e0', background: '#fff', cursor: 'pointer' },
  tabOn: { background: '#4338ca', color: '#fff', borderColor: '#4338ca' },
  card: { border: '1px solid #ececf3', borderRadius: 12, padding: 14, marginBottom: 10, background: '#fff' },
  head: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  badge: { fontSize: 11, background: '#f3f3fb', padding: '2px 8px', borderRadius: 12 },
  svc: { fontSize: 13, color: '#444', marginTop: 4 },
  by: { fontSize: 12, color: '#888', marginTop: 2 },
  desc: { margin: '8px 0', fontSize: 14 },
  note: { width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid #d6d6e0', boxSizing: 'border-box' },
  action: { padding: '7px 12px', border: 'none', borderRadius: 8, background: '#4338ca', color: '#fff', cursor: 'pointer', fontSize: 13 },
  resolved: { fontSize: 13, color: '#1a7f37', marginTop: 6 },
  msg: { fontSize: 13, color: '#333', marginBottom: 8 },
};
