// ProviderProfile.jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../api/axios';
import Sidebar from '../../components/Sidebar';
import '../../styles/Dashboard.css';
import '../../styles/Profile.css';

function ProviderProfile() {
  const { user, refreshUser } = useAuth();
  const [profile, setProfile]   = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [saving, setSaving]     = useState(false);
  const [msg, setMsg]           = useState('');

  useEffect(() => {
    authAPI.getProfile().then(res => {
      setProfile(res.data);
      setFormData({
        first_name: res.data.first_name || '',
        last_name:  res.data.last_name  || '',
        biographie: res.data.profil?.biographie || '',
        universite: res.data.profil?.universite  || '',
        telephone:  res.data.profil?.telephone   || '',
      });
    }).catch(() => setProfile({ ...user, profil: {} }));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await authAPI.updateProfile(formData);
      await refreshUser();
      setMsg('Profil mis à jour !');
      setIsEditing(false);
      setTimeout(() => setMsg(''), 3000);
    } catch { setMsg('Erreur.'); }
    finally { setSaving(false); }
  };

  if (!profile) return <div className="dashboard"><Sidebar role="provider" /><div className="dashboard-content loading-state">Chargement...</div></div>;

  return (
    <div className="dashboard">
      <Sidebar role="provider" />
      <div className="dashboard-content">
        <div className="dashboard-header"><h1>Mon profil Prestataire</h1></div>
        {msg && <div style={{ background: '#d1fae5', color: '#065f46', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem' }}>{msg}</div>}

        <div className="profile-container">
          <div className="profile-card">
            <div className="profile-header-section">
              <div className="avatar-large">⭐</div>
              <div className="profile-header-info">
                <h2>{profile.first_name} {profile.last_name}</h2>
                <p className="email">{profile.email}</p>
                <p>📚 {profile.profil?.universite || 'Université non renseignée'}</p>
                <p style={{ color: '#f59e0b' }}>⭐ {profile.profil?.note_moyenne || 0}/5 · {profile.profil?.nb_commandes_total || 0} commandes</p>
              </div>
              <button className="btn-edit" onClick={() => setIsEditing(!isEditing)}>
                {isEditing ? 'Annuler' : '✏️ Modifier'}
              </button>
            </div>

            {isEditing ? (
              <div className="profile-form">
                <div className="form-row">
                  <div className="form-group"><label>Prénom</label><input value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} /></div>
                  <div className="form-group"><label>Nom</label><input value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} /></div>
                </div>
                <div className="form-group"><label>Université</label><input value={formData.universite} onChange={e => setFormData({...formData, universite: e.target.value})} /></div>
                <div className="form-group"><label>Téléphone</label><input value={formData.telephone} onChange={e => setFormData({...formData, telephone: e.target.value})} /></div>
                <div className="form-group"><label>Biographie</label><textarea rows={3} value={formData.biographie} onChange={e => setFormData({...formData, biographie: e.target.value})} /></div>
                <div className="form-actions">
                  <button className="btn-save" onClick={handleSave} disabled={saving}>{saving ? 'Sauvegarde...' : 'Enregistrer'}</button>
                  <button className="btn-cancel" onClick={() => setIsEditing(false)}>Annuler</button>
                </div>
              </div>
            ) : (
              <div className="profile-section">
                <h3>Informations</h3>
                <div className="info-grid">
                  <div className="info-item"><label>Biographie</label><p>{profile.profil?.biographie || '—'}</p></div>
                  <div className="info-item"><label>Téléphone</label><p>{profile.profil?.telephone || '—'}</p></div>
                  <div className="info-item"><label>Réputation</label><p>{profile.profil?.score_reputation || 0}</p></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProviderProfile;
