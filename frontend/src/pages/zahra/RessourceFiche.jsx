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
    return <div className="loader-wrap"><div className="loader" /></div>;
  }

  if (erreur) {
    return (
      <main style={styles.page}>
        <p className="erreur">{erreur}</p>
        <Link to="/ressources" className="retour">← Retour à la liste</Link>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <Link to="/ressources" className="retour">← Retour à la liste</Link>
      <div className="page-header">
        <h1 className="page-title">{ressource.label}</h1>
        <div className="actions">
          <Link to={`/ressources/${ressource.id}/modifier`} className="btn">Modifier</Link>
          <button onClick={supprimer} className="btn danger">Supprimer</button>
        </div>
      </div>
      {erreurSuppression && <p className="erreur">{erreurSuppression}</p>}

      <dl className="caracteristiques">
        <div><dt>Langue</dt><dd>{ressource.langue ?? "—"}</dd></div>
        {ressource.dureeMinutes && <div><dt>Durée</dt><dd>{ressource.dureeMinutes} min</dd></div>}
        {ressource.nombrePages && <div><dt>Pages</dt><dd>{ressource.nombrePages}</dd></div>}
        <div>
          <dt>Lien</dt>
          <dd><a href={ressource.urlRessource} target="_blank" rel="noreferrer">{ressource.urlRessource}</a></dd>
        </div>
      </dl>

      <div className="grille-relations">
        <Liste titre="Compétences ciblées" elements={ressource.competencesCiblees} lien="/competences" />
        <Liste titre="Utilisée par les cours" elements={ressource.utiliseeParCours} lien="/cours" />
      </div>
    </main>
  );
}

const styles = {
  page: {},
};
