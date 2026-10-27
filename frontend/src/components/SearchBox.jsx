// TEMPORAIRE (Ala) – à remplacer par la version de Zahra
//
// Props : valeur, onChange(texte), placeholder, delai (ms, défaut 300)
// onChange n'est appelé qu'après une pause de frappe (évite une requête par touche).
import { useEffect, useState } from 'react'
import './composants.css'

export default function SearchBox({ valeur = '', onChange, placeholder = 'Rechercher…', delai = 300 }) {
  const [texte, setTexte] = useState(valeur)

  // Si le parent réinitialise la valeur, on suit
  useEffect(() => { setTexte(valeur) }, [valeur])

  useEffect(() => {
    if (texte === valeur) return undefined
    const minuteur = setTimeout(() => onChange(texte), delai)
    return () => clearTimeout(minuteur)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [texte])

  return (
    <input type="search" className="recherche" value={texte} placeholder={placeholder}
           onChange={(e) => setTexte(e.target.value)} />
  )
}
