// TEMPORAIRE (Ala) – à remplacer par la version de Zahra
//
// Props : children (les champs de filtre), onReinitialiser? (affiche un bouton « Réinitialiser »)
import './composants.css'

export default function FilterBar({ children, onReinitialiser }) {
  return (
    <div className="filtres">
      {children}
      {onReinitialiser && <button className="btn" onClick={onReinitialiser}>Réinitialiser</button>}
    </div>
  )
}
