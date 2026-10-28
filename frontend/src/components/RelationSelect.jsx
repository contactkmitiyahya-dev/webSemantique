/**
 * RelationSelect — Tâche Phase 0 de Zahra
 * Liste déroulante alimentée dynamiquement depuis l'API.
 * Props :
 *   endpoint   : string  ex. "/modules"
 *   valeur     : string  id sélectionné
 *   onChange   : (id) => void
 *   label      : string  texte du champ
 *   optionVide : string  texte de l'option vide (défaut : "— Sélectionner —")
 *
 * Sélection MULTIPLE (ancienne doublure d'Ala, pages d'Ala et d'Imem) quand la prop `ressource` est donnée :
 *   ressource ('cours', 'formations'…), valeurs (tableau d'ids), onChange(ids), desactive, placeholder
 */
import { useEffect, useState } from "react";
import client from "../api/client";
import "./composants.css";

export default function RelationSelect(props) {
  return props.ressource !== undefined ? <RelationSelectMultiple {...props} /> : <RelationSelectSimple {...props} />;
}

function RelationSelectSimple({
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
    <div className="rs-simple">
      {label && <label>{label}</label>}
      <select
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
      {erreur && <span className="rs-erreur">{erreur}</span>}
    </div>
  );
}

// Libellé lisible quelle que soit la forme renvoyée par la route de l'autre membre
const libelle = (x) => x.label ?? x.intitule ?? x.nom_complet ?? x.nom ?? x.id;

// Version d'Ala : cases à cocher avec filtre ; si la route n'existe pas, saisie libre des identifiants
function RelationSelectMultiple({ ressource, valeurs = [], onChange, desactive = false, placeholder }) {
  const [options, setOptions] = useState(null);
  const [indisponible, setIndisponible] = useState(false);
  const [filtre, setFiltre] = useState("");

  useEffect(() => {
    let annule = false;
    client.get(`/${ressource}`, { params: { taille: 100 } })
      .then((r) => { if (!annule) setOptions(r.data.donnees ?? []); })
      .catch(() => { if (!annule) setIndisponible(true); });
    return () => { annule = true; };
  }, [ressource]);

  if (indisponible) {
    return (
      <div>
        <input type="text" value={valeurs.join(", ")} disabled={desactive} style={{ width: "100%" }}
               placeholder={`Identifiants séparés par des virgules${placeholder ? ` (${placeholder})` : ""}`}
               onChange={(e) => onChange(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))} />
        <p className="rs-aide">Liste « {ressource} » indisponible : saisissez les identifiants.</p>
      </div>
    );
  }
  if (!options) return <p className="rs-aide">Chargement…</p>;

  const basculer = (id) => onChange(valeurs.includes(id) ? valeurs.filter((v) => v !== id) : [...valeurs, id]);
  const visibles = options.filter((o) => libelle(o).toLowerCase().includes(filtre.toLowerCase()));

  return (
    <div className="rs">
      <input type="search" className="rs-filtre" placeholder="Filtrer…" value={filtre}
             onChange={(e) => setFiltre(e.target.value)} disabled={desactive} />
      <div className="rs-liste">
        {visibles.map((o) => (
          <label key={o.id}>
            <input type="checkbox" checked={valeurs.includes(o.id)} disabled={desactive}
                   onChange={() => basculer(o.id)} />
            {libelle(o)}
          </label>
        ))}
        {visibles.length === 0 && <span className="rs-aide">Aucun élément.</span>}
      </div>
    </div>
  );
}
