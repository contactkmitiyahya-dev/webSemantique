// Petits composants d'affichage partagés par les pages d'Imem (places, niveau, bloc de liens).
import { Link } from 'react-router-dom'

export function Places({ places, restantes }) {
  if (places == null) return <span className="doux">—</span>
  const ratio = places ? restantes / places : 0
  const etat = restantes <= 0 ? 'complet' : ratio < 0.25 ? 'faible' : ''
  return (
    <span className={`places ${etat}`} title={`${places - restantes} inscrits / ${places} places`}>
      <span className="jauge"><span style={{ width: `${Math.max(0, Math.min(100, (1 - ratio) * 100))}%` }} /></span>
      {restantes <= 0 ? 'Complet' : `${restantes} / ${places}`}
    </span>
  )
}

export function Niveau({ v }) {
  if (!v) return <span className="doux">—</span>
  const couleur = { 'Débutant': 'vert', 'Intermédiaire': 'orange', 'Avancé': 'rouge' }[v] || ''
  return <span className={`pastille ${couleur}`}>{v}</span>
}

// Bloc d'une fiche : liste d'individus liés ; lien vers la fiche si la page existe (route)
export function Bloc({ titre, items = [], route, vide = 'Aucun.' }) {
  return (
    <section className="bloc">
      <h3>{titre} <span className="nombre">{items.length}</span></h3>
      {items.length === 0 ? <p className="doux">{vide}</p> : (
        <ul className="puces">
          {items.map((x) => (
            <li key={x.id} title={x.id}>{route ? <Link to={`/${route}/${x.id}`}>{x.label}</Link> : x.label}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
