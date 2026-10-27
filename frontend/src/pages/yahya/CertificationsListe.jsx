import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import "./yahya.css";

export default function CertificationsListe() {
  const [certs, setCerts]         = useState([]);
  const [recherche, setRecherche] = useState("");
  const [loading, setLoading]     = useState(true);

  const charger = (q = "") => {
    setLoading(true);
    api.get(`/certifications?q=${q}`)
      .then((res) => { setCerts(res.data.donnees); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { charger(); }, []);

  const handleSupprimer = (id) => {
    if (window.confirm("Supprimer cette certification ?")) {
      api.delete(`/certifications/${id}`).then(() => charger(recherche));
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Certifications</h1>
          <p className="page-subtitle">{certs.length} certification{certs.length !== 1 ? "s" : ""}</p>
        </div>
        <Link to="/certifications/nouvelle" className="btn btn-primary">+ Nouvelle Certification</Link>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); charger(recherche); }} className="search-bar">
        <input type="text" placeholder="Rechercher une certification…" value={recherche}
          onChange={(e) => setRecherche(e.target.value)} className="input" />
        <button type="submit" className="btn btn-secondary">Filtrer</button>
      </form>

      {loading ? (
        <div className="loader-wrap"><div className="loader" /></div>
      ) : certs.length === 0 ? (
        <div className="empty-state"><div className="empty-icon">🏆</div><p>Aucune certification trouvée</p></div>
      ) : (
        <div className="cards-grid">
          {certs.map((c, i) => (
            <div key={`${c.id}-${i}`} className="cert-card">
              <div className="cert-icon">🏅</div>
              <h3 className="cert-label">{c.label}</h3>
              {c.organisme && <p className="cert-meta">📋 {c.organisme}</p>}
              {c.dureeValiditeAns && <p className="cert-meta">⏳ Valide {c.dureeValiditeAns} an{c.dureeValiditeAns > 1 ? "s" : ""}</p>}
              <div className="cert-actions">
                <Link to={`/certifications/${c.id}`} className="btn-sm btn-outline">Voir</Link>
                <button onClick={() => handleSupprimer(c.id)} className="btn-sm btn-danger">Supprimer</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
