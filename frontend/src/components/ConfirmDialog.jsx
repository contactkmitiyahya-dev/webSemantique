// TEMPORAIRE (Ala) – à remplacer par la version de Linda
//
// Props : ouvert, titre, message, onConfirmer, onAnnuler, enCours, texteConfirmer
import './composants.css'

export default function ConfirmDialog({
  ouvert, titre = 'Confirmation', message, onConfirmer, onAnnuler, enCours = false, texteConfirmer = 'Supprimer',
}) {
  if (!ouvert) return null
  return (
    <div className="modal-fond" onMouseDown={(e) => e.target === e.currentTarget && onAnnuler()}>
      <div className="modal petit" role="alertdialog">
        <div className="modal-entete"><h2>{titre}</h2></div>
        <div className="modal-corps"><p style={{ margin: 0 }}>{message}</p></div>
        <div className="modal-pied">
          <button className="btn" onClick={onAnnuler} disabled={enCours}>Annuler</button>
          <button className="btn danger" onClick={onConfirmer} disabled={enCours}>
            {enCours ? 'Suppression…' : texteConfirmer}
          </button>
        </div>
      </div>
    </div>
  )
}
