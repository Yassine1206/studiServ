import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ServiceCard from '../components/ServiceCard';
import { servicesAPI } from '../api/axios';
import '../styles/Home.css';

function Home() {
  const navigate = useNavigate();
  const [services, setServices]             = useState([]);
  const [filteredServices, setFilteredServices] = useState([]);
  const [searchQuery, setSearchQuery]       = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading]               = useState(true);

  const categories = [
    { id: 'all',         name: 'Tous les services' },
    { id: 'tutoring',    name: 'Cours particuliers' },
    { id: 'design',      name: 'Graphisme' },
    { id: 'translation', name: 'Traduction' },
    { id: 'development', name: 'Développement' },
    { id: 'video',       name: 'Montage vidéo' },
    { id: 'writing',     name: 'Rédaction' },
  ];

  useEffect(() => {
    fetchServices();
  }, []);

  useEffect(() => {
    filterServices();
  }, [services, searchQuery, selectedCategory]);

  const fetchServices = async () => {
    try {
      const response = await servicesAPI.getAll();
      setServices(response.data || getMockServices());
    } catch {
      setServices(getMockServices());
    } finally {
      setLoading(false);
    }
  };

  const filterServices = () => {
    let result = services;
    if (selectedCategory !== 'all') {
      result = result.filter((s) => s.categorie === selectedCategory);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (s) =>
          s.titre?.toLowerCase().includes(q) ||
          s.description?.toLowerCase().includes(q) ||
          s.provider_name?.toLowerCase().includes(q)
      );
    }
    setFilteredServices(result);
  };

  const getMockServices = () => [
    { id: 1, titre: 'Cours de Mathématiques', provider_name: 'Ahmed Ben Ali', categorie: 'tutoring', prix: 25, description: 'Cours de maths pour lycée et supérieur', rating: 4.8, reviews_count: 24, image: '📐' },
    { id: 2, titre: 'Design Graphique', provider_name: 'Leila Hamzi', categorie: 'design', prix: 40, description: 'Création de logos, affiches et identités visuelles', rating: 4.9, reviews_count: 18, image: '🎨' },
    { id: 3, titre: 'Traduction FR/EN/AR', provider_name: 'Mehdi Khlifi', categorie: 'translation', prix: 15, description: 'Traduction de documents et textes académiques', rating: 4.7, reviews_count: 32, image: '🌍' },
    { id: 4, titre: 'Développement Web', provider_name: 'Sara Ben Salah', categorie: 'development', prix: 60, description: 'Sites web React et Django sur mesure', rating: 5.0, reviews_count: 12, image: '💻' },
  ];

  return (
    <div className="home">
      <Navbar />

      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <h1>Trouvez les meilleurs services étudiants</h1>
          <p>Des prestataires vérifiés parmi vos camarades</p>
          <div className="hero-search">
            <input
              type="text"
              placeholder="Rechercher un service (ex : cours de maths, design...)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="hero-search-input"
            />
            <button
              className="btn-primary"
              onClick={filterServices}
            >
              🔍 Rechercher
            </button>
          </div>
        </div>
      </section>

      {/* Catégories */}
      <section className="categories">
        <div className="container">
          <div className="category-filters">
            {categories.map((cat) => (
              <button
                key={cat.id}
                className={`category-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat.id)}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Services */}
      <section className="services-section">
        <div className="container">
          <h2>
            {selectedCategory === 'all'
              ? 'Tous les services'
              : categories.find((c) => c.id === selectedCategory)?.name}
            <span className="count"> ({filteredServices.length})</span>
          </h2>

          {loading ? (
            <div className="loading-grid">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="service-card skeleton" />
              ))}
            </div>
          ) : filteredServices.length === 0 ? (
            <div className="empty-state">
              <p>🔍 Aucun service trouvé pour &quot;{searchQuery}&quot;</p>
              <button
                className="btn-secondary"
                onClick={() => { setSearchQuery(''); setSelectedCategory('all'); }}
              >
                Réinitialiser les filtres
              </button>
            </div>
          ) : (
            <div className="services-grid">
              {filteredServices.map((service) => (
                <ServiceCard key={service.id} service={service} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Vous avez une compétence à partager ?</h2>
          <p>Rejoignez nos prestataires et monétisez vos talents</p>
          <button
            className="btn-primary btn-large"
            onClick={() => navigate('/signup')}
          >
            Devenir prestataire
          </button>
        </div>
      </section>
    </div>
  );
}

export default Home;
