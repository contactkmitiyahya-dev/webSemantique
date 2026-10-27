import "./components.css";

/**
 * Formulaire dans une fenetre modale. Les champs sont passes en children.
 * <FormModal ouvert titre="Nouvelle sous-competence" onValider={...} onFermer={...} erreur={...}>
 *   <input ... />
 * </FormModal>
 */
export default function FormModal({
  ouvert, titre, children, erreur, enCours = false,
  libelleValider = "Enregistrer", onValider, onFermer,
}) {
  if (!ouvert) return null;
  const soumettre = (e) => {
    e.preventDefault();
    onValider();
  };
  return (
    <div className="modal-fond" onClick={onFermer}>
      <form className="modal-boite" role="dialog" aria-modal="true" onSubmit={soumettre} onClick={(e) => e.stopPropagation()}>
        <div className="modal-entete">
          <h2 className="modal-titre">{titre}</h2>
          <button type="button" className="modal-fermer" onClick={onFermer} aria-label="Fermer">×</button>
        </div>
        {erreur && <div className="alert alert-error">{erreur}</div>}
        <div className="modal-corps">{children}</div>
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onFermer}>Annuler</button>
          <button type="submit" className="btn btn-primary" disabled={enCours}>
            {enCours ? "Enregistrement…" : libelleValider}
          </button>
        </div>
      </form>
    </div>
  );
}
