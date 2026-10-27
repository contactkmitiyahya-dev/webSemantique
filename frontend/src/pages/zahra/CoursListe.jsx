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
    <main style={styles.page}>
      <h1>Cours</h1>
      <Link to="/cours/nouveau">+ Nouveau cours</Link>
      <div style={styles.barre}>
        <SearchBox valeur={q} onChange={changerRecherche} placeholder="Rechercher un cours..." />
      </div>
      <FilterBar
        filtres={filtres}
        valeurs={valeurs}
        onChange={changerFiltre}
        onReset={reinitialiser}
      />

      {erreur && <p style={styles.erreur}>{erreur}</p>}
      {chargement && <p>Chargement...</p>}

      {!chargement && !erreur && (
        <>
          <p>{total} cours</p>
          {donnees.length === 0 && <p>Aucun cours trouvé.</p>}
          <ul style={styles.liste}>
            {donnees.map((c) => (
              <li key={c.id} style={styles.item}>
                <Link to={`/cours/${c.id}`}>{c.intitule}</Link>
                <span>{c.niveauDifficulte}</span>
                <span>{c.dureeHeures} h</span>
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
