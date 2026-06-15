// frontend/src/components/OpenDisputeButton.jsx
// Bouton "Ouvrir un litige" pour une commande (consommateur ou prestataire).
// Usage :  <OpenDisputeButton orderId={order.id} />

import { useState } from 'react';
import { disputesAPI } from '../api/addons';

export default function OpenDisputeButton({ orderId }) {
  const [open, setOpen] = useState(false);
  const [desc, setDesc] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const submit = async () => {
    if (!desc.trim()) { setMsg('Décris le problème.'); return; }
    setBusy(true); setMsg('');
    try {
      await disputesAPI.open(orderId, desc.trim());
      setMsg('Litige ouvert. Un administrateur va l\'examiner.');
      setDesc('');
      setTimeout(() => setOpen(false), 1200);
    } catch (e) {
      setMsg(e.response?.data?.error || 'Impossible d\'ouvrir le litige.');
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button style={S.link} onClick={() => setOpen(true)}>⚠ Signaler un problème</button>
    );
  }
  return (
    <div style={S.box}>
      <textarea style={S.ta} rows={3} placeholder="Décris le problème (travail non livré, qualité…)"
                value={desc} onChange={(e) => setDesc(e.target.value)} />
      {msg && <div style={S.msg}>{msg}</div>}
      <div style={{ display: 'flex', gap: 8 }}>
        <button style={S.send} onClick={submit} disabled={busy}>
          {busy ? 'Envoi…' : 'Ouvrir le litige'}
        </button>
        <button style={S.cancel} onClick={() => setOpen(false)}>Annuler</button>
      </div>
    </div>
  );
}

const S = {
  link: { border: 'none', background: 'none', color: '#b3261e', cursor: 'pointer', fontSize: 13, padding: 0 },
  box: { marginTop: 8, padding: 10, border: '1px solid #f0d6d6', borderRadius: 8, background: '#fff8f8' },
  ta: { width: '100%', padding: 8, borderRadius: 8, border: '1px solid #d6d6e0', boxSizing: 'border-box' },
  msg: { fontSize: 12, color: '#333', margin: '6px 0' },
  send: { padding: '7px 12px', border: 'none', borderRadius: 8, background: '#b3261e', color: '#fff', cursor: 'pointer' },
  cancel: { padding: '7px 12px', border: '1px solid #d6d6e0', borderRadius: 8, background: '#fff', cursor: 'pointer' },
};
