import { useEffect, useState } from "react";
import api from "../../api/client";
import "./yahya.css";

export default function ApprenantsStats() {
  const [stats, setStats]   = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/apprenants/stats")
      .then((res) => { setStats(res.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const total = stats.reduce((sum, s) => sum + s.nombre, 0);
  const max   = Math.max(...stats.map((s) => s.nombre), 1);

  const COULEURS = ["#6366f1", "#22d3ee", "#a78bfa", "#34d399", "#f59e0b", "#f87171"];

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Statistiques</h1>
          <p className="page-subtitle">Répartition des {total} apprenants par niveau d'études</p>
        </div>
      </div>

      {loading ? (
        <div className="loader-wrap"><div className="loader" /></div>
      ) : stats.length === 0 ? (
        <div className="empty-state"><div className="empty-icon">📊</div><p>Aucune donnée disponible</p></div>
      ) : (
        <div className="stats-layout">
          {/* Barres */}
          <div className="card stats-card">
            <h3 className="card-title">Distribution par niveau</h3>
            <div className="bar-chart">
              {stats.map((s, i) => (
                <div key={i} className="bar-row">
                  <span className="bar-label">{s.niveau}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(s.nombre / max) * 100}%`,
                        background: COULEURS[i % COULEURS.length],
                      }}
                    />
                  </div>
                  <span className="bar-value">{s.nombre}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tableau récapitulatif */}
          <div className="card">
            <h3 className="card-title">Détail</h3>
            <table className="data-table">
              <thead>
                <tr><th>Niveau</th><th>Nombre</th><th>%</th></tr>
              </thead>
              <tbody>
                {stats.map((s, i) => (
                  <tr key={i} className="table-row">
                    <td><span className="color-dot" style={{ background: COULEURS[i % COULEURS.length] }} />{s.niveau}</td>
                    <td className="font-medium">{s.nombre}</td>
                    <td>{total > 0 ? Math.round((s.nombre / total) * 100) : 0}%</td>
                  </tr>
                ))}
                <tr className="table-total">
                  <td><strong>Total</strong></td>
                  <td><strong>{total}</strong></td>
                  <td><strong>100%</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
