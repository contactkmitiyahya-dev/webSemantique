import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import ConfirmDialog from "../../components/ConfirmDialog";
import Notification from "../../components/Notification";
import { Pagination } from "./commun";
import { messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

const TAILLE = 10;

export default function TechnologiesListe() {
  const [donnees, setDonnees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filtres, setFiltres] = useState({ q: "", type: "" });
  const [types, setTypes] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [aSupprimer, setASupprimer] = useState(null);
  const [notif, setNotif] = useState(null);

  const charger = useCallback((f, p) => {
    const params = new URLSearchParams({ page: p, taille: TAILLE });
    Object.entries(f).forEach(([k, v]) => { if (v !== "") params.set(k, v); });
    api.get(`/technologies?${params}`)
      .then((res) => { setDonnees(res.data.donnees); setTotal(res.data.total); })
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }))
      .finally(() => setChargement(false));
  }, []);

  const recharger = (f, p) => { setChargement(true); charger(f, p); };

  useEffect(() => {
    charger({ q: "", type: "" }, 1);
    api.get("/technologies/types").then((res) => setTypes(res.data)).catch(() => {});
  }, [charger]);

  const set = (champ) => (e) => setFiltres({ ...filtres, [champ]: e.target.value });
  const filtrer = (e) => { e.preventDefault(); setPage(1); recharger(filtres, 1); };
  const changerPage = (p) => { setPage(p); recharger(filtres, p); };

  const supprimer = () => {
    const t = aSupprimer;
    setASupprimer(null);
    api.delete(`/technologies/${t.id}`)
      .then(() => { setNotif({ type: "succes", message: `« ${t.label} » supprimée.` }); recharger(filtres, page); })
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }));
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Technologies</h1>
          <p className="page-subtitle">{total} technologie{total !== 1 ? "s" : ""}</p>
        </div>
        <Link to="/technologies/nouvelle" className="btn btn-primary">+ Nouvelle technologie</Link>
      </div>

      <form onSubmit={filtrer} className="filtres">
        <input className="input" placeholder="Rechercher une technologie…" value={filtres.q} onChange={set("q")} />
        <select className="input select" value={filtres.type} onChange={set("type")}>
          <option value="">Tous les types</option>
          {types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        <button type="submit" className="btn btn-secondary">Filtrer</button>
      </form>

      {chargement ? (
        <div className="loader-wrap"><div className="loader" /></div>
      ) : donnees.length === 0 ? (
        <div className="empty-state"><div className="empty-icon">🛠️</div><p>Aucune technologie trouvée</p></div>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr><th>Technologie</th><th>Type</th><th>Compétences</th><th>Cours</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {donnees.map((t) => (
                <tr key={t.id} className="table-row">
                  <td className="font-medium">{t.label}</td>
                  <td><span className="badge">{t.type}</span></td>
                  <td>{t.nbCompetences}</td>
                  <td>{t.nbCours}</td>
                  <td className="actions-cell">
                    <Link to={`/technologies/${t.id}`} className="btn-sm btn-outline">Voir</Link>
                    <Link to={`/technologies/${t.id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
                    <button className="btn-sm btn-danger" onClick={() => setASupprimer(t)}>Supprimer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} taille={TAILLE} total={total} onPage={changerPage} />
        </div>
      )}

      <ConfirmDialog
        ouvert={!!aSupprimer}
        titre="Supprimer la technologie ?"
        message={aSupprimer && `« ${aSupprimer.label} » sera retirée des compétences, cours et apprenants qui la référencent.`}
        onConfirmer={supprimer}
        onAnnuler={() => setASupprimer(null)}
      />
      <Notification notif={notif} onFermer={() => setNotif(null)} />
    </div>
  );
}
