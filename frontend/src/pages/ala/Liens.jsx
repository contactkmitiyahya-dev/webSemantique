// Affiche une relation d'une fiche : liste de {id, label, modifiable}, chaque élément cliquable.
// Les liens écrits dans l'autre sens (par un autre membre) portent une mention discrète.
import { Link } from 'react-router-dom'

export default function Liens({ titre, liens = [], route }) {
  return (
    <section className="carte">
      <h3>{titre} <span className="compteur">{liens.length}</span></h3>
      {liens.length === 0 ? (
        <p className="doux">Aucun.</p>
      ) : (
        <ul className="liens">
          {liens.map((l) => (
            <li key={l.id}>
              <Link to={`/${route}/${l.id}`}>{l.label}</Link>
              {!l.modifiable && <span className="lecture-seule" title="Lien écrit dans l'autre sens : non modifiable ici">défini par une autre partie</span>}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
