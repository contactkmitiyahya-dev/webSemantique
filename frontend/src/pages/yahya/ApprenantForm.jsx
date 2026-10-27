import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../../api/client";
import "./yahya.css";

const NIVEAUX = ["Licence", "Master", "Doctorat", "BTS", "DUT", "Bac", "Autre"];

export default function ApprenantForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    id: "",
    nom: "",
    prenom: "",
    email: "",
    niveauEtudes: "Licence",
    dateNaissance: "2000-01-01T00:00:00",
  });
  const [erreur, setErreur]   = useState("");
  const [loading, setLoading] = useState(false);

  const set = (field) => (e) => setFormData({ ...formData, [field]: e.target.value });

  // Auto-génération de l'ID depuis nom + prénom
  const autoId = () => {
    if (formData.nom && formData.prenom && !formData.id) {
      const id = `${formData.prenom}_${formData.nom}`
        .normalize("NFD").replace(/\p{Diacritic}/gu, "")
        .replace(/[^a-zA-Z0-9_]/g, "_")
        .replace(/^(.)/, (m) => m.toUpperCase());
      setFormData((prev) => ({ ...prev, id }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setErreur(""); setLoading(true);
    api.post("/apprenants", formData)
      .then(() => navigate("/apprenants"))
      .catch((err) => {
        if (err.response?.status === 409) setErreur("Cet ID existe déjà. Choisissez-en un autre.");
        else if (err.response?.status === 400) setErreur("ID invalide : doit commencer par une majuscule.");
        else setErreur("Erreur lors de la création.");
        setLoading(false);
      });
  };

  return (
    <div className="page-container page-narrow">
      <div className="back-link">
        <Link to="/apprenants" className="btn-sm btn-outline">← Retour</Link>
      </div>
      <div className="card form-card">
        <h1 className="page-title">Nouvel Apprenant</h1>
        {erreur && <div className="alert alert-error">{erreur}</div>}
        <form onSubmit={handleSubmit} className="form-grid">
          <div className="form-group">
            <label className="form-label">Prénom *</label>
            <input className="input" placeholder="Ex: Omar" required value={formData.prenom} onChange={set("prenom")} onBlur={autoId} />
          </div>
          <div className="form-group">
            <label className="form-label">Nom *</label>
            <input className="input" placeholder="Ex: Gharbi" required value={formData.nom} onChange={set("nom")} onBlur={autoId} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">
              Identifiant (ID) *
              <span className="form-hint">Commence par une majuscule, lettres/chiffres/underscore uniquement</span>
            </label>
            <input className="input font-mono" placeholder="Ex: Omar_Gharbi" required value={formData.id} onChange={set("id")} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Email *</label>
            <input className="input" type="email" placeholder="exemple@mail.com" required value={formData.email} onChange={set("email")} />
          </div>
          <div className="form-group">
            <label className="form-label">Niveau d'études *</label>
            <select className="input select" value={formData.niveauEtudes} onChange={set("niveauEtudes")}>
              {NIVEAUX.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Date de naissance *</label>
            <input className="input" type="date" value={formData.dateNaissance.slice(0, 10)} onChange={(e) => setFormData({ ...formData, dateNaissance: e.target.value + "T00:00:00" })} />
          </div>
          <div className="form-group form-full form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => navigate("/apprenants")}>Annuler</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Création…" : "Créer l'apprenant"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
