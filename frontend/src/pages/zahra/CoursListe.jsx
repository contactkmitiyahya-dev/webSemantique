import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../../api/client";
import FilterBar from "../../components/FilterBar";
import SearchBox from "../../components/SearchBox";

const TAILLE = 20;
const NIVEAUX = ["Débutant", "Intermédiaire", "Avancé"];

export default function CoursListe() {
  const [donnees, setDonnees] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [valeurs, setValeurs] = useState({});
  const [page, setPage] = useState(1);
  const [modules, setModules] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    client
      .get("/modules", { params: { taille: 100 } })
      .then((res) => setModules(res.data.donnees))
      .catch(() => setModules([]));
  }, []);

  useEffect(() => {
    setChargement(true);
    setErreur("");
    client
      .get("/cours", {
        params: {
          q,
          niveau: valeurs.niveau ?? "",
          moduleId: valeurs.moduleId ?? "",
          page,
          taille: TAILLE,
        },
      })
      .then((res) => {
        setDonnees(res.data.donnees);
        setTotal(res.data.total);
      })
      .catch((e) => setErreur(e.message))
      .finally(() => setChargement(false));
  }, [q, valeurs, page]);

  const filtres = [
    {
      id: "niveau",
      label: "Niveau",
      options: NIVEAUX.map((n) => ({ valeur: n, label: n })),
    },
    {
      id: "moduleId",
      label: "Module",
      options: modules.map((m) => ({ valeur: m.id, label: m.intitule })),
    },
  ];

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
          <h1 className="page-title">Cours</h1>
          <p className="page-subtitle">{total} {total > 1 ? "cours" : "cours"}</p>
        </div>
        <Link to="/cours/nouveau" className="btn btn-primary">+ Nouveau cours</Link>
      </div>

      <div style={styles.barre}>
        <SearchBox valeur={q} onChange={changerRecherche} placeholder="Rechercher un cours..." />
      </div>
      <FilterBar
        filtres={filtres}
        valeurs={valeurs}
        onChange={changerFiltre}
        onReset={reinitialiser}
      />

      {erreur && <p className="erreur">{erreur}</p>}

      {chargement ? (
        <div className="loader-wrap"><div className="loader" /></div>
      ) : erreur ? null : donnees.length === 0 ? (
        <div className="empty-state"><p>Aucun cours trouvé.</p></div>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr><th>Cours</th><th>Niveau</th><th>Durée</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {donnees.map((x) => (
                <tr key={x.id} className="table-row">
                  <td className="font-medium"><Link to={`/cours/${x.id}`}>{x.intitule}</Link></td>
                  <td>{x.niveauDifficulte && <span className="badge">{x.niveauDifficulte}</span>}</td>
                  <td>{x.dureeHeures != null && `${x.dureeHeures} h`}</td>
                  <td className="actions-cell">
                    <Link to={`/cours/${x.id}`} className="btn-sm btn-outline">Voir</Link>
                    <Link to={`/cours/${x.id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
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
