// frontend/src/components/DeliverablePanel.jsx
// Côté PRESTATAIRE : déposer une archive ZIP livrable pour une commande.
// Le consommateur ne pourra la télécharger qu'après paiement (géré par le backend).
// Usage : <DeliverablePanel orderId={order.id} />

import { useEffect, useState } from 'react';
import { deliverablesAPI } from '../api/addons';

export default function DeliverablePanel({ orderId }) {
  const [files, setFiles] = useState([]);
  const [selected, setSelected] = useState(null);
  const [desc, setDesc] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const load = async () => {
    try {
      const { data } = await deliverablesAPI.list(orderId);
      setFiles(data || []);
    } catch { /* ignore */ }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [orderId]);

  const pick = (e) => {
    const f = e.target.files?.[0];
    setMsg('');
    if (f && !f.name.toLowerCase().endsWith('.zip')) {
      setMsg('Seules les archives .zip sont acceptées.');
      setSelected(null);
      return;
    }
    setSelected(f || null);
  };

  const upload = async () => {
    if (!selected) return;
    setBusy(true);
    setMsg('');
    try {
      await deliverablesAPI.upload(orderId, selected, desc);
      setSelected(null);
      setDesc('');
      setMsg('Livrable déposé ✅');
      load();
    } catch (err) {
      setMsg(err.response?.data?.error || 'Échec du dépôt.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={S.box}>
      <strong>Livrable (ZIP)</strong>
      <p style={S.note}>
        Déposez l'archive du travail terminé. Le client y aura accès une fois le paiement effectué.
      </p>

      <input type="file" accept=".zip" onChange={pick} />
      <input style={S.desc} placeholder="Description (optionnel)"
             value={desc} onChange={(e) => setDesc(e.target.value)} />
      <button style={S.btn} onClick={upload} disabled={!selected || busy}>
        {busy ? 'Envoi…' : 'Déposer le ZIP'}
      </button>

      {msg && <div style={S.msg}>{msg}</div>}

      {files.length > 0 && (
        <div style={S.list}>
          <span style={S.listLabel}>Déjà déposé :</span>
          {files.map((f) => (
            <div key={f.id} style={S.item}>📦 {f.nom_original} ({Math.round((f.taille_octets || 0) / 1024)} Ko)</div>
          ))}
        </div>
      )}
    </div>
  );
}

const S = {
  box: { border: '1px solid #ececf3', borderRadius: 12, padding: 16, background: '#fff' },
  note: { fontSize: 13, color: '#666', margin: '6px 0 12px' },
  desc: { display: 'block', width: '100%', marginTop: 10, padding: '8px 10px',
          borderRadius: 8, border: '1px solid #d6d6e0', boxSizing: 'border-box' },
  btn: { marginTop: 12, padding: '10px 14px', border: 'none', borderRadius: 9,
         background: '#4338ca', color: '#fff', fontWeight: 600, cursor: 'pointer' },
  msg: { marginTop: 10, fontSize: 13, color: '#333' },
  list: { marginTop: 14, paddingTop: 12, borderTop: '1px dashed #e6e6ef' },
  listLabel: { fontSize: 11, color: '#999', textTransform: 'uppercase' },
  item: { fontSize: 13, marginTop: 6 },
};
