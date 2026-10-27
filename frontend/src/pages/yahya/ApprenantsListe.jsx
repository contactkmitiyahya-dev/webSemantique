import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import "./yahya.css";

export default function ApprenantsListe() {
  const [apprenants, setApprenants] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [niveau, setNiveau]       = useState("");
  const [chargement, setChargement] = useState(true);
  const [page, setPage]           = useState(1);
  const [total, setTotal]         = useState(0);
  const TAILLE = 10;

  const chargerApprenants = (q = "", niv = "", p = 1) => {
    setChargement(true);
    const params = new URLSearchParams({ q, niveau: niv, page: p, taille: TAILLE });
    api.get(`/apprenants?${params}`)
      .then((res) => {
        setApprenants(res.data.donnees);
        setTotal(res.data.total);
        setChargement(false);
      })
      .catch(() => { alert("Erreur de chargement"); setChargement(false); });
  };

  useEffect(() => { chargerApprenants(); }, []);

  const handleRecherche = (e) => {
    e.preventDefault();
    setPage(1);
    chargerApprenants(recherche, niveau, 1);
  };

  const handleSupprimer = (id) => {
    if (window.confirm("Voulez-vous vraiment supprimer cet apprenant ?")) {
      api.delete(`/apprenants/${id}`)
        .then(() => chargerApprenants(recherche, niveau, page))
        .catch(() => alert("Erreur lors de la suppression."));
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Apprenants</h1>
          <p className="page-subtitle">{total} apprenant{total !== 1 ? "s" : ""} inscrits</p>
        </div>
        <Link to="/apprenants/nouveau" className="btn btn-primary">
          <span>+</span> Nouvel Apprenant
        </Link>
      </div>

      <form onSubmit={handleRecherche} className="search-bar">
        <input
          type="text"
          placeholder="Rechercher par nom…"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          className="input"
        />
        <select className="input select" value={niveau} onChange={(e) => setNiveau(e.target.value)}>
          <option value="">Tous les niveaux</option>
          {["Licence", "Master", "Doctorat", "BTS", "DUT", "Bac"].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
        <button type="submit" className="btn btn-secondary">Filtrer</button>
      </form>

      {chargement ? (
        <div className="loader-wrap"><div className="loader" /></div>
      ) : apprenants.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">👤</div>
          <p>Aucun apprenant trouvé</p>
        </div>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Prénom</th>
                <th>Niveau</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {apprenants.map((app) => (
                <tr key={app.id} className="table-row">
                  <td className="font-medium">{app.nom}</td>
                  <td>{app.prenom}</td>
                  <td><span className="badge">{app.niveau}</span></td>
                  <td className="actions-cell">
                    <Link to={`/apprenants/${app.id}`} className="btn-sm btn-outline">Voir</Link>
                    <button
                      onClick={() => handleSupprimer(app.id)}
                      className="btn-sm btn-danger"
                    >Supprimer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            <button className="btn-sm btn-outline" disabled={page === 1} onClick={() => { setPage(page - 1); chargerApprenants(recherche, niveau, page - 1); }}>← Précédent</button>
            <span className="page-info">Page {page}</span>
            <button className="btn-sm btn-outline" disabled={apprenants.length < TAILLE} onClick={() => { setPage(page + 1); chargerApprenants(recherche, niveau, page + 1); }}>Suivant →</button>
          </div>
        </div>
      )}
    </div>
  );
}
