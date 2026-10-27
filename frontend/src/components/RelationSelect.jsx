/**
 * RelationSelect — Tâche Phase 0 de Zahra
 * Liste déroulante alimentée dynamiquement depuis l'API.
 * Props :
 *   endpoint   : string  ex. "/api/modules"
 *   valeur     : string  id sélectionné
 *   onChange   : (id) => void
 *   label      : string  texte du champ
 *   optionVide : string  texte de l'option vide (défaut : "— Sélectionner —")
 */
import { useEffect, useState } from "react";
import client from "../api/client";

export default function RelationSelect({
  endpoint,
  valeur = "",
  onChange,
  label = "",
  optionVide = "— Sélectionner —",
}) {
  const [options, setOptions] = useState([]);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    if (!endpoint) return;
    setChargement(true);
    setErreur("");
    client
      .get(endpoint, { params: { taille: 100 } })
      .then((res) => {
        const donnees = res.data?.donnees ?? res.data ?? [];
        setOptions(donnees);
      })
      .catch(() => setErreur("Impossible de charger les options."))
      .finally(() => setChargement(false));
  }, [endpoint]);

  return (
    <div style={styles.conteneur}>
      {label && <label style={styles.label}>{label}</label>}
      <select
        style={styles.select}
        value={valeur}
        onChange={(e) => onChange(e.target.value)}
        disabled={chargement}
      >
        <option value="">{chargement ? "Chargement..." : optionVide}</option>
        {options.map((opt) => (
          <option key={opt.id} value={opt.id}>
            {opt.intitule ?? opt.label ?? opt.id}
          </option>
        ))}
      </select>
      {erreur && <span style={styles.erreur}>{erreur}</span>}
    </div>
  );
}

const styles = {
  conteneur: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  label: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#555",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  select: {
    padding: "6px 10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
    background: "#fff",
    cursor: "pointer",
    minWidth: "180px",
  },
  erreur: {
    fontSize: "12px",
    color: "#e53e3e",
  },
};
