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

  if (erreur) return <li style={styles.erreur}>{id} : {erreur}</li>;
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
    return <main style={styles.page}><p>Chargement...</p></main>;
  }

  if (erreur) {
    return (
      <main style={styles.page}>
        <p style={styles.erreur}>{erreur}</p>
        <Link to="/modules">Retour à la liste</Link>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <Link to="/modules">← Retour à la liste</Link>
      <h1>{module.intitule}</h1>
      <Link to={`/modules/${module.id}/modifier`}>Modifier ce module</Link>
      <button onClick={supprimer} style={{ marginLeft: "16px", color: "#e53e3e" }}>
        Supprimer
      </button>
      {erreurSuppression && <p style={styles.erreur}>{erreurSuppression}</p>}
      <p>
        Niveau : {module.niveauDifficulte} · Durée : {module.dureeHeures} h
      </p>

      <h2>Cours</h2>
      {module.cours.length === 0 ? (
        <p>Aucun cours.</p>
      ) : (
        <ul>
          {module.cours.map((c) => (
            <li key={c.id}>{c.label}</li>
          ))}
        </ul>
      )}

      <h2>Arbre des prérequis</h2>
      {module.prerequis.length === 0 ? (
        <p>Aucun prérequis : module de départ.</p>
      ) : (
        <ul style={styles.arbre}>
          {module.prerequis.map((p) => (
            <ArbrePrerequis key={p.id} id={p.id} profondeur={1} />
          ))}
        </ul>
      )}

      <h2>Ajouter un prérequis</h2>
      <div style={{ display: "flex", gap: "8px", alignItems: "flex-end" }}>
        <RelationSelect
          endpoint="/modules"
          valeur={prerequisAjout}
          onChange={setPrerequisAjout}
          label="Module prérequis"
        />
        <button onClick={ajouterPrerequis} disabled={!prerequisAjout}>
          Ajouter
        </button>
      </div>
      {erreurAjout && <p style={styles.erreur}>{erreurAjout}</p>}

      <h2>Tous les prérequis (directs et indirects)</h2>
      {prerequisTous.length === 0 ? (
        <p>Aucun.</p>
      ) : (
        <ul>
          {prerequisTous.map((p) => (
            <li key={p.id}>
              <Link to={`/modules/${p.id}`}>{p.label}</Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

const styles = {
  page: { padding: "24px", fontFamily: "sans-serif" },
  erreur: { color: "#e53e3e" },
  arbre: {
    listStyle: "none",
    paddingLeft: "20px",
    borderLeft: "2px solid #ddd",
    marginLeft: "8px",
  },
};
