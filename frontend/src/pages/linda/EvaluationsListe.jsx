import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import ConfirmDialog from "../../components/ConfirmDialog";
import Notification from "../../components/Notification";
import { Pagination } from "./commun";
import { aujourdhui, formaterDate, messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

const TAILLE = 10;
const FILTRES_VIDES = { q: "", type: "", module: "", date_min: "", date_max: "" };

export default function EvaluationsListe() {
  const [donnees, setDonnees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filtres, setFiltres] = useState(FILTRES_VIDES);
  const [options, setOptions] = useState({ types: [], modules: [] });
  const [stats, setStats] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [aSupprimer, setASupprimer] = useState(null);
  const [notif, setNotif] = useState(null);

  const charger = useCallback((f, p) => {
    const params = new URLSearchParams({ page: p, taille: TAILLE });
    Object.entries(f).forEach(([k, v]) => { if (v !== "") params.set(k, v); });
    api.get(`/evaluations?${params}`)
      .then((res) => { setDonnees(res.data.donnees); setTotal(res.data.total); })
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }))
      .finally(() => setChargement(false));
  }, []);

  const recharger = (f, p) => { setChargement(true); charger(f, p); };

  useEffect(() => {
    charger(FILTRES_VIDES, 1);
    api.get("/evaluations/options").then((res) => setOptions(res.data)).catch(() => {});
    api.get("/evaluations/statistiques").then((res) => setStats(res.data)).catch(() => {});
  }, [charger]);

  const set = (champ) => (e) => setFiltres({ ...filtres, [champ]: e.target.value });
  const appliquer = (f) => { setFiltres(f); setPage(1); recharger(f, 1); };
  const filtrer = (e) => { e.preventDefault(); appliquer(filtres); };
  const changerPage = (p) => { setPage(p); recharger(filtres, p); };

  const supprimer = () => {
    const ev = aSupprimer;
    setASupprimer(null);
    api.delete(`/evaluations/${ev.id}`)
      .then(() => { setNotif({ type: "succes", message: `« ${ev.label} » supprimée.` }); recharger(filtres, page); })
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }));
  };

  const today = aujourdhui();

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Évaluations</h1>
          <p className="page-subtitle">{total} évaluation{total !== 1 ? "s" : ""}</p>
        </div>
        <Link to="/evaluations/nouvelle" className="btn btn-primary">+ Nouvelle évaluation</Link>
      </div>

      <form onSubmit={filtrer} className="filtres">
        <input className="input" placeholder="Rechercher…" value={filtres.q} onChange={set("q")} />
        <select className="input select" value={filtres.type} onChange={set("type")}>
          <option value="">Tous les types</option>
          {options.types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        <select className="input select" value={filtres.module} onChange={set("module")}>
          <option value="">Tous les modules</option>
          {options.modules.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
        </select>
        <label className="filtre-date">Après le
          <input className="input" type="date" value={filtres.date_min} onChange={set("date_min")} />
        </label>
        <label className="filtre-date">Avant le
          <input className="input" type="date" value={filtres.date_max} onChange={set("date_max")} />
        </label>
        <button type="submit" className="btn btn-secondary">Filtrer</button>
        <button type="button" className="btn btn-secondary" onClick={() => appliquer({ ...filtres, date_min: today, date_max: "" })}>À venir</button>
        <button type="button" className="btn-sm btn-outline" onClick={() => appliquer(FILTRES_VIDES)}>Réinitialiser</button>
      </form>

      {chargement ? (
        <div className="loader-wrap"><div className="loader" /></div>
      ) : donnees.length === 0 ? (
        <div className="empty-state"><div className="empty-icon">📝</div><p>Aucune évaluation trouvée</p></div>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr><th>Date</th><th>Évaluation</th><th>Type</th><th>Module(s)</th><th>Note min.</th><th>Coef.</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {donnees.map((ev) => (
                <tr key={ev.id} className="table-row">
                  <td className={ev.dateEvaluation && ev.dateEvaluation.slice(0, 10) >= today ? "date-future" : "date-passee"}>
                    {formaterDate(ev.dateEvaluation)}
                  </td>
                  <td className="font-medium">{ev.label}</td>
                  <td><span className="badge">{ev.type}</span></td>
                  <td>{ev.modules || "—"}</td>
                  <td>{ev.noteMinimale ?? "—"}/20</td>
                  <td>{ev.coefficient ?? "—"}</td>
                  <td className="actions-cell">
                    <Link to={`/evaluations/${ev.id}`} className="btn-sm btn-outline">Voir</Link>
                    <Link to={`/evaluations/${ev.id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
                    <button className="btn-sm btn-danger" onClick={() => setASupprimer(ev)}>Supprimer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} taille={TAILLE} total={total} onPage={changerPage} />
        </div>
      )}

      {stats.length > 0 && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2 className="card-title">📊 Moyenne des notes minimales par type (AVG + GROUP BY)</h2>
          <div className="bar-chart">
            {stats.map((s) => (
              <div key={s.type} className="bar-row" style={{ gridTemplateColumns: "180px 1fr 70px" }}>
                <span className="bar-label">{s.label}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(s.moyenneNoteMinimale / 20) * 100}%`, background: "var(--accent-g)" }} />
                </div>
                <span className="bar-value">{s.moyenneNoteMinimale}/20 ({s.nbEvaluations})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <ConfirmDialog
        ouvert={!!aSupprimer}
        titre="Supprimer l'évaluation ?"
        message={aSupprimer && `« ${aSupprimer.label} » sera supprimée, ainsi que les liens des apprenants qui l'ont passée.`}
        onConfirmer={supprimer}
        onAnnuler={() => setASupprimer(null)}
      />
      <Notification notif={notif} onFermer={() => setNotif(null)} />
    </div>
  );
}
