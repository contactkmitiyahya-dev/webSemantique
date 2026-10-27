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
    <main style={styles.page}>
      <h1>Modules</h1>
      <Link to="/modules/nouveau">+ Nouveau module</Link>
      <div style={styles.barre}>
        <SearchBox valeur={q} onChange={changerRecherche} placeholder="Rechercher un module..." />
      </div>
      <FilterBar
        filtres={FILTRES}
        valeurs={valeurs}
        onChange={changerFiltre}
        onReset={reinitialiser}
      />

      {erreur && <p style={styles.erreur}>{erreur}</p>}
      {chargement && <p>Chargement...</p>}

      {!chargement && !erreur && (
        <>
          <p>{total} module(s)</p>
          {donnees.length === 0 && <p>Aucun module trouvé.</p>}
          <ul style={styles.liste}>
            {donnees.map((m) => (
              <li key={m.id} style={styles.item}>
                <Link to={`/modules/${m.id}`}>{m.intitule}</Link>
                <span>{m.niveauDifficulte}</span>
                <span>{m.dureeHeures} h</span>
              </li>
            ))}
          </ul>
          <div style={styles.pagination}>
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Précédent
            </button>
            <span>
              Page {page} / {pages}
            </span>
            <button disabled={page >= pages} onClick={() => setPage(page + 1)}>
              Suivant
            </button>
          </div>
        </>
      )}
    </main>
  );
}

const styles = {
  page: { padding: "24px", fontFamily: "sans-serif" },
  barre: { marginBottom: "12px" },
  erreur: { color: "#e53e3e" },
  liste: { listStyle: "none", padding: 0 },
  item: {
    display: "flex",
    gap: "16px",
    padding: "10px 0",
    borderBottom: "1px solid #eee",
  },
  pagination: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginTop: "16px",
  },
};
