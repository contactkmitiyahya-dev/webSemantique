import { useState } from "react";
import api from "../api/client";
import "./components.css";

/**
 * Barre de question en langage naturel, en haut de l'application.
 * Affiche la reponse (tableau), les entites reconnues et la requete SPARQL generee.
 */
export default function QuestionBar() {
  const [question, setQuestion] = useState("");
  const [reponse, setReponse]   = useState(null);
  const [erreur, setErreur]     = useState("");
  const [enCours, setEnCours]   = useState(false);
  const [voirSparql, setVoirSparql] = useState(false);

  const poser = (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setEnCours(true); setErreur("");
    api.post("/nlp/question", { question })
      .then((res) => setReponse(res.data))
      .catch((err) => setErreur(err.response?.data?.detail || "L'API ne répond pas (port 8000)."))
      .finally(() => setEnCours(false));
  };

  const fermer = () => { setReponse(null); setErreur(""); };
  const resultats = reponse?.resultats || [];
  const colonnes = resultats.length ? Object.keys(resultats[0]) : [];
  const entites = Object.entries(reponse?.entites || {});
  const echec = reponse && (reponse.intention === "INCONNUE" || !reponse.sparql);

  return (
    <div className="qbar">
      <form className="qbar-form" onSubmit={poser}>
        <span className="qbar-icone">💬</span>
        <input
          className="qbar-input"
          placeholder="Posez une question… ex. Quelles sont les sous-compétences de Programmation Web ?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" disabled={enCours}>{enCours ? "…" : "Demander"}</button>
      </form>

      {(reponse || erreur) && (
        <div className="qbar-panneau">
          <button type="button" className="modal-fermer qbar-fermer" onClick={fermer} aria-label="Fermer">×</button>
          {erreur && <div className="alert alert-error">{erreur}</div>}
          {reponse && (
            <>
              <div className="qbar-meta">
                <span className="badge">{reponse.intention}</span>
                {/* Linda : {rôle: "libellé -> uri"} ; Ala, Imem, Yahya : liste de {texte, uri, type} */}
                {entites.map(([role, valeur]) => (
                  typeof valeur === "object"
                    ? <span key={role} className="tag tag-green"><strong>{valeur.type}</strong> : {valeur.texte} → {valeur.uri}</span>
                    : <span key={role} className="tag tag-green"><strong>{role}</strong> : {valeur}</span>
                ))}
                {reponse.sparql && (
                  <button type="button" className="btn-sm btn-outline" onClick={() => setVoirSparql(!voirSparql)}>
                    {voirSparql ? "Masquer" : "Voir"} la requête SPARQL
                  </button>
                )}
                {!echec && <span className="qbar-compte">{resultats.length} résultat{resultats.length !== 1 ? "s" : ""}</span>}
              </div>

              {voirSparql && reponse.sparql && <pre className="nlp-code-box qbar-sparql">{reponse.sparql}</pre>}

              {echec ? (
                <div className="alert alert-warning">{reponse.message}</div>
              ) : resultats.length === 0 ? (
                <p className="empty-text">La requête n'a renvoyé aucun résultat.</p>
              ) : (
                <div className="qbar-resultats">
                  <table className="nlp-results-table">
                    <thead><tr>{colonnes.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                    <tbody>
                      {resultats.map((r, i) => (
                        <tr key={i}>{colonnes.map((c) => <td key={c}>{r[c]}</td>)}</tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
