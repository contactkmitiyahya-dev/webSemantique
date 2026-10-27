import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import { ChoixMultiple } from "./commun";
import { messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

const VIDE = { id: "", label: "", type: "Technologie", competences: [] };

/** Creation (/technologies/nouvelle) et modification (/technologies/:id/modifier). */
export default function TechnologieForm() {
  const { id } = useParams();
  const edition = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(VIDE);
  const [types, setTypes] = useState([]);
  const [competences, setCompetences] = useState([]);
  const [erreur, setErreur] = useState("");
  const [enCours, setEnCours] = useState(false);

  useEffect(() => {
    api.get("/technologies/types").then((res) => setTypes(res.data)).catch(() => {});
    api.get("/competences?taille=100")
      .then((res) => setCompetences(res.data.donnees.map((c) => ({ id: c.id, label: c.intitule }))))
      .catch(() => {});
    if (edition) {
      api.get(`/technologies/${id}`)
        .then(({ data }) => setForm({
          id: data.id, label: data.label, type: data.type || "Technologie",
          competences: data.competences.map((c) => c.id),
        }))
        .catch(() => navigate("/technologies"));
    }
  }, [edition, id, navigate]);

  const set = (champ) => (e) => setForm({ ...form, [champ]: e.target.value });

  const soumettre = (e) => {
    e.preventDefault();
    setErreur(""); setEnCours(true);
    const payload = { ...form, id: form.id.trim() || null };
    const requete = edition ? api.put(`/technologies/${id}`, payload) : api.post("/technologies", payload);
    requete
      .then((res) => navigate(`/technologies/${res.data.id}`))
      .catch((err) => { setErreur(messageErreur(err)); setEnCours(false); });
  };

  return (
    <div className="page-container page-narrow">
      <div className="back-link">
        <Link to={edition ? `/technologies/${id}` : "/technologies"} className="btn-sm btn-outline">← Retour</Link>
      </div>
      <div className="card form-card">
        <h1 className="page-title">{edition ? "Modifier la technologie" : "Nouvelle technologie"}</h1>
        {erreur && <div className="alert alert-error">{erreur}</div>}
        <form onSubmit={soumettre} className="form-grid">
          {!edition && (
            <div className="form-group form-full">
              <label className="form-label">Identifiant
                <span className="form-hint">Facultatif : généré depuis le libellé (ex. Tech_Svelte)</span>
              </label>
              <input className="input font-mono" placeholder="Tech_Svelte" value={form.id} onChange={set("id")} />
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Libellé *</label>
            <input className="input" required value={form.label} onChange={set("label")} />
          </div>
          <div className="form-group">
            <label className="form-label">Type</label>
            <select className="input select" value={form.type} onChange={set("type")}>
              {types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </div>
          <div className="form-group form-full">
            <label className="form-label">Compétences qui la mobilisent</label>
            <ChoixMultiple options={competences} valeurs={form.competences} onChange={(v) => setForm({ ...form, competences: v })} />
          </div>
          <div className="form-group form-full form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>Annuler</button>
            <button type="submit" className="btn btn-primary" disabled={enCours}>
              {enCours ? "Enregistrement…" : edition ? "Enregistrer" : "Créer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
