import { useNavigate } from 'react-router-dom';

function NotFound() {
  const navigate = useNavigate();
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      height: '100vh', gap: '1rem', textAlign: 'center',
      fontFamily: 'sans-serif'
    }}>
      <div style={{ fontSize: '5rem' }}>📚</div>
      <h1 style={{ fontSize: '3rem', margin: 0 }}>404</h1>
      <p style={{ color: '#666', fontSize: '1.1rem' }}>
        Cette page n&apos;existe pas ou a été déplacée.
      </p>
      <button
        onClick={() => navigate('/')}
        style={{
          padding: '0.75rem 2rem', background: '#6366f1',
          color: 'white', border: 'none', borderRadius: '8px',
          cursor: 'pointer', fontSize: '1rem'
        }}
      >
        Retour à l&apos;accueil
      </button>
    </div>
  );
}

export default NotFound;

