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
 */
import "./composants.css";

export default function FilterBar({ filtres = [], valeurs = {}, onChange, onReset, children, onReinitialiser }) {
  // Forme d'Ala : les champs sont fournis par la page
  if (children && filtres.length === 0) {
    return (
      <div className="filtres">
        {children}
        {onReinitialiser && <button className="btn" onClick={onReinitialiser}>Réinitialiser</button>}
      </div>
    );
  }

  const reinitialiser = onReset ?? onReinitialiser;
  return (
    <div style={styles.barre}>
      {filtres.map((f) => (
        <div key={f.id} style={styles.groupe}>
          <label style={styles.label} htmlFor={f.id}>
            {f.label}
          </label>
          <select
            id={f.id}
            style={styles.select}
            value={valeurs[f.id] ?? ""}
            onChange={(e) => onChange(f.id, e.target.value)}
          >
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
        <button style={styles.reset} onClick={reinitialiser}>
          Réinitialiser
        </button>
      )}
    </div>
  );
}

const styles = {
  barre: {
    display: "flex",
    flexWrap: "wrap",
    gap: "12px",
    alignItems: "flex-end",
    padding: "12px 16px",
    background: "#f5f7fa",
    borderRadius: "8px",
    marginBottom: "16px",
  },
  groupe: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  label: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#555",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  select: {
    padding: "6px 10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
    background: "#fff",
    cursor: "pointer",
  },
  reset: {
    padding: "6px 14px",
    borderRadius: "6px",
    border: "1px solid #bbb",
    background: "#fff",
    cursor: "pointer",
    fontSize: "13px",
    color: "#666",
    alignSelf: "flex-end",
  },
};
