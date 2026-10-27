import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../../api/client";

function Liste({ titre, elements, lien }) {
  return (
    <section>
      <h2>{titre}</h2>
      {elements.length === 0 ? (
        <p>Aucun.</p>
      ) : (
        <ul>
          {elements.map((e) => (
            <li key={e.id}>
              {lien ? <Link to={`${lien}/${e.id}`}>{e.label}</Link> : e.label}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function RessourceFiche() {
  const { id } = useParams();
  const [ressource, setRessource] = useState(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [erreurSuppression, setErreurSuppression] = useState("");
  const navigate = useNavigate();

  async function supprimer() {
    if (!window.confirm(`Supprimer la ressource « ${ressource.label} » ?`)) return;
    try {
      await client.delete(`/ressources/${ressource.id}`);
      navigate("/ressources");
    } catch (e) {
      setErreurSuppression(e.message);
    }
  }

  useEffect(() => {
    setChargement(true);
    setErreur("");
    client
      .get(`/ressources/${id}`)
      .then((res) => setRessource(res.data))
      .catch((e) => setErreur(e.message))
      .finally(() => setChargement(false));
  }, [id]);

  if (chargement) {
    return <main style={styles.page}><p>Chargement...</p></main>;
  }

  if (erreur) {
    return (
      <main style={styles.page}>
        <p style={styles.erreur}>{erreur}</p>
        <Link to="/ressources">Retour à la liste</Link>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <Link to="/ressources">← Retour à la liste</Link>
      <h1>{ressource.label}</h1>
      <Link to={`/ressources/${ressource.id}/modifier`}>Modifier cette ressource</Link>
      <button onClick={supprimer} style={{ marginLeft: "16px", color: "#e53e3e" }}>
        Supprimer
      </button>
      {erreurSuppression && <p style={styles.erreur}>{erreurSuppression}</p>}

      <p>
        Langue : {ressource.langue}
        {ressource.dureeMinutes && ` · Durée : ${ressource.dureeMinutes} min`}
        {ressource.nombrePages && ` · Pages : ${ressource.nombrePages}`}
      </p>
      <p>
        Lien : <a href={ressource.urlRessource} target="_blank" rel="noreferrer">{ressource.urlRessource}</a>
      </p>

      <Liste titre="Compétences ciblées" elements={ressource.competencesCiblees} />
      <Liste titre="Utilisée par les cours" elements={ressource.utiliseeParCours} lien="/cours" />
    </main>
  );
}

const styles = {
  page: { padding: "24px", fontFamily: "sans-serif" },
  erreur: { color: "#e53e3e" },
};
