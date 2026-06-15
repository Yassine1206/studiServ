// frontend/src/components/PaymentModal.jsx
// Fenêtre de paiement (simulé mais validé : Luhn, expiration, CVV).
// Usage :
//   <PaymentModal order={order} onPaid={(paiement) => ...} onClose={() => ...} />
//
// Carte de test OK : 4242 4242 4242 4242  (n'importe quelle date future, CVV 3 chiffres)
// Carte refusée    : 4000 0000 0000 0002

import { useState } from 'react';
import { paymentAPI } from '../api/addons';

export default function PaymentModal({ order, onPaid, onClose }) {
  const [form, setForm] = useState({
    card_name: '', card_number: '', exp_month: '', exp_year: '', cvv: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const amount = order?.montant ?? order?.service?.prix ?? order?.prix ?? '';

  const change = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    setError('');
  };

  const submit = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await paymentAPI.pay(order.id, {
        ...form,
        card_number: form.card_number.replace(/\s+/g, ''),
        methode: 'card',
      });
      onPaid?.(res.data.paiement);
    } catch (err) {
      setError(err.response?.data?.error || 'Le paiement a échoué.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={S.overlay} onClick={onClose}>
      <div style={S.modal} onClick={(e) => e.stopPropagation()}>
        <div style={S.head}>
          <strong>Paiement sécurisé</strong>
          <button style={S.x} onClick={onClose}>✕</button>
        </div>

        <p style={S.amount}>
          Montant : <b>{amount} TND</b>
        </p>

        <label style={S.label}>Titulaire de la carte</label>
        <input style={S.input} name="card_name" value={form.card_name}
               onChange={change} placeholder="Prénom Nom" />

        <label style={S.label}>Numéro de carte</label>
        <input style={S.input} name="card_number" value={form.card_number}
               onChange={change} placeholder="4242 4242 4242 4242" inputMode="numeric" />

        <div style={S.row}>
          <div style={{ flex: 1 }}>
            <label style={S.label}>Mois</label>
            <input style={S.input} name="exp_month" value={form.exp_month}
                   onChange={change} placeholder="MM" inputMode="numeric" />
          </div>
          <div style={{ flex: 1 }}>
            <label style={S.label}>Année</label>
            <input style={S.input} name="exp_year" value={form.exp_year}
                   onChange={change} placeholder="AAAA" inputMode="numeric" />
          </div>
          <div style={{ flex: 1 }}>
            <label style={S.label}>CVV</label>
            <input style={S.input} name="cvv" value={form.cvv}
                   onChange={change} placeholder="123" inputMode="numeric" />
          </div>
        </div>

        {error && <div style={S.error}>{error}</div>}

        <button style={S.pay} onClick={submit} disabled={loading}>
          {loading ? 'Traitement…' : `Payer ${amount} TND`}
        </button>
        <p style={S.hint}>Paiement simulé pour la démo — aucune transaction réelle.</p>
      </div>
    </div>
  );
}

const S = {
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,.45)',
             display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { background: '#fff', borderRadius: 14, padding: 22, width: 380,
           maxWidth: '92vw', boxShadow: '0 20px 60px rgba(0,0,0,.25)' },
  head: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  x: { border: 'none', background: 'none', fontSize: 18, cursor: 'pointer' },
  amount: { margin: '0 0 14px', fontSize: 15 },
  label: { display: 'block', fontSize: 12, color: '#555', margin: '8px 0 4px' },
  input: { width: '100%', padding: '10px 12px', borderRadius: 8,
           border: '1px solid #d6d6e0', fontSize: 14, boxSizing: 'border-box' },
  row: { display: 'flex', gap: 8 },
  error: { background: '#fdecec', color: '#b3261e', padding: '8px 10px',
           borderRadius: 8, fontSize: 13, marginTop: 10 },
  pay: { width: '100%', marginTop: 16, padding: '12px', borderRadius: 10, border: 'none',
         background: '#4338ca', color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: 15 },
  hint: { fontSize: 11, color: '#888', textAlign: 'center', marginTop: 8 },
};
