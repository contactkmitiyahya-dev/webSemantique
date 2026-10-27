import { Link } from "react-router-dom";

/** Liste de relations {id, label} en etiquettes ; `lien` construit l'URL (ou null : pas de lien). */
export function ListeTags({ elements, lien, couleur = "", vide = "Aucun" }) {
  if (!elements || elements.length === 0) return <p className="empty-text">{vide}</p>;
  return (
    <ul className="tag-list">
      {elements.map((e) => (
        <li key={e.id}>
          {lien ? (
            <Link to={lien(e.id)} className={`tag tag-lien ${couleur}`}>{e.label}</Link>
          ) : (
            <span className={`tag ${couleur}`} title={e.id}>{e.label}</span>
          )}
        </li>
      ))}
    </ul>
  );
}

/** Choix multiple par cases a cocher. options : [{id, label}], valeurs : ids coches. */
export function ChoixMultiple({ options, valeurs, onChange, exclure = [] }) {
  const basculer = (id) =>
    onChange(valeurs.includes(id) ? valeurs.filter((v) => v !== id) : [...valeurs, id]);
  const visibles = options.filter((o) => !exclure.includes(o.id));
  return (
    <div className="choix-multiple">
      {visibles.length === 0 && <span className="empty-text">Aucune option</span>}
      {visibles.map((o) => (
        <label key={o.id} className={"choix-item" + (valeurs.includes(o.id) ? " choix-actif" : "")}>
          <input type="checkbox" checked={valeurs.includes(o.id)} onChange={() => basculer(o.id)} />
          {o.label}
        </label>
      ))}
    </div>
  );
}

/** Pagination basee sur le total renvoye par l'API. */
export function Pagination({ page, taille, total, onPage }) {
  const pages = Math.max(1, Math.ceil(total / taille));
  return (
    <div className="pagination">
      <button className="btn-sm btn-outline" disabled={page <= 1} onClick={() => onPage(page - 1)}>← Précédent</button>
      <span className="page-info">Page {page} / {pages}</span>
      <button className="btn-sm btn-outline" disabled={page >= pages} onClick={() => onPage(page + 1)}>Suivant →</button>
    </div>
  );
}
