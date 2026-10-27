import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../../api/client";
import "./yahya.css";

export default function CertificationForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    id: "", label: "", organisme_id: "", dureeValiditeAns: "",
  });
  const [erreur, setErreur]   = useState("");
  const [loading, setLoading] = useState(false);

  const set = (field) => (e) => setFormData({ ...formData, [field]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    setErreur(""); setLoading(true);
    const payload = {
      ...formData,
      dureeValiditeAns: formData.dureeValiditeAns ? parseInt(formData.dureeValiditeAns) : null,
    };
    api.post("/certifications", payload)
      .then(() => navigate("/certifications"))
      .catch((err) => {
        if (err.response?.status === 409) setErreur("Cet ID existe déjà.");
        else if (err.response?.status === 400) setErreur("ID invalide.");
        else setErreur("Erreur lors de la création.");
        setLoading(false);
      });
  };

  return (
    <div className="page-container page-narrow">
      <div className="back-link">
        <Link to="/certifications" className="btn-sm btn-outline">← Retour</Link>
      </div>
      <div className="card form-card">
        <h1 className="page-title">Nouvelle Certification</h1>
        {erreur && <div className="alert alert-error">{erreur}</div>}
        <form onSubmit={handleSubmit} className="form-grid">
          <div className="form-group form-full">
            <label className="form-label">Identifiant (ID) *<span className="form-hint">Ex: Cert_AWS_Solutions</span></label>
            <input className="input font-mono" placeholder="Cert_AWS_Solutions" required value={formData.id} onChange={set("id")} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Intitulé *</label>
            <input className="input" placeholder="Ex: AWS Solutions Architect" required value={formData.label} onChange={set("label")} />
          </div>
          <div className="form-group">
            <label className="form-label">ID Organisme *<span className="form-hint">Ex: Organisme_AWS</span></label>
            <input className="input font-mono" placeholder="Organisme_AWS" required value={formData.organisme_id} onChange={set("organisme_id")} />
          </div>
          <div className="form-group">
            <label className="form-label">Durée de validité (ans)</label>
            <input className="input" type="number" min="1" max="10" placeholder="Ex: 3" value={formData.dureeValiditeAns} onChange={set("dureeValiditeAns")} />
          </div>
          <div className="form-group form-full form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => navigate("/certifications")}>Annuler</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? "Création…" : "Créer"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
