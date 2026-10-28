/**
 * FilterBar — Tâche Phase 0 de Zahra
 * Barre de filtres réutilisable par toutes les pages liste.
 * Props :
 *   filtres    : tableau de { id, label, options: [{valeur, label}] }
 *   valeurs    : objet { [id]: valeurChoisie }
 *   onChange   : (id, valeur) => void
 *   onReset    : () => void
 *
 * Forme de l'ancienne doublure d'Ala (pages d'Ala et d'Imem), toujours acceptée :
 *   children (les champs de filtre) + onReinitialiser
 * Styles : composants.css (.filtres)
 */
import "./composants.css";

export default function FilterBar({ filtres = [], valeurs = {}, onChange, onReset, children, onReinitialiser }) {
  const reinitialiser = onReset ?? onReinitialiser;
  return (
    <div className="filtres">
      {filtres.map((f) => (
        <div key={f.id} className="filtre-groupe">
          <label className="filtre-label" htmlFor={f.id}>
            {f.label}
          </label>
          <select id={f.id} value={valeurs[f.id] ?? ""} onChange={(e) => onChange(f.id, e.target.value)}>
            <option value="">Tous</option>
            {f.options.map((opt) => (
              <option key={opt.valeur} value={opt.valeur}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ))}

      {children}

      {reinitialiser && (
        <button type="button" className="btn" onClick={reinitialiser}>
          Réinitialiser
        </button>
      )}
    </div>
  );
}
