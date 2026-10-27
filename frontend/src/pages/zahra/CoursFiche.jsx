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

export default function CoursFiche() {
  const { id } = useParams();
  const [cours, setCours] = useState(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [erreurSuppression, setErreurSuppression] = useState("");
  const navigate = useNavigate();

  async function supprimer() {
    if (!window.confirm(`Supprimer le cours « ${cours.intitule} » ?`)) return;
    try {
      await client.delete(`/cours/${cours.id}`);
      navigate("/cours");
    } catch (e) {
      setErreurSuppression(e.message);
    }
  }

  useEffect(() => {
    setChargement(true);
    setErreur("");
    client
      .get(`/cours/${id}`)
      .then((res) => setCours(res.data))
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
        <Link to="/cours">Retour à la liste</Link>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <Link to="/cours">← Retour à la liste</Link>
      <h1>{cours.intitule}</h1>
      <Link to={`/cours/${cours.id}/modifier`}>Modifier ce cours</Link>
      <button onClick={supprimer} style={{ marginLeft: "16px", color: "#e53e3e" }}>
        Supprimer
      </button>
      {erreurSuppression && <p style={styles.erreur}>{erreurSuppression}</p>}
      <p>
        Niveau : {cours.niveauDifficulte} · Durée : {cours.dureeHeures} h · Ordre dans le module :{" "}
        {cours.ordreDansModule}
      </p>

      <Liste titre="Module" elements={cours.module} lien="/modules" />
      <Liste titre="Formateur" elements={cours.formateur} />
      <Liste titre="Compétences" elements={cours.competences} />
      <Liste titre="Technologies" elements={cours.technologies} />
      <Liste titre="Ressources" elements={cours.ressources} />
    </main>
  );
}

const styles = {
  page: { padding: "24px", fontFamily: "sans-serif" },
  erreur: { color: "#e53e3e" },
};
