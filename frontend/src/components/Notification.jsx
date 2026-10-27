import { useEffect, useRef } from "react";
import "./components.css";

/**
 * Message temporaire en bas a droite (succes ou erreur), ferme apres `duree` ms.
 * <Notification notif={{ type: "succes", message: "Enregistre" }} onFermer={() => setNotif(null)} />
 */
export default function Notification({ notif, onFermer, duree = 4000 }) {
  // Ref : le minuteur ne redemarre pas a chaque rendu du parent (fonction onFermer recreee)
  const fermer = useRef(onFermer);
  useEffect(() => { fermer.current = onFermer; });

  useEffect(() => {
    if (!notif) return undefined;
    const minuteur = setTimeout(() => fermer.current(), duree);
    return () => clearTimeout(minuteur);
  }, [notif, duree]);

  if (!notif) return null;
  return (
    <div className={`notification notification-${notif.type || "succes"}`} role="status">
      <span>{notif.type === "erreur" ? "⚠️" : "✅"} {notif.message}</span>
      <button type="button" className="notification-fermer" onClick={onFermer} aria-label="Fermer">×</button>
    </div>
  );
}
