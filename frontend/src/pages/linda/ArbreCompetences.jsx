import { useState } from "react";
import { Link } from "react-router-dom";

/** Jauge horizontale du score de maturite (0 a 100). */
export function Jauge({ valeur }) {
  if (valeur === null || valeur === undefined) return <span className="empty-text">—</span>;
  return (
    <span className="jauge">
      <span className="jauge-piste"><span className="jauge-remplie" style={{ width: `${valeur}%` }} /></span>
      <span className="jauge-valeur">{valeur}</span>
    </span>
  );
}

function Noeud({ noeud, courant, profondeur }) {
  const [ouvert, setOuvert] = useState(profondeur < 2);
  const aEnfants = noeud.enfants.length > 0;
  return (
    <li>
      <span className={"arbre-noeud" + (noeud.id === courant ? " arbre-courant" : "")}>
        <button type="button" className="arbre-bouton" onClick={() => setOuvert(!ouvert)} disabled={!aEnfants}
          aria-label={ouvert ? "Replier" : "Déplier"}>
          {aEnfants ? (ouvert ? "▼" : "▶") : "•"}
        </button>
        <Link to={`/competences/${noeud.id}`}>{noeud.label}</Link>
        {noeud.scoreMaturite !== null && <span className="arbre-score">({noeud.scoreMaturite})</span>}
      </span>
      {aEnfants && ouvert && (
        <ul>
          {noeud.enfants.map((e) => <Noeud key={e.id} noeud={e} courant={courant} profondeur={profondeur + 1} />)}
        </ul>
      )}
    </li>
  );
}

/** Arbre des sous-competences renvoye par GET /api/competences/arbre. */
export default function ArbreCompetences({ racines, courant }) {
  if (!racines || racines.length === 0) return <p className="empty-text">Aucune compétence.</p>;
  return (
    <ul className="arbre">
      {racines.map((r) => <Noeud key={r.id} noeud={r} courant={courant} profondeur={0} />)}
    </ul>
  );
}
