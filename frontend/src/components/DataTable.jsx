// TEMPORAIRE (Ala) – à remplacer par la version d'Imem
//
// Props :
//   colonnes    : [{ cle, titre, rendu?: (ligne) => contenu, triable?: bool }]
//   lignes      : tableau d'objets (une ligne par objet, clé React = ligne.id)
//   chargement  : bool
//   tri, onTri  : si fournis, tri côté serveur ({ cle, ordre: 'asc' | 'desc' }) ; sinon tri local de la page
//   page, taille, total, onPage : pagination côté serveur
//   onClicLigne : (ligne) => void (facultatif)
import { useMemo, useState } from 'react'
import './composants.css'

function comparer(a, b) {
  if (a == null) return 1
  if (b == null) return -1
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b), 'fr')
}

export default function DataTable({
  colonnes, lignes = [], chargement = false, tri, onTri,
  page = 1, taille = 20, total = 0, onPage, onClicLigne, vide = 'Aucun résultat.',
}) {
  const [triLocal, setTriLocal] = useState({ cle: null, ordre: 'asc' })
  const triActif = onTri ? tri : triLocal

  const changerTri = (cle) => {
    const ordre = triActif?.cle === cle && triActif.ordre === 'asc' ? 'desc' : 'asc'
    if (onTri) onTri({ cle, ordre })
    else setTriLocal({ cle, ordre })
  }

  // Tri local uniquement si le parent ne gère pas le tri
  const affichees = useMemo(() => {
    if (onTri || !triLocal.cle) return lignes
    const sens = triLocal.ordre === 'asc' ? 1 : -1
    return [...lignes].sort((a, b) => comparer(a[triLocal.cle], b[triLocal.cle]) * sens)
  }, [lignes, triLocal, onTri])

  const nbPages = Math.max(1, Math.ceil(total / taille))

  return (
    <div>
      <div className="dt-conteneur">
        <table className="dt">
          <thead>
            <tr>
              {colonnes.map((col) => (
                <th key={col.cle} className={col.triable ? 'triable' : ''}
                    onClick={col.triable ? () => changerTri(col.cle) : undefined}>
                  {col.titre}
                  {triActif?.cle === col.cle && (triActif.ordre === 'asc' ? ' ▲' : ' ▼')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {affichees.map((ligne) => (
              <tr key={ligne.id} className={onClicLigne ? 'cliquable' : ''}
                  onClick={onClicLigne ? () => onClicLigne(ligne) : undefined}>
                {colonnes.map((col) => (
                  <td key={col.cle}>{col.rendu ? col.rendu(ligne) : (ligne[col.cle] ?? '—')}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {!chargement && affichees.length === 0 && <div className="dt-vide">{vide}</div>}
        {chargement && <div className="dt-vide">Chargement…</div>}
      </div>

      {onPage && (
        <div className="dt-pagination">
          <span>{total} résultat(s)</span>
          <div>
            <button className="btn" disabled={page <= 1} onClick={() => onPage(page - 1)}>‹ Précédent</button>
            <span>Page {page} / {nbPages}</span>
            <button className="btn" disabled={page >= nbPages} onClick={() => onPage(page + 1)}>Suivant ›</button>
          </div>
        </div>
      )}
    </div>
  )
}
