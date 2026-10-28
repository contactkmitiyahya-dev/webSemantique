import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../../api/client";
import RelationSelect from "../../components/RelationSelect";

const PROFONDEUR_MAX = 5;

function ArbrePrerequis({ id, profondeur }) {
  const [donnees, setDonnees] = useState(null);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    client
      .get(`/modules/${id}`)
      .then((res) => setDonnees(res.data))
      .catch((e) => setErreur(e.message));
  }, [id]);

  if (erreur) return <li className="erreur">{id} : {erreur}</li>;
  if (!donnees) return <li>{id}...</li>;

  return (
    <li>
      <Link to={`/modules/${id}`}>{donnees.intitule}</Link>
      {donnees.prerequis.length > 0 && profondeur < PROFONDEUR_MAX && (
        <ul style={styles.arbre}>
          {donnees.prerequis.map((p) => (
            <ArbrePrerequis key={p.id} id={p.id} profondeur={profondeur + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function ModuleFiche() {
  const { id } = useParams();
  const [module, setModule] = useState(null);
  const [prerequisTous, setPrerequisTous] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [erreurSuppression, setErreurSuppression] = useState("");
  const navigate = useNavigate();
  const [rafraichir, setRafraichir] = useState(0);
  const [prerequisAjout, setPrerequisAjout] = useState("");
  const [erreurAjout, setErreurAjout] = useState("");

  async function ajouterPrerequis() {
    setErreurAjout("");
    try {
      await client.post(`/modules/${module.id}/prerequis`, { prerequisId: prerequisAjout });
      setPrerequisAjout("");
      setRafraichir((n) => n + 1);
    } catch (e) {
      setErreurAjout(e.message);
    }
  }

  async function supprimer() {
    if (!window.confirm(`Supprimer le module « ${module.intitule} » ?`)) return;
    try {
      await client.delete(`/modules/${module.id}`);
      navigate("/modules");
    } catch (e) {
      setErreurSuppression(e.message);
    }
  }

  useEffect(() => {
    setChargement(true);
    setErreur("");
    Promise.all([
      client.get(`/modules/${id}`),
      client.get(`/modules/${id}/prerequis`),
    ])
      .then(([detail, prerequis]) => {
        setModule(detail.data);
        setPrerequisTous(prerequis.data.prerequis);
      })
      .catch((e) => setErreur(e.message))
      .finally(() => setChargement(false));
  }, [id, rafraichir]);

  if (chargement) {
    return <div className="loader-wrap"><div className="loader" /></div>;
  }

  if (erreur) {
    return (
      <main style={styles.page}>
        <p className="erreur">{erreur}</p>
        <Link to="/modules" className="retour">← Retour à la liste</Link>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <Link to="/modules" className="retour">← Retour à la liste</Link>
      <div className="page-header">
        <h1 className="page-title">{module.intitule}</h1>
        <div className="actions">
          <Link to={`/modules/${module.id}/modifier`} className="btn">Modifier</Link>
          <button onClick={supprimer} className="btn danger">Supprimer</button>
        </div>
      </div>
      {erreurSuppression && <p className="erreur">{erreurSuppression}</p>}

      <dl className="caracteristiques">
        <div><dt>Niveau</dt><dd>{module.niveauDifficulte ?? "—"}</dd></div>
        <div><dt>Durée</dt><dd>{module.dureeHeures != null ? `${module.dureeHeures} h` : "—"}</dd></div>
        <div><dt>Cours</dt><dd>{module.cours.length}</dd></div>
        <div><dt>Prérequis (tous)</dt><dd>{prerequisTous.length}</dd></div>
      </dl>

      <div className="grille-relations">
        <div className="card">
          <h2 className="card-title">Cours</h2>
          {module.cours.length === 0 ? (
            <p className="empty-text">Aucun cours.</p>
          ) : (
            <ul className="tag-list">
              {module.cours.map((c) => (
                <li key={c.id}>
                  <Link to={`/cours/${c.id}`} className="tag tag-lien">{c.label}</Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="card-title">Arbre des prérequis</h2>
          {module.prerequis.length === 0 ? (
            <p className="empty-text">Aucun prérequis : module de départ.</p>
          ) : (
            <ul style={styles.arbre}>
              {module.prerequis.map((p) => (
                <ArbrePrerequis key={p.id} id={p.id} profondeur={1} />
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="card-title">Tous les prérequis (directs et indirects)</h2>
          {prerequisTous.length === 0 ? (
            <p className="empty-text">Aucun.</p>
          ) : (
            <ul className="tag-list">
              {prerequisTous.map((p) => (
                <li key={p.id}>
                  <Link to={`/modules/${p.id}`} className="tag tag-lien">{p.label}</Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="card-title">Ajouter un prérequis</h2>
          <div className="actions" style={{ alignItems: "flex-end" }}>
            <RelationSelect
              endpoint="/modules"
              valeur={prerequisAjout}
              onChange={setPrerequisAjout}
              label="Module prérequis"
            />
            <button className="btn btn-primary" onClick={ajouterPrerequis} disabled={!prerequisAjout}>
              Ajouter
            </button>
          </div>
          {erreurAjout && <p className="erreur" style={{ marginTop: "12px" }}>{erreurAjout}</p>}
        </div>
      </div>
    </main>
  );
}

const styles = {
  page: {},
  arbre: {
    listStyle: "none",
    margin: 0,
    paddingLeft: "16px",
    borderLeft: "2px solid var(--line-strong)",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
};
