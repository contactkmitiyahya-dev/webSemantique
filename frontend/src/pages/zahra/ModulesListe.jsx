import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../../api/client";
import FilterBar from "../../components/FilterBar";
import SearchBox from "../../components/SearchBox";

const TAILLE = 20;

const FILTRES = [
  {
    id: "niveau",
    label: "Niveau",
    options: ["Débutant", "Intermédiaire", "Avancé"].map((n) => ({ valeur: n, label: n })),
  },
];

export default function ModulesListe() {
  const [donnees, setDonnees] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [valeurs, setValeurs] = useState({});
  const [page, setPage] = useState(1);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    setChargement(true);
    setErreur("");
    client
      .get("/modules", { params: { q, niveau: valeurs.niveau ?? "", page, taille: TAILLE } })
      .then((res) => {
        setDonnees(res.data.donnees);
        setTotal(res.data.total);
      })
      .catch((e) => setErreur(e.message))
      .finally(() => setChargement(false));
  }, [q, valeurs, page]);

  const pages = Math.max(1, Math.ceil(total / TAILLE));

  function changerRecherche(valeur) {
    setQ(valeur);
    setPage(1);
  }

  function changerFiltre(id, valeur) {
    setValeurs((precedent) => ({ ...precedent, [id]: valeur }));
    setPage(1);
  }

  function reinitialiser() {
    setQ("");
    setValeurs({});
    setPage(1);
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Modules</h1>
          <p className="page-subtitle">{total} {total > 1 ? "modules" : "module"}</p>
        </div>
        <Link to="/modules/nouveau" className="btn btn-primary">+ Nouveau module</Link>
      </div>

      <div style={styles.barre}>
        <SearchBox valeur={q} onChange={changerRecherche} placeholder="Rechercher un module..." />
      </div>
      <FilterBar
        filtres={FILTRES}
        valeurs={valeurs}
        onChange={changerFiltre}
        onReset={reinitialiser}
      />

      {erreur && <p className="erreur">{erreur}</p>}

      {chargement ? (
        <div className="loader-wrap"><div className="loader" /></div>
      ) : erreur ? null : donnees.length === 0 ? (
        <div className="empty-state"><p>Aucun module trouvé.</p></div>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr><th>Module</th><th>Niveau</th><th>Durée</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {donnees.map((x) => (
                <tr key={x.id} className="table-row">
                  <td className="font-medium"><Link to={`/modules/${x.id}`}>{x.intitule}</Link></td>
                  <td>{x.niveauDifficulte && <span className="badge">{x.niveauDifficulte}</span>}</td>
                  <td>{x.dureeHeures != null && `${x.dureeHeures} h`}</td>
                  <td className="actions-cell">
                    <Link to={`/modules/${x.id}`} className="btn-sm btn-outline">Voir</Link>
                    <Link to={`/modules/${x.id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            <button className="btn-sm btn-outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              ← Précédent
            </button>
            <span className="page-info">Page {page} / {pages}</span>
            <button className="btn-sm btn-outline" disabled={page >= pages} onClick={() => setPage(page + 1)}>
              Suivant →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  barre: { marginBottom: "12px" },
};
