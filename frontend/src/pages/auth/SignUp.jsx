import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../api/axios';
import '../../styles/Auth.css';

function SignUp() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [step, setStep]                 = useState(1);
  const [selectedRole, setSelectedRole] = useState(null);
  const [formData, setFormData]         = useState({
    firstName: '', lastName: '', email: '',
    password: '', confirmPassword: '',
    university: '', studentCard: null,
  });
  const [error, setError]   = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setFormData((prev) => ({ ...prev, [name]: files ? files[0] : value }));
    setError('');
  };

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
    setStep(2);
  };

  const validatePassword = (pwd) => {
    if (pwd.length < 8)        return 'Le mot de passe doit contenir au moins 8 caractères.';
    if (!/[A-Z]/.test(pwd))    return 'Le mot de passe doit contenir au moins une majuscule.';
    if (!/[0-9]/.test(pwd))    return 'Le mot de passe doit contenir au moins un chiffre.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setError('Les mots de passe ne correspondent pas.');
      return;
    }
    const pwdError = validatePassword(formData.password);
    if (pwdError) { setError(pwdError); return; }

    setLoading(true);
    try {
      const data = new FormData();
      data.append('first_name', formData.firstName);
      data.append('last_name',  formData.lastName);
      data.append('email',      formData.email);
      data.append('password',   formData.password);
      data.append('role',       selectedRole);

      // Université et carte étudiante seulement pour les prestataires
      if (selectedRole === 'provider') {
        data.append('university', formData.university);
        if (formData.studentCard) data.append('student_card', formData.studentCard);
      }

      const response = await authAPI.signup(data);
      const { token, refresh, role, user } = response.data;

      localStorage.setItem('refresh', refresh);
      login(token, role, user);

      navigate(role === 'provider' ? '/provider/dashboard' : '/consumer/dashboard');
    } catch (err) {
      const errData = err.response?.data;
      if (typeof errData === 'object') {
        const msgs = Object.values(errData).flat().join(' ');
        setError(msgs);
      } else {
        setError("Erreur lors de l'inscription. Vérifiez vos informations.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-wrapper">

        {/* Gauche - Branding */}
        <div className="auth-brand">
          <div className="brand-content">
            <h1 className="brand-title">StudiServ</h1>
            <p className="brand-subtitle">Rejoignez la communauté StudiServ</p>
            <p className="brand-description">
              Inscrivez-vous pour trouver ou proposer des services de qualité.
            </p>
            <div className="brand-features">
              <div className="feature">✓ Inscription gratuite</div>
              <div className="feature">✓ Prestataires étudiants vérifiés</div>
              <div className="feature">✓ Paiement sécurisé</div>
            </div>
          </div>
        </div>

        {/* Droite - Formulaire */}
        <div className="auth-form-container">

          {/* ── ÉTAPE 1 : Choix du rôle ── */}
          {step === 1 && (
            <div className="auth-form-box">
              <h2>Je m&apos;inscris en tant que…</h2>
              <p className="form-subtitle">Choisissez votre rôle sur la plateforme</p>

              <div className="role-selection">
                <div
                  className={`role-card ${selectedRole === 'consumer' ? 'selected' : ''}`}
                  onClick={() => handleRoleSelect('consumer')}
                >
                  <div className="role-icon">🛒</div>
                  <h3>Consommateur</h3>
                  <p>Je cherche des services</p>
                  <ul className="role-benefits">
                    <li>Pas besoin d&apos;être étudiant</li>
                    <li>Rechercher et commander</li>
                    <li>Évaluer les prestataires</li>
                  </ul>
                </div>

                <div
                  className={`role-card ${selectedRole === 'provider' ? 'selected' : ''}`}
                  onClick={() => handleRoleSelect('provider')}
                >
                  <div className="role-icon">🎓</div>
                  <h3>Prestataire</h3>
                  <p>Je suis étudiant et je propose mes services</p>
                  <ul className="role-benefits">
                    <li>Réservé aux étudiants</li>
                    <li>Carte étudiante requise</li>
                    <li>Monétisez vos compétences</li>
                  </ul>
                </div>
              </div>

              <p className="terms-text">
                Déjà inscrit ? <Link to="/signin">Se connecter</Link>
              </p>
            </div>
          )}

          {/* ── ÉTAPE 2 : Formulaire ── */}
          {step === 2 && (
            <div className="auth-form-box">
              <button className="btn-back" onClick={() => setStep(1)}>
                ← Retour
              </button>

              <h2>
                {selectedRole === 'consumer' ? '🛒 Consommateur' : '🎓 Prestataire étudiant'}
              </h2>
              <p className="form-subtitle">
                {selectedRole === 'consumer'
                  ? 'Créez votre compte pour commander des services'
                  : 'Créez votre compte étudiant pour proposer vos services'}
              </p>

              {error && <div className="error-message">{error}</div>}

              <form onSubmit={handleSubmit} className="auth-form">

                {/* Prénom / Nom */}
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="firstName">Prénom</label>
                    <input
                      type="text" id="firstName" name="firstName"
                      placeholder="Jean"
                      value={formData.firstName}
                      onChange={handleChange} required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="lastName">Nom</label>
                    <input
                      type="text" id="lastName" name="lastName"
                      placeholder="Dupont"
                      value={formData.lastName}
                      onChange={handleChange} required
                    />
                  </div>
                </div>

                {/* Email — label différent selon le rôle */}
                <div className="form-group">
                  <label htmlFor="email">
                    {selectedRole === 'provider' ? 'Email universitaire' : 'Email'}
                  </label>
                  <input
                    type="email" id="email" name="email"
                    placeholder={
                      selectedRole === 'provider'
                        ? 'prenom.nom@universite.edu'
                        : 'votre@email.com'
                    }
                    value={formData.email}
                    onChange={handleChange} required
                    autoComplete="email"
                  />
                  {selectedRole === 'provider' && (
                    <small>Utilisez votre adresse email universitaire</small>
                  )}
                </div>

                {/* Université + Carte étudiante — prestataire uniquement */}
                {selectedRole === 'provider' && (
                  <>
                    <div className="form-group">
                      <label htmlFor="university">Université *</label>
                      <input
                        type="text" id="university" name="university"
                        placeholder="Université de Tunis"
                        value={formData.university}
                        onChange={handleChange} required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="studentCard">
                        Carte étudiante * (PDF / Image)
                      </label>
                      <input
                        type="file" id="studentCard" name="studentCard"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={handleChange} required
                      />
                      <small>
                        Votre compte sera activé après vérification par un admin
                      </small>
                    </div>
                  </>
                )}

                {/* Mot de passe */}
                <div className="form-group">
                  <label htmlFor="password">Mot de passe</label>
                  <input
                    type="password" id="password" name="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange} required minLength="8"
                    autoComplete="new-password"
                  />
                  <small>8 caractères min., une majuscule, un chiffre</small>
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirmer le mot de passe</label>
                  <input
                    type="password" id="confirmPassword" name="confirmPassword"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange} required
                    autoComplete="new-password"
                  />
                </div>

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Inscription...' : 'Créer mon compte'}
                </button>
              </form>

              <p className="terms-text">
                En m&apos;inscrivant, j&apos;accepte les{' '}
                <a href="#terms">conditions d&apos;utilisation</a>
              </p>
            </div>
          )}

          <div className="auth-footer">
            <p>Déjà inscrit ? <Link to="/signin">Se connecter</Link></p>
          </div>

        </div>
      </div>
    </div>
  );
}

export default SignUp;