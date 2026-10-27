// TEMPORAIRE (Ala) – à remplacer par la version de Zahra
//
// Sélection multiple d'individus d'une autre ressource, liste alimentée par l'API.
// Props :
//   ressource : chemin de l'API sans /api (ex. 'cours', 'formations')
//   valeurs   : tableau d'identifiants sélectionnés
//   onChange  : (nouveauxIdentifiants) => void
//   desactive : bool
//   placeholder : exemple d'identifiant pour la saisie libre (ex. 'ex. Cours_React')
// Si la route n'existe pas encore (partie d'un autre membre pas encore fusionnée),
// repli sur une saisie libre des identifiants séparés par des virgules.
import { useEffect, useState } from 'react'
import client from '../api/client'
import './composants.css'

// Libellé lisible quelle que soit la forme renvoyée par la route de l'autre membre
const libelle = (x) => x.label ?? x.intitule ?? x.nom_complet ?? x.nom ?? x.id

export default function RelationSelect({ ressource, valeurs = [], onChange, desactive = false, placeholder }) {
  const [options, setOptions] = useState(null)
  const [indisponible, setIndisponible] = useState(false)
  const [filtre, setFiltre] = useState('')

  useEffect(() => {
    let annule = false
    client.get(`/${ressource}`, { params: { taille: 100 } })
      .then((r) => { if (!annule) setOptions(r.data.donnees ?? []) })
      .catch(() => { if (!annule) setIndisponible(true) })
    return () => { annule = true }
  }, [ressource])

  if (indisponible) {
    return (
      <div>
        <input type="text" value={valeurs.join(', ')} disabled={desactive} style={{ width: '100%' }}
               placeholder={`Identifiants séparés par des virgules${placeholder ? ` (${placeholder})` : ''}`}
               onChange={(e) => onChange(e.target.value.split(',').map((s) => s.trim()).filter(Boolean))} />
        <p className="rs-aide">Liste « {ressource} » indisponible : saisissez les identifiants.</p>
      </div>
    )
  }
  if (!options) return <p className="rs-aide">Chargement…</p>

  const basculer = (id) => onChange(valeurs.includes(id) ? valeurs.filter((v) => v !== id) : [...valeurs, id])
  const visibles = options.filter((o) => libelle(o).toLowerCase().includes(filtre.toLowerCase()))

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
  )
}
