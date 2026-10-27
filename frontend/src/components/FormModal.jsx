// TEMPORAIRE (Ala) – à remplacer par la version de Linda
//
// Props : ouvert, titre, onFermer, onValider (appelé à la soumission du formulaire),
//         enCours (désactive les boutons), erreur (message affiché), texteValider, children (les champs)
import './composants.css'

export default function FormModal({
  ouvert, titre, onFermer, onValider, enCours = false, erreur, texteValider = 'Enregistrer', children,
}) {
  if (!ouvert) return null

  const soumettre = (e) => {
    e.preventDefault() // pas de rechargement de page
    onValider()
  }

  return (
    <div className="modal-fond" onMouseDown={(e) => e.target === e.currentTarget && onFermer()}>
      <form className="modal" onSubmit={soumettre}>
        <div className="modal-entete">
          <h2>{titre}</h2>
          <button type="button" className="fermer" onClick={onFermer} aria-label="Fermer">×</button>
        </div>
        <div className="modal-corps">
          {children}
          {erreur && <p className="erreur">{erreur}</p>}
        </div>
        <div className="modal-pied">
          <button type="button" className="btn" onClick={onFermer} disabled={enCours}>Annuler</button>
          <button type="submit" className="btn primaire" disabled={enCours}>
            {enCours ? 'Enregistrement…' : texteValider}
          </button>
        </div>
      </form>
    </div>
  )
}
