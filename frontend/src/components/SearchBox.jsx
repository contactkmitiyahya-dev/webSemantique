/**
 * SearchBox — Tâche Phase 0 de Zahra
 * Barre de recherche textuelle réutilisable.
 * Props :
 *   valeur      : string
 *   onChange    : (valeur) => void
 *   placeholder : string (optionnel)
 */
import { useRef } from "react";

export default function SearchBox({
  valeur = "",
  onChange,
  placeholder = "Rechercher...",
}) {
  const inputRef = useRef(null);

  function effacer() {
    onChange("");
    inputRef.current?.focus();
  }

  return (
    <div style={styles.conteneur}>
      <span style={styles.icone}>🔍</span>
      <input
        ref={inputRef}
        type="text"
        style={styles.input}
        value={valeur}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      {valeur && (
        <button style={styles.effacer} onClick={effacer} title="Effacer">
          ✕
        </button>
      )}
    </div>
  );
}

const styles = {
  conteneur: {
    display: "flex",
    alignItems: "center",
    border: "1px solid #ccc",
    borderRadius: "8px",
    padding: "6px 10px",
    background: "#fff",
    gap: "8px",
    minWidth: "220px",
  },
  icone: {
    fontSize: "14px",
    color: "#888",
  },
  input: {
    border: "none",
    outline: "none",
    fontSize: "14px",
    flex: 1,
    background: "transparent",
  },
  effacer: {
    border: "none",
    background: "none",
    cursor: "pointer",
    fontSize: "12px",
    color: "#999",
    padding: "0 2px",
  },
};
