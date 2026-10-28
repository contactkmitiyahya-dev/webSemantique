import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../../api/client";
import FilterBar from "../../components/FilterBar";
import SearchBox from "../../components/SearchBox";

const TAILLE = 20;
const TYPES = [
  "TutorielComplet", "SupportPDF", "GuideRapide", "Diapositives",
  "DocumentationOfficielle", "EditeurEnLigne", "DocumentReference", "Video", "Webinaire",
];
const LANGUES = [
  { valeur: "fr", label: "Français" },
  { valeur: "en", label: "Anglais" },
];

const FILTRES = [
  { id: "type", label: "Type", options: TYPES.map((t) => ({ valeur: t, label: t })) },
  { id: "langue", label: "Langue", options: LANGUES },
];

export default function RessourcesListe() {
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
      .get("/ressources", {
        params: {
          q,
          type: valeurs.type ?? "",
          langue: valeurs.langue ?? "",
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
          <h1 className="page-title">Ressources pédagogiques</h1>
          <p className="page-subtitle">{total} {total > 1 ? "ressources" : "ressource"}</p>
        </div>
        <Link to="/ressources/nouveau" className="btn btn-primary">+ Nouvelle ressource</Link>
      </div>

      <div style={styles.barre}>
        <SearchBox valeur={q} onChange={changerRecherche} placeholder="Rechercher une ressource..." />
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
        <div className="empty-state"><p>Aucune ressource trouvée.</p></div>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr><th>Ressource</th><th>Langue</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {donnees.map((x) => (
                <tr key={x.id} className="table-row">
                  <td className="font-medium"><Link to={`/ressources/${x.id}`}>{x.label}</Link></td>
                  <td>{x.langue && <span className="pastille">{x.langue}</span>}</td>
                  <td className="actions-cell">
                    <Link to={`/ressources/${x.id}`} className="btn-sm btn-outline">Voir</Link>
                    <Link to={`/ressources/${x.id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
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
