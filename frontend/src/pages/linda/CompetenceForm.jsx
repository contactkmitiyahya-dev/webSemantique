import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import { ChoixMultiple } from "./commun";
import { messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

const VIDE = { id: "", intitule: "", type: "Competence", scoreMaturite: "", parents: [], equivalentes: [], technologies: [] };

/** Creation (/competences/nouvelle) et modification (/competences/:id/modifier). */
export default function CompetenceForm() {
  const { id } = useParams();
  const edition = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(VIDE);
  const [types, setTypes] = useState([]);
  const [competences, setCompetences] = useState([]);
  const [technologies, setTechnologies] = useState([]);
  const [erreur, setErreur] = useState("");
  const [enCours, setEnCours] = useState(false);

  useEffect(() => {
    api.get("/competences/types").then((res) => setTypes(res.data)).catch(() => {});
    api.get("/competences?taille=100")
      .then((res) => setCompetences(res.data.donnees.map((c) => ({ id: c.id, label: c.intitule }))))
      .catch(() => {});
    api.get("/technologies?taille=100").then((res) => setTechnologies(res.data.donnees)).catch(() => {});
    if (edition) {
      api.get(`/competences/${id}`)
        .then(({ data }) => setForm({
          id: data.id, intitule: data.intitule, type: data.type || "Competence",
          scoreMaturite: data.scoreMaturite ?? "",
          parents: data.parents.map((p) => p.id),
          equivalentes: data.equivalentes.map((e) => e.id),
          technologies: data.technologies.map((t) => t.id),
        }))
        .catch(() => navigate("/competences"));
    }
  }, [edition, id, navigate]);

  const set = (champ) => (e) => setForm({ ...form, [champ]: e.target.value });
  const setListe = (champ) => (valeurs) => setForm({ ...form, [champ]: valeurs });

  const soumettre = (e) => {
    e.preventDefault();
    setErreur(""); setEnCours(true);
    const payload = {
      ...form,
      id: form.id.trim() || null,
      scoreMaturite: form.scoreMaturite === "" ? null : Number(form.scoreMaturite),
    };
    const requete = edition ? api.put(`/competences/${id}`, payload) : api.post("/competences", payload);
    requete
      .then((res) => navigate(`/competences/${res.data.id}`))
      .catch((err) => { setErreur(messageErreur(err)); setEnCours(false); });
  };

  return (
    <div className="page-container page-narrow">
      <div className="back-link">
        <Link to={edition ? `/competences/${id}` : "/competences"} className="btn-sm btn-outline">← Retour</Link>
      </div>
      <div className="card form-card">
        <h1 className="page-title">{edition ? "Modifier la compétence" : "Nouvelle compétence"}</h1>
        {erreur && <div className="alert alert-error">{erreur}</div>}
        <form onSubmit={soumettre} className="form-grid">
          {!edition && (
            <div className="form-group form-full">
              <label className="form-label">Identifiant
                <span className="form-hint">Facultatif : généré depuis l'intitulé (ex. Comp_Tests_Unitaires)</span>
              </label>
              <input className="input font-mono" placeholder="Comp_Tests_Unitaires" value={form.id} onChange={set("id")} />
            </div>
          )}
          <div className="form-group form-full">
            <label className="form-label">Intitulé *</label>
            <input className="input" required value={form.intitule} onChange={set("intitule")} />
          </div>
          <div className="form-group">
            <label className="form-label">Type</label>
            <select className="input select" value={form.type} onChange={set("type")}>
              {types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Score de maturité<span className="form-hint">Entre 0 et 100</span></label>
            <input className="input" type="number" min="0" max="100" value={form.scoreMaturite} onChange={set("scoreMaturite")} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Sous-compétence de<span className="form-hint">Un cycle est refusé par l'API</span></label>
            <ChoixMultiple options={competences} valeurs={form.parents} onChange={setListe("parents")} exclure={[id]} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Équivalente à<span className="form-hint">Enregistrée dans les deux sens</span></label>
            <ChoixMultiple options={competences} valeurs={form.equivalentes} onChange={setListe("equivalentes")} exclure={[id]} />
          </div>
          <div className="form-group form-full">
            <label className="form-label">Technologies mobilisées</label>
            <ChoixMultiple options={technologies} valeurs={form.technologies} onChange={setListe("technologies")} />
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
