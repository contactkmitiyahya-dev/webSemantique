/**
 * SearchBox — Tâche Phase 0 de Zahra
 * Barre de recherche textuelle réutilisable.
 * Props :
 *   valeur      : string
 *   onChange    : (valeur) => void
 *   placeholder : string (optionnel)
 *   delai       : ms (optionnel, défaut 300) — onChange n'est appelé qu'après une pause de frappe
 *                 (repris de la doublure d'Ala : évite une requête par touche ; 0 = immédiat)
 */
import { useEffect, useRef, useState } from "react";

export default function SearchBox({
  valeur = "",
  onChange,
  placeholder = "Rechercher...",
  delai = 300,
}) {
  const inputRef = useRef(null);
  const [texte, setTexte] = useState(valeur);

  // Si le parent réinitialise la valeur, on suit
  useEffect(() => { setTexte(valeur); }, [valeur]);

  useEffect(() => {
    if (texte === valeur) return undefined;
    const minuteur = setTimeout(() => onChange(texte), delai);
    return () => clearTimeout(minuteur);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [texte]);

  function effacer() {
    setTexte("");
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
        value={texte}
        placeholder={placeholder}
        onChange={(e) => setTexte(e.target.value)}
      />
      {texte && (
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
