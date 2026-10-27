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
    if (reponse.length === 0) return <p>Aucun résultat.</p>;
    return (
      <ul>
        {reponse.map((r) => (
          <li key={r.id}>{r.label ?? r.id}</li>
        ))}
      </ul>
    );
  }
  return <p>{String(reponse)}</p>;
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
    <main style={styles.page}>
      <h1>Poser une question</h1>

      <form onSubmit={poser} style={styles.form}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ex. Quels sont les prérequis du module Interactivité ?"
          style={styles.input}
        />
        <button type="submit" disabled={chargement}>
          {chargement ? "Recherche..." : "Poser"}
        </button>
      </form>

      <div style={styles.exemples}>
        {EXEMPLES.map((ex) => (
          <button key={ex} type="button" onClick={() => setQuestion(ex)} style={styles.exemple}>
            {ex}
          </button>
        ))}
      </div>

      {erreur && <p style={styles.erreur}>{erreur}</p>}

      {resultat && (
        <section style={styles.resultat}>
          {resultat.message ? (
            <p>{resultat.message}</p>
          ) : (
            <>
              <p>
                <strong>Intention :</strong> {resultat.intention}
              </p>
              <p>
                <strong>Mots de base (spaCy) :</strong> {resultat.lemmes.join(", ")}
              </p>
              {resultat.entite && (
                <p>
                  <strong>Élément reconnu :</strong> {resultat.entite.label} ({resultat.entite.type})
                </p>
              )}
              <h2>Réponse</h2>
              {afficherReponse(resultat.reponse)}
            </>
          )}
        </section>
      )}
    </main>
  );
}

const styles = {
  page: { padding: "24px", fontFamily: "sans-serif" },
  form: { display: "flex", gap: "8px", maxWidth: "720px" },
  input: { flex: 1, padding: "8px", fontSize: "14px", borderRadius: "6px", border: "1px solid #ccc" },
  exemples: { display: "flex", flexWrap: "wrap", gap: "8px", margin: "16px 0" },
  exemple: {
    padding: "6px 10px",
    fontSize: "13px",
    borderRadius: "6px",
    border: "1px solid #bbb",
    background: "#fff",
    cursor: "pointer",
  },
  resultat: { marginTop: "16px", padding: "16px", background: "#f5f7fa", borderRadius: "8px", maxWidth: "720px" },
  erreur: { color: "#e53e3e" },
};
