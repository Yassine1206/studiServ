import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../../api/axios';
import '../../styles/Auth.css';

function ForgotPassword() {
  const [email, setEmail]     = useState('');
  const [sent, setSent]       = useState(false);
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await authAPI.resetPassword(email);
      setSent(true);
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Une erreur est survenue. Vérifiez votre email.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-wrapper auth-wrapper--narrow">
        <div className="auth-form-container">
          <div className="auth-form-box">
            {sent ? (
              <>
                <div className="success-icon">📧</div>
                <h2>Email envoyé !</h2>
                <p className="form-subtitle">
                  Si l&apos;adresse <strong>{email}</strong> est associée à un
                  compte, vous recevrez un lien de réinitialisation.
                </p>
                <Link to="/signin" className="btn-primary" style={{ display: 'block', textAlign: 'center' }}>
                  Retour à la connexion
                </Link>
              </>
            ) : (
              <>
                <h2>Mot de passe oublié</h2>
                <p className="form-subtitle">
                  Saisissez votre email pour recevoir un lien de
                  réinitialisation.
                </p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                  <div className="form-group">
                    <label htmlFor="email">Email universitaire</label>
                    <input
                      type="email"
                      id="email"
                      placeholder="vous@universite.edu"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      autoComplete="email"
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={loading}
                  >
                    {loading ? 'Envoi...' : 'Envoyer le lien'}
                  </button>
                </form>

                <div className="auth-footer" style={{ marginTop: '1rem' }}>
                  <Link to="/signin" className="forgot-link">
                    ← Retour à la connexion
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword;
