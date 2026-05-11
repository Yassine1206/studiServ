import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../api/axios';
import '../../styles/Auth.css';

function SignIn() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData]     = useState({ email: '', password: '' });
  const [error, setError]           = useState('');
  const [loading, setLoading]       = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(0);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (loginAttempts >= 5) {
      setError('Trop de tentatives échouées. Veuillez réessayer plus tard.');
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.signin(formData.email, formData.password);
      const { token, refresh, role, user } = response.data;

      // Stocker aussi le refresh token
      localStorage.setItem('refresh', refresh);
      login(token, role, user);

      // Redirection selon le rôle
      const routes = {
        consumer: '/consumer/dashboard',
        provider: '/provider/dashboard',
        admin: '/admin/dashboard',
      };
      navigate(routes[role] || '/');
    } catch (err) {
      setLoginAttempts((prev) => prev + 1);
      setError(err.response?.data?.message || 'Identifiants incorrects.');
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
            <p className="brand-subtitle">
              La plateforme de confiance pour les services étudiants
            </p>
            <p className="brand-description">
              Connectez-vous pour explorer et acheter des services de qualité
              auprès de vos camarades étudiants.
            </p>
            <div className="brand-features">
              <div className="feature">✓ Paiement sécurisé</div>
              <div className="feature">✓ Prestataires vérifiés</div>
              <div className="feature">✓ Système de notation</div>
            </div>
          </div>
        </div>

        {/* Droite - Formulaire */}
        <div className="auth-form-container">
          <div className="auth-form-box">
            <h2>Connexion</h2>
            <p className="form-subtitle">Connectez-vous à votre compte</p>

            {error && <div className="error-message">{error}</div>}
            {loginAttempts > 0 && loginAttempts < 5 && (
              <div className="warning-message">
                {5 - loginAttempts} tentative(s) restante(s)
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="email">Email universitaire</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="vous@universite.edu"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Mot de passe</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  autoComplete="current-password"
                />
              </div>

              <div className="form-footer">
                <label>
                  <input type="checkbox" /> Se souvenir de moi
                </label>
                <Link to="/forgot-password" className="forgot-link">
                  Mot de passe oublié ?
                </Link>
              </div>

              <button
                type="submit"
                className="btn-primary"
                disabled={loading || loginAttempts >= 5}
              >
                {loading ? 'Connexion...' : 'Se connecter'}
              </button>
            </form>

            <div className="auth-divider">
              <span>Pas encore de compte ?</span>
            </div>

            <Link to="/signup" className="btn-secondary">
              Créer un compte
            </Link>

            <p className="terms-text">
              En vous connectant, vous acceptez nos{' '}
              <a href="#terms">conditions d&apos;utilisation</a> et notre{' '}
              <a href="#privacy">politique de confidentialité</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignIn;
