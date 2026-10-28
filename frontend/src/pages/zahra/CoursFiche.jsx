import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../../api/client";

function Liste({ titre, elements, lien }) {
  return (
    <div className="card">
      <h2 className="card-title">{titre}</h2>
      {elements.length === 0 ? (
        <p className="empty-text">Aucun.</p>
      ) : (
        <ul className="tag-list">
          {elements.map((e) => (
            <li key={e.id}>
              {lien ? (
                <Link to={`${lien}/${e.id}`} className="tag tag-lien">{e.label}</Link>
              ) : (
                <span className="tag">{e.label}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
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
    return <div className="loader-wrap"><div className="loader" /></div>;
  }

  if (erreur) {
    return (
      <main style={styles.page}>
        <p className="erreur">{erreur}</p>
        <Link to="/cours" className="retour">← Retour à la liste</Link>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <Link to="/cours" className="retour">← Retour à la liste</Link>
      <div className="page-header">
        <h1 className="page-title">{cours.intitule}</h1>
        <div className="actions">
          <Link to={`/cours/${cours.id}/modifier`} className="btn">Modifier</Link>
          <button onClick={supprimer} className="btn danger">Supprimer</button>
        </div>
      </div>
      {erreurSuppression && <p className="erreur">{erreurSuppression}</p>}

      <dl className="caracteristiques">
        <div><dt>Niveau</dt><dd>{cours.niveauDifficulte ?? "—"}</dd></div>
        <div><dt>Durée</dt><dd>{cours.dureeHeures != null ? `${cours.dureeHeures} h` : "—"}</dd></div>
        <div><dt>Ordre dans le module</dt><dd>{cours.ordreDansModule ?? "—"}</dd></div>
      </dl>

      <div className="grille-relations">
        <Liste titre="Module" elements={cours.module} lien="/modules" />
        <Liste titre="Formateur" elements={cours.formateur} lien="/formateurs" />
        <Liste titre="Compétences" elements={cours.competences} lien="/competences" />
        <Liste titre="Technologies" elements={cours.technologies} lien="/technologies" />
        <Liste titre="Ressources" elements={cours.ressources} lien="/ressources" />
      </div>
    </main>
  );
}

const styles = {
  page: {},
};
