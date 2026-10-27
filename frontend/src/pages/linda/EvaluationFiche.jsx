import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import ConfirmDialog from "../../components/ConfirmDialog";
import Notification from "../../components/Notification";
import { ListeTags } from "./commun";
import { formaterDate, messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

export default function EvaluationFiche() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ev, setEv] = useState(null);
  const [confirmer, setConfirmer] = useState(false);
  const [notif, setNotif] = useState(null);

  useEffect(() => {
    api.get(`/evaluations/${id}`).then((res) => setEv(res.data)).catch(() => navigate("/evaluations"));
  }, [id, navigate]);

  const supprimer = () => {
    setConfirmer(false);
    api.delete(`/evaluations/${id}`)
      .then(() => navigate("/evaluations"))
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }));
  };

  if (!ev) return <div className="loader-wrap"><div className="loader" /></div>;

  return (
    <div className="page-container">
      <div className="back-link">
        <Link to="/evaluations" className="btn-sm btn-outline">← Retour</Link>
      </div>
      <div className="fiche-grid">
        <div className="card profile-card">
          <div className="avatar">📝</div>
          <h1 className="fiche-name">{ev.label}</h1>
          <span className="badge">{ev.type}</span>
          <div className="info-list">
            <div className="info-row"><span className="info-label">Identifiant</span><span className="font-mono">{ev.id}</span></div>
            <div className="info-row"><span className="info-label">Date</span><span>{formaterDate(ev.dateEvaluation)}</span></div>
            <div className="info-row"><span className="info-label">Note minimale</span><span>{ev.noteMinimale ?? "—"}/20</span></div>
            <div className="info-row"><span className="info-label">Coefficient</span><span>{ev.coefficient ?? "—"}</span></div>
          </div>
          <div className="fiche-actions">
            <Link to={`/evaluations/${id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
            <button className="btn-sm btn-danger" onClick={() => setConfirmer(true)}>Supprimer</button>
          </div>
        </div>
        <div className="relations-col">
          <div className="card">
            <h2 className="card-title">🧠 Compétences évaluées</h2>
            <ListeTags elements={ev.competences} lien={(c) => `/competences/${c}`} />
          </div>
          <div className="card">
            <h2 className="card-title">📦 Module(s)</h2>
            <ListeTags elements={ev.modules} couleur="tag-gold" />
          </div>
          <div className="card">
            <h2 className="card-title">📚 Cours évalués</h2>
            <ListeTags elements={ev.cours} couleur="tag-gold" />
          </div>
          <div className="card">
            <h2 className="card-title">👤 Apprenants qui l'ont passée</h2>
            <ListeTags elements={ev.apprenants} lien={(a) => `/apprenants/${a}`} couleur="tag-green" />
          </div>
        </div>
      </div>

      <ConfirmDialog
        ouvert={confirmer}
        titre="Supprimer l'évaluation ?"
        message={`« ${ev.label} » et tous ses liens seront supprimés de Fuseki.`}
        onConfirmer={supprimer}
        onAnnuler={() => setConfirmer(false)}
      />
      <Notification notif={notif} onFermer={() => setNotif(null)} />
    </div>
  );
}
