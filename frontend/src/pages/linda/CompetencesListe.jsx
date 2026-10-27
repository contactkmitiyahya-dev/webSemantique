import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import ConfirmDialog from "../../components/ConfirmDialog";
import Notification from "../../components/Notification";
import ArbreCompetences, { Jauge } from "./ArbreCompetences";
import { Pagination } from "./commun";
import { messageErreur } from "./outils";
import "../yahya/yahya.css";
import "./linda.css";

const TAILLE = 10;

export default function CompetencesListe() {
  const [onglet, setOnglet] = useState("liste");
  const [donnees, setDonnees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filtres, setFiltres] = useState({ q: "", type: "", score_min: "" });
  const [types, setTypes] = useState([]);
  const [arbre, setArbre] = useState([]);
  const [repandues, setRepandues] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [aSupprimer, setASupprimer] = useState(null);
  const [notif, setNotif] = useState(null);

  const charger = useCallback((f, p) => {
    const params = new URLSearchParams({ page: p, taille: TAILLE });
    Object.entries(f).forEach(([k, v]) => { if (v !== "") params.set(k, v); });
    api.get(`/competences?${params}`)
      .then((res) => { setDonnees(res.data.donnees); setTotal(res.data.total); })
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }))
      .finally(() => setChargement(false));
  }, []);

  const recharger = (f, p) => { setChargement(true); charger(f, p); };

  useEffect(() => {
    charger({ q: "", type: "", score_min: "" }, 1);
    api.get("/competences/types").then((res) => setTypes(res.data)).catch(() => {});
  }, [charger]);

  useEffect(() => {
    if (onglet === "arbre") api.get("/competences/arbre").then((res) => setArbre(res.data)).catch(() => {});
    if (onglet === "repandues") api.get("/competences/repandues").then((res) => setRepandues(res.data)).catch(() => {});
  }, [onglet]);

  const set = (champ) => (e) => setFiltres({ ...filtres, [champ]: e.target.value });

  const filtrer = (e) => {
    e.preventDefault();
    setPage(1);
    recharger(filtres, 1);
  };

  const changerPage = (p) => { setPage(p); recharger(filtres, p); };

  const supprimer = () => {
    const c = aSupprimer;
    setASupprimer(null);
    api.delete(`/competences/${c.id}`)
      .then(() => { setNotif({ type: "succes", message: `« ${c.intitule} » supprimée.` }); recharger(filtres, page); })
      .catch((err) => setNotif({ type: "erreur", message: messageErreur(err) }));
  };

  const maxRepandue = Math.max(1, ...repandues.map((r) => r.nbApprenants));

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Compétences</h1>
          <p className="page-subtitle">{total} compétence{total !== 1 ? "s" : ""} — sous-compétences via estSousCompetenceDe+</p>
        </div>
        <Link to="/competences/nouvelle" className="btn btn-primary">+ Nouvelle compétence</Link>
      </div>

      <div className="onglets">
        {[["liste", "Liste"], ["arbre", "Arbre"], ["repandues", "Les plus répandues"]].map(([cle, libelle]) => (
          <button key={cle} className={"onglet" + (onglet === cle ? " onglet-actif" : "")} onClick={() => setOnglet(cle)}>
            {libelle}
          </button>
        ))}
      </div>

      {onglet === "liste" && (
        <>
          <form onSubmit={filtrer} className="filtres">
            <input className="input" placeholder="Rechercher une compétence…" value={filtres.q} onChange={set("q")} />
            <select className="input select" value={filtres.type} onChange={set("type")}>
              <option value="">Tous les types</option>
              {types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
            <input className="input" type="number" min="0" max="100" placeholder="Score minimal" value={filtres.score_min} onChange={set("score_min")} />
            <button type="submit" className="btn btn-secondary">Filtrer</button>
          </form>

          {chargement ? (
            <div className="loader-wrap"><div className="loader" /></div>
          ) : donnees.length === 0 ? (
            <div className="empty-state"><div className="empty-icon">🧠</div><p>Aucune compétence trouvée</p></div>
          ) : (
            <div className="table-card">
              <table className="data-table">
                <thead>
                  <tr><th>Intitulé</th><th>Type</th><th>Maturité</th><th>Sous-compétences</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {donnees.map((c) => (
                    <tr key={c.id} className="table-row">
                      <td className="font-medium">{c.intitule}</td>
                      <td><span className="badge">{c.type}</span></td>
                      <td><Jauge valeur={c.scoreMaturite} /></td>
                      <td>{c.nbSousCompetences}</td>
                      <td className="actions-cell">
                        <Link to={`/competences/${c.id}`} className="btn-sm btn-outline">Voir</Link>
                        <Link to={`/competences/${c.id}/modifier`} className="btn-sm btn-outline">Modifier</Link>
                        <button className="btn-sm btn-danger" onClick={() => setASupprimer(c)}>Supprimer</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <Pagination page={page} taille={TAILLE} total={total} onPage={changerPage} />
            </div>
          )}
        </>
      )}

      {onglet === "arbre" && (
        <div className="card"><ArbreCompetences racines={arbre} /></div>
      )}

      {onglet === "repandues" && (
        <div className="card">
          <h2 className="card-title">Compétences possédées par le plus d'apprenants (GROUP BY)</h2>
          <div className="bar-chart">
            {repandues.map((r) => (
              <div key={r.id} className="bar-row" style={{ gridTemplateColumns: "160px 1fr 30px" }}>
                <Link to={`/competences/${r.id}`} className="bar-label">{r.label}</Link>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(r.nbApprenants / maxRepandue) * 100}%`, background: "var(--accent-g)" }} />
                </div>
                <span className="bar-value">{r.nbApprenants}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <ConfirmDialog
        ouvert={!!aSupprimer}
        titre="Supprimer la compétence ?"
        message={aSupprimer && `« ${aSupprimer.intitule} » et tous ses liens (sous-compétences, équivalences, apprenants) seront supprimés.`}
        onConfirmer={supprimer}
        onAnnuler={() => setASupprimer(null)}
      />
      <Notification notif={notif} onFermer={() => setNotif(null)} />
    </div>
  );
}
