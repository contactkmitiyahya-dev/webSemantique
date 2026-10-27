import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../../api/client";
import "./yahya.css";

export default function CertificationFiche() {
  const { id }                   = useParams();
  const navigate                 = useNavigate();
  const [cert, setCert]          = useState(null);
  const [apprenantId, setApprenantId] = useState("");
  const [erreur, setErreur]       = useState("");
  const [succes, setSucces]       = useState("");
  const [loading, setLoading]     = useState(true);

  const charger = () => {
    setLoading(true);
    api.get(`/certifications/${id}`)
      .then((res) => {
        setCert(res.data);
        setLoading(false);
      })
      .catch(() => {
        navigate("/certifications");
      });
  };

  useEffect(() => {
    charger();
  }, [id]);

  const handleAttribution = (e) => {
    e.preventDefault();
    setErreur("");
    setSucces("");

    api.post("/certifications/attribution", {
      apprenant_id: apprenantId.trim(),
      certification_id: id,
    })
      .then(() => {
        setSucces("Certification attribuée avec succès !");
        setApprenantId("");
        charger();
      })
      .catch((err) => {
        if (err.response?.status === 404) {
          setErreur(err.response.data.detail || "Ressource introuvable. Vérifiez l'ID de l'apprenant.");
        } else if (err.response?.status === 400) {
          setErreur("Format d'identifiant invalide.");
        } else {
          setErreur("Erreur lors de l'attribution.");
        }
      });
  };

  const handleSupprimer = () => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer la certification "${cert.label}" ?`)) {
      api.delete(`/certifications/${id}`)
        .then(() => navigate("/certifications"))
        .catch(() => setErreur("Erreur lors de la suppression."));
    }
  };

  if (loading) return <div className="loader-wrap"><div className="loader" /></div>;
  if (!cert) return null;

  return (
    <div className="page-container">
      <div className="back-link">
        <Link to="/certifications" className="btn-sm btn-outline">← Retour aux certifications</Link>
      </div>

      <div className="fiche-grid">
        {/* Carte principale */}
        <div className="card profile-card">
          <div className="avatar">🏆</div>
          <h1 className="fiche-name">{cert.label}</h1>
          <span className="badge badge-lg font-mono">{cert.id}</span>

          <div className="info-list">
            <div className="info-row">
              <span className="info-label">📋 Organisme</span>
              <span>{cert.organisme || "Non spécifié"}</span>
            </div>
            <div className="info-row">
              <span className="info-label">⏳ Validité</span>
              <span>
                {cert.dureeValiditeAns
                  ? `${cert.dureeValiditeAns} an${cert.dureeValiditeAns > 1 ? "s" : ""}`
                  : "Illimitée / Non spécifiée"}
              </span>
            </div>
            <div className="info-row">
              <span className="info-label">👥 Apprenants certifiés</span>
              <span>{cert.apprenants?.length || 0}</span>
            </div>
          </div>

          <div style={{ marginTop: "1.5rem" }}>
            <button onClick={handleSupprimer} className="btn btn-danger" style={{ width: "100%" }}>
              Supprimer la certification
            </button>
          </div>
        </div>

        {/* Colonne droite : Apprenants certifiés & Attribution */}
        <div className="relations-col">
          {/* Liste des apprenants certifiés */}
          <div className="card">
            <h3 className="card-title">
              🎓 Apprenants ayant obtenu cette certification
              <span className="count-badge">{cert.apprenants?.length || 0}</span>
            </h3>

            {!cert.apprenants || cert.apprenants.length === 0 ? (
              <p className="empty-text">Aucun apprenant n'a encore obtenu cette certification.</p>
            ) : (
              <div className="apprenants-cert-list" style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {cert.apprenants.map((app) => (
                  <div
                    key={app.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "0.6rem 0.8rem",
                      background: "var(--surface2)",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <div>
                      <strong>{app.prenom} {app.nom}</strong>
                      <span className="font-mono text-muted" style={{ marginLeft: "0.5rem", fontSize: "0.8rem" }}>
                        ({app.id})
                      </span>
                    </div>
                    <Link to={`/apprenants/${app.id}`} className="btn-sm btn-outline">
                      Voir la fiche
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Formulaire d'attribution */}
          <div className="card">
            <h3 className="card-title">➕ Attribuer à un apprenant</h3>
            {erreur && <div className="alert alert-error">{erreur}</div>}
            {succes && <div className="alert alert-success">{succes}</div>}

            <form onSubmit={handleAttribution} className="inline-form">
              <input
                type="text"
                placeholder="ID apprenant (ex: Apprenant_Yahya)"
                value={apprenantId}
                onChange={(e) => setApprenantId(e.target.value)}
                required
                className="input font-mono"
              />
              <button type="submit" className="btn btn-primary">
                Attribuer
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
