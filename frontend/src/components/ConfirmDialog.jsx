import "./components.css";

/**
 * Boite de confirmation (remplace window.confirm).
 * <ConfirmDialog ouvert={...} titre="Supprimer ?" message="..." onConfirmer={...} onAnnuler={...} />
 * Accepte aussi les props de l'ancienne version d'Ala (pages d'Ala et d'Imem) : texteConfirmer, enCours.
 */
export default function ConfirmDialog({
  ouvert, titre = "Confirmer", message, libelleConfirmer, texteConfirmer,
  danger = true, enCours = false, onConfirmer, onAnnuler,
}) {
  if (!ouvert) return null;
  const libelle = libelleConfirmer ?? texteConfirmer ?? "Supprimer";
  return (
    <div className="modal-fond" onClick={onAnnuler}>
      <div className="modal-boite modal-petite" role="alertdialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-titre">{titre}</h2>
        {message && <p className="modal-texte">{message}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onAnnuler} disabled={enCours}>Annuler</button>
          <button type="button" className={danger ? "btn btn-danger-plein" : "btn btn-primary"} onClick={onConfirmer}
                  disabled={enCours} autoFocus>
            {enCours ? "Suppression…" : libelle}
          </button>
        </div>
      </div>
    </div>
  );
}
