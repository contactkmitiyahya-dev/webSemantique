import { useEffect, useRef } from "react";
import "./components.css";

/**
 * Message temporaire en bas a droite (succes ou erreur), ferme apres `duree` ms.
 * <Notification notif={{ type: "succes", message: "Enregistre" }} onFermer={() => setNotif(null)} />
 * Accepte aussi l'ancienne forme d'Ala (pages d'Ala et d'Imem) :
 * <Notification message="Enregistre" type="succes" onFermer={...} />
 */
export default function Notification({ notif: notifObjet, message, type = "succes", onFermer, duree = 4000 }) {
  // Ref : le minuteur ne redemarre pas a chaque rendu du parent (fonction onFermer recreee)
  const fermer = useRef(onFermer);
  useEffect(() => { fermer.current = onFermer; });

  useEffect(() => {
    if (!notifObjet && !message) return undefined;
    const minuteur = setTimeout(() => fermer.current(), duree);
    return () => clearTimeout(minuteur);
  }, [notifObjet, message, duree]);

  const notif = notifObjet ?? (message ? { message, type } : null);
  if (!notif) return null;
  return (
    <div className={`notification notification-${notif.type || "succes"}`} role="status">
      <span>{notif.type === "erreur" ? "⚠️" : "✅"} {notif.message}</span>
      <button type="button" className="notification-fermer" onClick={onFermer} aria-label="Fermer">×</button>
    </div>
  );
}
