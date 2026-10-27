import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import ConfirmDialog from "../../components/ConfirmDialog";
import Notification from "../../components/Notification";
import { ListeTags } from "./commun";
import { messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

export default function TechnologieFiche() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tech, setTech] = useState(null);
  const [confirmer, setConfirmer] = useState(false);
  const [notif, setNotif] = useState(null);

  useEffect(() => {
    api.get(`/technologies/${id}`).then((res) => setTech(res.data)).catch(() => navigate("/technologies"));
  }, [id, navigate]);

  const supprimer = () => {
    setConfirmer(false);
    api.delete(`/technologies/${id}`)
      .then(() => navigate("/technologies"))
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }));
  };

  if (!tech) return <div className="loader-wrap"><div className="loader" /></div>;

  return (
    <div className="page-container">
      <div className="back-link">
        <Link to="/technologies" className="btn-sm btn-outline">← Retour</Link>
      </div>
      <div className="fiche-grid">
        <div className="card profile-card">
          <div className="avatar">🛠️</div>
          <h1 className="fiche-name">{tech.label}</h1>
          <span className="badge">{tech.type}</span>
          <div className="info-list">
            <div className="info-row"><span className="info-label">Identifiant</span><span className="font-mono">{tech.id}</span></div>
            <div className="info-row"><span className="info-label">Cours</span><span>{tech.cours.length}</span></div>
            <div className="info-row"><span className="info-label">Apprenants</span><span>{tech.apprenants.length}</span></div>
          </div>
          <div className="fiche-actions">
            <Link to={`/technologies/${id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
            <button className="btn-sm btn-danger" onClick={() => setConfirmer(true)}>Supprimer</button>
          </div>
        </div>
        <div className="relations-col">
          <div className="card">
            <h2 className="card-title">🧠 Compétences mobilisant cette technologie</h2>
            <ListeTags elements={tech.competences} lien={(c) => `/competences/${c}`} />
          </div>
          <div className="card">
            <h2 className="card-title">📚 Cours qui l'utilisent</h2>
            <ListeTags elements={tech.cours} couleur="tag-gold" />
          </div>
          <div className="card">
            <h2 className="card-title">👤 Apprenants qui la maîtrisent</h2>
            <ListeTags elements={tech.apprenants} lien={(a) => `/apprenants/${a}`} couleur="tag-green" />
          </div>
        </div>
      </div>

      <ConfirmDialog
        ouvert={confirmer}
        titre="Supprimer la technologie ?"
        message={`« ${tech.label} » et tous ses liens seront supprimés de Fuseki.`}
        onConfirmer={supprimer}
        onAnnuler={() => setConfirmer(false)}
      />
      <Notification notif={notif} onFermer={() => setNotif(null)} />
    </div>
  );
}
