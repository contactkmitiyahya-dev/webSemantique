import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import ConfirmDialog from "../../components/ConfirmDialog";
import FormModal from "../../components/FormModal";
import Notification from "../../components/Notification";
import ArbreCompetences, { Jauge } from "./ArbreCompetences";
import { ListeTags } from "./commun";
import { messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

const SOUS_VIDE = { intitule: "", type: "", scoreMaturite: "" };

export default function CompetenceFiche() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [comp, setComp] = useState(null);
  const [arbre, setArbre] = useState([]);
  const [types, setTypes] = useState([]);
  const [confirmer, setConfirmer] = useState(false);
  const [modal, setModal] = useState(false);
  const [sous, setSous] = useState(SOUS_VIDE);
  const [erreurModal, setErreurModal] = useState("");
  const [enCours, setEnCours] = useState(false);
  const [notif, setNotif] = useState(null);

  const charger = useCallback(() => {
    api.get(`/competences/${id}`)
      .then((res) => setComp(res.data))
      .catch(() => navigate("/competences"));
    api.get(`/competences/arbre?racine=${id}`).then((res) => setArbre(res.data)).catch(() => {});
  }, [id, navigate]);

  useEffect(() => { charger(); }, [charger]);
  useEffect(() => { api.get("/competences/types").then((res) => setTypes(res.data)).catch(() => {}); }, []);

  const supprimer = () => {
    setConfirmer(false);
    api.delete(`/competences/${id}`)
      .then(() => navigate("/competences"))
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }));
  };

  const creerSousCompetence = () => {
    setEnCours(true); setErreurModal("");
    const payload = {
      intitule: sous.intitule,
      type: sous.type || comp.type || "Competence",
      scoreMaturite: sous.scoreMaturite === "" ? null : Number(sous.scoreMaturite),
      parents: [id],
    };
    api.post("/competences", payload)
      .then((res) => {
        setModal(false); setSous(SOUS_VIDE);
        setNotif({ type: "succes", message: `Sous-compétence « ${res.data.intitule} » créée (${res.data.id}).` });
        charger();
      })
      .catch((err) => setErreurModal(messageErreur(err)))
      .finally(() => setEnCours(false));
  };

  if (!comp) return <div className="loader-wrap"><div className="loader" /></div>;

  return (
    <div className="page-container">
      <div className="back-link">
        <Link to="/competences" className="btn-sm btn-outline">← Retour</Link>
      </div>

      <div className="fiche-grid">
        <div className="card profile-card">
          <div className="avatar">🧠</div>
          <h1 className="fiche-name">{comp.intitule}</h1>
          <span className="badge">{comp.type}</span>
          <div className="info-list">
            <div className="info-row"><span className="info-label">Identifiant</span><span className="font-mono">{comp.id}</span></div>
            <div className="info-row"><span className="info-label">Maturité</span><Jauge valeur={comp.scoreMaturite} /></div>
            <div className="info-row"><span className="info-label">Apprenants</span><span>{comp.apprenants.length}</span></div>
            <div className="info-row"><span className="info-label">Évaluations</span><span>{comp.evaluations.length}</span></div>
          </div>
          <div className="fiche-actions">
            <Link to={`/competences/${id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
            <button className="btn-sm btn-outline" onClick={() => setModal(true)}>+ Sous-compétence</button>
            <button className="btn-sm btn-danger" onClick={() => setConfirmer(true)}>Supprimer</button>
          </div>
        </div>

        <div className="relations-col">
          <div className="card">
            {comp.ancetres.length > 0 && (
              <p className="fil-ariane">
                Fait partie de :{" "}
                {comp.ancetres.map((a, i) => (
                  <span key={a.id}>{i > 0 && " · "}<Link to={`/competences/${a.id}`}>{a.label}</Link></span>
                ))}
              </p>
            )}
            <h2 className="card-title">🌳 Arbre des sous-compétences
              <span className="count-badge">{comp.toutesSousCompetences.length} au total</span>
            </h2>
            {comp.sousCompetences.length === 0
              ? <p className="empty-text">Aucune sous-compétence.</p>
              : <ArbreCompetences racines={arbre} courant={id} />}
          </div>

          <div className="card">
            <h2 className="card-title">🔁 Compétences équivalentes</h2>
            <ListeTags elements={comp.equivalentes} lien={(c) => `/competences/${c}`} />
          </div>

          <div className="card">
            <h2 className="card-title">🛠️ Technologies</h2>
            <ListeTags elements={comp.technologies} lien={(t) => `/technologies/${t}`} couleur="tag-green" />
          </div>

          <div className="card">
            <h2 className="card-title">📦 Modules pour acquérir la compétence</h2>
            <ListeTags elements={comp.modulesPourAcquerir} couleur="tag-gold" vide="Aucun cours ne développe cette compétence." />
            <h2 className="card-title" style={{ marginTop: "1rem" }}>🔒 Modules qui la requièrent</h2>
            <ListeTags elements={comp.modulesRequierent} couleur="tag-gold" />
          </div>

          <div className="card">
            <h2 className="card-title">📝 Évaluations</h2>
            <ListeTags elements={comp.evaluations} lien={(e) => `/evaluations/${e}`} />
          </div>

          <div className="card">
            <h2 className="card-title">👤 Apprenants qui la possèdent</h2>
            <ListeTags elements={comp.apprenants} lien={(a) => `/apprenants/${a}`} couleur="tag-green" />
          </div>
        </div>
      </div>

      <ConfirmDialog
        ouvert={confirmer}
        titre="Supprimer la compétence ?"
        message={`« ${comp.intitule} » et tous ses liens entrants et sortants seront supprimés de Fuseki.`}
        onConfirmer={supprimer}
        onAnnuler={() => setConfirmer(false)}
      />

      <FormModal
        ouvert={modal}
        titre={`Nouvelle sous-compétence de « ${comp.intitule} »`}
        erreur={erreurModal}
        enCours={enCours}
        libelleValider="Créer"
        onValider={creerSousCompetence}
        onFermer={() => { setModal(false); setErreurModal(""); }}
      >
        <label className="form-label">Intitulé *
          <input className="input" required value={sous.intitule} onChange={(e) => setSous({ ...sous, intitule: e.target.value })} />
        </label>
        <label className="form-label">Type
          <select className="input select" value={sous.type} onChange={(e) => setSous({ ...sous, type: e.target.value })}>
            <option value="">Même type que le parent ({comp.type})</option>
            {types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </label>
        <label className="form-label">Score de maturité (0 à 100)
          <input className="input" type="number" min="0" max="100" value={sous.scoreMaturite}
            onChange={(e) => setSous({ ...sous, scoreMaturite: e.target.value })} />
        </label>
      </FormModal>

      <Notification notif={notif} onFermer={() => setNotif(null)} />
    </div>
  );
}
