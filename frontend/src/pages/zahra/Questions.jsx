import { useState } from "react";
import client from "../../api/client";

const EXEMPLES = [
  "Quels sont les prérequis du module Interactivité et dynamisme ?",
  "Quels cours sont dans le Module HTML ?",
  "Quel est le niveau du cours Introduction HTML ?",
  "Quelles vidéos sont disponibles sur HTML ?",
  "Quel est le module qui suit Interactivité et dynamisme ?",
];

function afficherReponse(reponse) {
  if (reponse === null || reponse === undefined) return null;
  if (Array.isArray(reponse)) {
    if (reponse.length === 0) return <p className="empty-text">Aucun résultat.</p>;
    return (
      <ul className="tag-list">
        {reponse.map((r) => (
          <li key={r.id}><span className="tag" title={r.id}>{r.label ?? r.id}</span></li>
        ))}
      </ul>
    );
  }
  return <span className="badge badge-lg">{String(reponse)}</span>;
}

export default function Questions() {
  const [question, setQuestion] = useState("");
  const [resultat, setResultat] = useState(null);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState("");

  async function poser(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setChargement(true);
    setErreur("");
    setResultat(null);
    try {
      const res = await client.post("/questions", { question: question.trim() });
      setResultat(res.data);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Questions guidées</h1>
          <p className="page-subtitle">Modules, cours et ressources : posez une question en français.</p>
        </div>
      </div>

      <form onSubmit={poser} className="card search-bar" style={{ maxWidth: "760px" }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ex. Quels sont les prérequis du module Interactivité ?"
          style={{ flex: 1, minWidth: 0 }}
        />
        <button type="submit" className="btn btn-primary" disabled={chargement}>
          {chargement ? "Recherche..." : "Poser"}
        </button>
      </form>

      <div className="nlp-chips" style={{ margin: "0 0 18px", maxWidth: "760px" }}>
        {EXEMPLES.map((ex) => (
          <button key={ex} type="button" className="nlp-chip" onClick={() => setQuestion(ex)}>
            {ex}
          </button>
        ))}
      </div>

      {erreur && <p className="erreur">{erreur}</p>}

      {resultat && (
        <div className="card" style={{ maxWidth: "760px" }}>
          {resultat.message ? (
            <p className="doux" style={{ margin: 0 }}>{resultat.message}</p>
          ) : (
            <>
              <dl className="proprietes">
                <dt>Intention</dt>
                <dd><span className="badge">{resultat.intention}</span></dd>
                <dt>Mots de base (spaCy)</dt>
                <dd className="font-mono">{resultat.lemmes.join(", ")}</dd>
                {resultat.entite && (
                  <>
                    <dt>Élément reconnu</dt>
                    <dd>{resultat.entite.label} <span className="pastille">{resultat.entite.type}</span></dd>
                  </>
                )}
              </dl>
              <h2 className="card-title" style={{ marginTop: "18px" }}>Réponse</h2>
              {afficherReponse(resultat.reponse)}
            </>
          )}
        </div>
      )}
    </div>
  );
}
