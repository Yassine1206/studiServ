import '../styles/Components.css';

function DashboardStats({ stats }) {
  return (
    <div className="stats-container">
      {stats.map((stat, idx) => (
        <div key={idx} className="stat-card">
          <div className="stat-icon">{stat.icon}</div>
          <div className="stat-content">
            <p className="stat-label">{stat.label}</p>
            <p className="stat-value">{stat.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default DashboardStats;
