// Choix d'individus liés dans une liste déjà chargée (options de /formations/options ou /parcours/options).
// Les listes viennent de l'API d'Imem : elles marchent même si la page de l'autre membre
// (modules, certifications…) n'est pas encore fusionnée. Mêmes styles que RelationSelect.
//
// Props : titre, options [{ id, label }], valeur (tableau d'ids, ou un id si unique), onChange, unique, requis
import { useState } from 'react'
import '../../components/composants.css'

export default function ChoixMultiple({ titre, options = [], valeur, onChange, unique = false, requis = false }) {
  const [filtre, setFiltre] = useState('')
  const choisis = unique ? (valeur ? [valeur] : []) : valeur
  const visibles = options.filter((o) => o.label.toLowerCase().includes(filtre.toLowerCase()))

  const basculer = (id) => {
    if (unique) onChange(valeur === id ? null : id)
    else onChange(choisis.includes(id) ? choisis.filter((v) => v !== id) : [...choisis, id])
  }

  return (
    <fieldset className="choix">
      <legend>{titre}{requis && ' *'} <span className="nombre">{choisis.length}</span></legend>
      <div className="rs">
        <input type="search" className="rs-filtre" placeholder="Filtrer…" value={filtre}
               onChange={(e) => setFiltre(e.target.value)} />
        <div className="rs-liste">
          {visibles.map((o) => (
            <label key={o.id}>
              <input type={unique ? 'radio' : 'checkbox'} checked={choisis.includes(o.id)}
                     onChange={() => basculer(o.id)} onClick={unique ? () => valeur === o.id && basculer(o.id) : undefined} />
              {o.label}
            </label>
          ))}
          {visibles.length === 0 && <span className="rs-aide">Aucun élément.</span>}
        </div>
      </div>
    </fieldset>
  )
}
