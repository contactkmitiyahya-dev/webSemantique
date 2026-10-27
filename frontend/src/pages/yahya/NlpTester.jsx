import { useState, useEffect } from "react";
import api from "../../api/client";
import "./yahya.css";

const EXEMPLES_DEFAUT = [
  "Quels sont les apprenants de niveau Master ?",
  "Quelles sont les compétences de Omar ?",
  "À quelles formations est inscrit Ahmed ?",
  "Qui est inscrit à la Formation Full-Stack ?",
  "Combien y a-t-il d'apprenants en tout ?",
  "Quelles certifications a obtenu Lina ?",
  "Quels modules sont requis pour le Certificat Développeur Front-end ?",
  "Qui sont les coéquipiers de Nour ?"
];

export default function NlpTester() {
  const [question, setQuestion]     = useState("");
  const [exemples, setExemples]     = useState(EXEMPLES_DEFAUT);
  const [loading, setLoading]       = useState(false);
  const [reponse, setReponse]       = useState(null);
  const [erreur, setErreur]         = useState("");
  const [copie, setCopie]           = useState(false);
  const [vueJson, setVueJson]       = useState(false);

  useEffect(() => {
    // Tenter de charger les exemples types depuis le backend
    api.get("/nlp/exemples")
      .then((res) => {
        if (Array.isArray(res.data) && res.data.length > 0) {
          setExemples(res.data.map(item => item.question));
        }
      })
      .catch(() => {
        // En cas d'erreur réseau, on garde les exemples par défaut
      });
  }, []);

  const handleDemander = (qTexte) => {
    const qAEnvoyer = (typeof qTexte === "string" ? qTexte : question).trim();
    if (!qAEnvoyer) return;

    setQuestion(qAEnvoyer);
    setLoading(true);
    setErreur("");
    setReponse(null);

    api.post("/nlp/question", { question: qAEnvoyer })
      .then((res) => {
        setReponse(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setErreur(
          err.response?.data?.detail ||
          "Erreur lors de l'appel au service NLP. Vérifiez que le backend FastAPI est actif."
        );
        setLoading(false);
      });
  };

  const copierSparql = () => {
    if (reponse?.sparql) {
      navigator.clipboard.writeText(reponse.sparql);
      setCopie(true);
      setTimeout(() => setCopie(false), 2000);
    }
  };

  return (
    <div className="page-container">
      <div className="nlp-header">
        <h1 className="page-title">Module NLP &amp; Questions SPARQL</h1>
        <p className="page-subtitle">
          Interrogez l'ontologie en langage naturel français — conversion automatique en requêtes SPARQL
        </p>
      </div>

      {/* Exemples de questions types */}
      <div className="card nlp-examples-wrap">
        <div className="nlp-examples-title">💡 Questions types recommandées (cliquez pour tester) :</div>
        <div className="nlp-chips">
          {exemples.map((ex, index) => (
            <button
              key={index}
              type="button"
              className="nlp-chip"
              onClick={() => handleDemander(ex)}
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Formulaire de saisie de question */}
      <div className="card">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleDemander();
          }}
          className="search-bar"
          style={{ marginBottom: 0 }}
        >
          <input
            type="text"
            className="input"
            placeholder="Posez votre question en français (ex: Quels sont les apprenants de niveau Master ?)"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !question.trim()}
          >
            {loading ? "Traitement..." : "Demander 🚀"}
          </button>
        </form>
      </div>

      {/* Message d'erreur */}
      {erreur && (
        <div className="alert alert-error" style={{ marginTop: "1rem" }}>
          ⚠️ {erreur}
        </div>
      )}

      {/* Chargement */}
      {loading && (
        <div className="loader-wrap">
          <div className="loader" />
        </div>
      )}

      {/* Affichage des résultats */}
      {reponse && !loading && (
        <div className="nlp-card">
          {/* 1. Intention détectée */}
          <div style={{ marginBottom: "1.5rem" }}>
            <h3 className="card-title">
              🎯 Intention détectée
              <span className="badge badge-lg font-mono">{reponse.intention}</span>
              {reponse.source && (
                <span className={`nlp-source-badge ${reponse.source === "fuseki" ? "nlp-source-fuseki" : "nlp-source-simu"}`}>
                  Source : {reponse.source === "fuseki" ? "Fuseki (En direct)" : "Résultats simulés"}
                </span>
              )}
            </h3>

            {/* Entités identifiées */}
            {reponse.entites && Object.keys(reponse.entites).length > 0 && (
              <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
                <span className="info-label" style={{ alignSelf: "center" }}>Entités extraites :</span>
                {/* Format commun : liste de {texte, uri, type} ; ancien format : {cle: valeur} */}
                {Object.entries(reponse.entites).map(([k, v]) => (
                  <span key={k} className="tag tag-green">
                    {typeof v === "object"
                      ? <><strong>{v.type}</strong>: {v.texte} → {v.uri}</>
                      : <><strong>{k}</strong>: {v}</>}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* 2. Requête SPARQL générée (En vert sur fond noir) */}
          <div style={{ marginBottom: "1.5rem" }}>
            <div className="nlp-code-header">
              <h3 className="card-title" style={{ margin: 0 }}>
                ⚡ Requête SPARQL générée
              </h3>
              <button
                type="button"
                onClick={copierSparql}
                className="btn-sm btn-outline"
                style={{ fontSize: "0.75rem" }}
              >
                {copie ? "✓ Copié !" : "📋 Copier SPARQL"}
              </button>
            </div>
            <pre className="nlp-code-box">
              <code>{reponse.sparql}</code>
            </pre>
          </div>

          {/* 3. Résultats */}
          <div>
            <div className="nlp-code-header">
              <h3 className="card-title" style={{ margin: 0 }}>
                📊 Résultats retournés
                {Array.isArray(reponse.resultats) && (
                  <span className="count-badge">{reponse.resultats.length} ligne(s)</span>
                )}
              </h3>
              <button
                type="button"
                onClick={() => setVueJson(!vueJson)}
                className="btn-sm btn-outline"
                style={{ fontSize: "0.75rem" }}
              >
                {vueJson ? "Vue Tableau" : "Vue JSON brut"}
              </button>
            </div>

            {vueJson ? (
              <pre className="nlp-code-box" style={{ color: "#38bdf8", marginTop: "0.5rem" }}>
                <code>{JSON.stringify(reponse.resultats, null, 2)}</code>
              </pre>
            ) : Array.isArray(reponse.resultats) && reponse.resultats.length > 0 ? (
              <div style={{ overflowX: "auto" }}>
                <table className="nlp-results-table">
                  <thead>
                    <tr>
                      {Object.keys(reponse.resultats[0]).map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {reponse.resultats.map((row, rIndex) => (
                      <tr key={rIndex}>
                        {Object.values(row).map((val, cIndex) => (
                          <td key={cIndex} className="font-mono">
                            {typeof val === "object" ? JSON.stringify(val) : String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="empty-text">Aucun résultat retourné.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
