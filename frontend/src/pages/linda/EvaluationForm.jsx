import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import { ChoixMultiple } from "./commun";
import { messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

const VIDE = {
  id: "", label: "", type: "QuizEnLigne", dateEvaluation: "", noteMinimale: "10", coefficient: "1",
  competences: [], modules: [], cours: [],
};

/** Creation (/evaluations/nouvelle) et modification (/evaluations/:id/modifier). */
export default function EvaluationForm() {
  const { id } = useParams();
  const edition = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(VIDE);
  const [options, setOptions] = useState({ types: [], competences: [], modules: [], cours: [] });
  const [erreur, setErreur] = useState("");
  const [enCours, setEnCours] = useState(false);

  useEffect(() => {
    api.get("/evaluations/options").then((res) => setOptions(res.data)).catch(() => {});
    if (edition) {
      api.get(`/evaluations/${id}`)
        .then(({ data }) => setForm({
          id: data.id, label: data.label, type: data.type,
          dateEvaluation: (data.dateEvaluation || "").slice(0, 10),
          noteMinimale: String(data.noteMinimale ?? ""), coefficient: String(data.coefficient ?? ""),
          competences: data.competences.map((c) => c.id),
          modules: data.modules.map((m) => m.id),
          cours: data.cours.map((c) => c.id),
        }))
        .catch(() => navigate("/evaluations"));
    }
  }, [edition, id, navigate]);

  const set = (champ) => (e) => setForm({ ...form, [champ]: e.target.value });
  const setListe = (champ) => (valeurs) => setForm({ ...form, [champ]: valeurs });

  const soumettre = (e) => {
    e.preventDefault();
    // Controle cote client ; l'API refait les memes controles (400)
    if (form.competences.length === 0) return setErreur("Choisissez au moins une compétence.");
    if (form.modules.length === 0) return setErreur("Choisissez au moins un module.");
    setErreur(""); setEnCours(true);
    const payload = {
      ...form,
      id: form.id.trim() || null,
      dateEvaluation: `${form.dateEvaluation}T00:00:00`,
      noteMinimale: Number(form.noteMinimale),
      coefficient: Number(form.coefficient),
    };
    const requete = edition ? api.put(`/evaluations/${id}`, payload) : api.post("/evaluations", payload);
    requete
      .then((res) => navigate(`/evaluations/${res.data.id}`))
      .catch((err) => { setErreur(messageErreur(err)); setEnCours(false); });
  };

  return (
    <div className="page-container page-narrow">
      <div className="back-link">
        <Link to={edition ? `/evaluations/${id}` : "/evaluations"} className="btn-sm btn-outline">← Retour</Link>
      </div>
      <div className="card form-card">
        <h1 className="page-title">{edition ? "Modifier l'évaluation" : "Nouvelle évaluation"}</h1>
        {erreur && <div className="alert alert-error">{erreur}</div>}
        <form onSubmit={soumettre} className="form-grid">
          {!edition && (
            <div className="form-group form-full">
              <label className="form-label">Identifiant
                <span className="form-hint">Facultatif : généré depuis le libellé (ex. Eval_Quiz_Vue)</span>
              </label>
              <input className="input font-mono" placeholder="Eval_Quiz_Vue" value={form.id} onChange={set("id")} />
            </div>
          )}
          <div className="form-group form-full">
            <label className="form-label">Libellé *</label>
            <input className="input" required value={form.label} onChange={set("label")} />
          </div>
          <div className="form-group">
            <label className="form-label">Type *</label>
            <select className="input select" value={form.type} onChange={set("type")}>
              {options.types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Date *</label>
            <input className="input" type="date" required value={form.dateEvaluation} onChange={set("dateEvaluation")} />
          </div>
          <div className="form-group">
            <label className="form-label">Note minimale *<span className="form-hint">Entre 0 et 20</span></label>
            <input className="input" type="number" step="0.5" min="0" max="20" required value={form.noteMinimale} onChange={set("noteMinimale")} />
          </div>
          <div className="form-group">
            <label className="form-label">Coefficient *<span className="form-hint">Strictement positif</span></label>
            <input className="input" type="number" step="0.5" min="0.5" required value={form.coefficient} onChange={set("coefficient")} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Compétences évaluées *<span className="form-hint">Au moins une</span></label>
            <ChoixMultiple options={options.competences} valeurs={form.competences} onChange={setListe("competences")} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Module(s) *<span className="form-hint">Au moins un</span></label>
            <ChoixMultiple options={options.modules} valeurs={form.modules} onChange={setListe("modules")} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Cours évalués</label>
            <ChoixMultiple options={options.cours} valeurs={form.cours} onChange={setListe("cours")} />
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
