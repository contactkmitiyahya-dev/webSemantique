import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../../api/client";
import "./yahya.css";

export default function ApprenantFiche() {
  const { id }           = useParams();
  const navigate         = useNavigate();
  const [apprenant, setApprenant] = useState(null);
  const [formationId, setFormationId] = useState("");
  const [erreur, setErreur]           = useState("");
  const [succes, setSucces]           = useState("");
  const [loading, setLoading]         = useState(true);

  const charger = () => {
    setLoading(true);
    api.get(`/apprenants/${id}`)
      .then((res) => { setApprenant(res.data); setLoading(false); })
      .catch(() => navigate("/apprenants"));
  };

  useEffect(() => { charger(); }, [id]);

  const calculerAge = (dateNaissance) => {
    if (!dateNaissance) return "Inconnu";
    const diff = Date.now() - new Date(dateNaissance).getTime();
    return Math.floor(diff / (365.25 * 24 * 3600 * 1000)) + " ans";
  };

  const handleInscription = (e) => {
    e.preventDefault();
    setErreur(""); setSucces("");
    api.post(`/apprenants/${id}/inscription`, { formation_id: formationId })
      .then(() => {
        setSucces("Inscription réussie !");
        setFormationId("");
        charger();
      })
      .catch((err) => {
        if (err.response?.status === 409)
          setErreur("Limite de 3 inscriptions simultanées atteinte pour cet apprenant.");
        else if (err.response?.status === 404)
          setErreur("Formation introuvable. Vérifiez l'identifiant.");
        else
          setErreur("Erreur lors de l'inscription.");
      });
  };

  if (loading) return <div className="loader-wrap"><div className="loader" /></div>;
  if (!apprenant) return null;

  const nbFormations = apprenant.relations.formations.length;

  return (
    <div className="page-container">
      <div className="back-link">
        <Link to="/apprenants" className="btn-sm btn-outline">← Retour</Link>
      </div>

      <div className="fiche-grid">
        {/* Carte principale */}
        <div className="card profile-card">
          <div className="avatar">{apprenant.prenom[0]}{apprenant.nom[0]}</div>
          <h1 className="fiche-name">{apprenant.prenom} {apprenant.nom}</h1>
          <span className="badge badge-lg">{apprenant.niveau}</span>
          <div className="info-list">
            <div className="info-row"><span className="info-label">📧 Email</span><span>{apprenant.email}</span></div>
            <div className="info-row"><span className="info-label">🎂 Âge</span><span>{calculerAge(apprenant.dateNaissance)}</span></div>
            <div className="info-row"><span className="info-label">📅 Naissance</span><span>{new Date(apprenant.dateNaissance).toLocaleDateString("fr-FR")}</span></div>
          </div>
        </div>

        {/* Relations */}
        <div className="relations-col">
          <div className="card">
            <h3 className="card-title">
              🎓 Formations
              <span className={`count-badge ${nbFormations >= 3 ? "count-full" : ""}`}>{nbFormations}/3</span>
            </h3>
            {apprenant.relations.formations.length === 0 ? (
              <p className="empty-text">Aucune formation</p>
            ) : (
              <ul className="tag-list">
                {apprenant.relations.formations.map((f, i) => <li key={i} className="tag">{f.label}</li>)}
              </ul>
            )}
          </div>

          <div className="card">
            <h3 className="card-title">💡 Compétences</h3>
            {apprenant.relations.competences.length === 0 ? (
              <p className="empty-text">Aucune compétence</p>
            ) : (
              <ul className="tag-list">
                {apprenant.relations.competences.map((c, i) => <li key={i} className="tag tag-green">{c.label}</li>)}
              </ul>
            )}
          </div>

          <div className="card">
            <h3 className="card-title">🏆 Certifications</h3>
            {apprenant.relations.certifications.length === 0 ? (
              <p className="empty-text">Aucune certification</p>
            ) : (
              <ul className="tag-list">
                {apprenant.relations.certifications.map((c, i) => <li key={i} className="tag tag-gold">{c.label}</li>)}
              </ul>
            )}
          </div>

          {/* Formulaire d'inscription */}
          <div className="card">
            <h3 className="card-title">➕ Inscrire à une formation</h3>
            {nbFormations >= 3 && (
              <div className="alert alert-warning">⚠️ Limite de 3 inscriptions atteinte</div>
            )}
            {erreur  && <div className="alert alert-error">{erreur}</div>}
            {succes  && <div className="alert alert-success">{succes}</div>}
            <form onSubmit={handleInscription} className="inline-form">
              <input
                type="text"
                placeholder="ID formation (ex: Formation_FullStack)"
                value={formationId}
                onChange={(e) => setFormationId(e.target.value)}
                required
                disabled={nbFormations >= 3}
                className="input"
              />
              <button type="submit" className="btn btn-primary" disabled={nbFormations >= 3}>
                Inscrire
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
