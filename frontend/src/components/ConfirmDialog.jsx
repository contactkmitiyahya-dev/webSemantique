import "./components.css";

/**
 * Boite de confirmation (remplace window.confirm).
 * <ConfirmDialog ouvert={...} titre="Supprimer ?" message="..." onConfirmer={...} onAnnuler={...} />
 */
export default function ConfirmDialog({
  ouvert, titre = "Confirmer", message, libelleConfirmer = "Supprimer",
  danger = true, onConfirmer, onAnnuler,
}) {
  if (!ouvert) return null;
  return (
    <div className="modal-fond" onClick={onAnnuler}>
      <div className="modal-boite modal-petite" role="alertdialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-titre">{titre}</h2>
        {message && <p className="modal-texte">{message}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onAnnuler}>Annuler</button>
          <button type="button" className={danger ? "btn btn-danger-plein" : "btn btn-primary"} onClick={onConfirmer} autoFocus>
            {libelleConfirmer}
          </button>
        </div>
      </div>
    </div>
  );
}
