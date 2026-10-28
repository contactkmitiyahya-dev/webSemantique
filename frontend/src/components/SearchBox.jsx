/**
 * SearchBox — Tâche Phase 0 de Zahra
 * Barre de recherche textuelle réutilisable.
 * Props :
 *   valeur      : string
 *   onChange    : (valeur) => void
 *   placeholder : string (optionnel)
 *   delai       : ms (optionnel, défaut 300) — onChange n'est appelé qu'après une pause de frappe
 *                 (repris de la doublure d'Ala : évite une requête par touche ; 0 = immédiat)
 * Styles : composants.css (.champ-recherche)
 */
import { useEffect, useRef, useState } from "react";
import "./composants.css";

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
    <div className="champ-recherche">
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.7"
           strokeLinecap="round" aria-hidden="true">
        <circle cx="7" cy="7" r="4.5" />
        <path d="M10.5 10.5 14 14" />
      </svg>
      <input
        ref={inputRef}
        type="text"
        value={texte}
        placeholder={placeholder}
        aria-label={placeholder}
        onChange={(e) => setTexte(e.target.value)}
      />
      {texte && (
        <button type="button" onClick={effacer} title="Effacer" aria-label="Effacer la recherche">
          ✕
        </button>
      )}
    </div>
  );
}
