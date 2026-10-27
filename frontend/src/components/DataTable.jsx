// DataTable réutilisable (propriétaire : Imem) : colonnes, tri, pagination, clic sur une ligne.
//
// Props :
//   colonnes    : [{ cle, titre, rendu?: (ligne) => contenu, triable?: bool,
//                    align?: 'droite', valeurTri?: (ligne) => valeur utilisée par le tri local }]
//   lignes      : tableau d'objets (une ligne par objet, clé React = ligne[cleLigne], 'id' par défaut)
//   chargement  : bool ; vide : texte affiché quand il n'y a aucune ligne
//   tri, onTri  : si fournis, tri côté serveur ({ cle, ordre: 'asc' | 'desc' }) ; sinon tri local
//   page, taille, total, onPage : pagination côté serveur
//   taille sans onPage : pagination locale (liste déjà chargée en entier)
//   onClicLigne : (ligne) => void (facultatif)
import { useMemo, useState } from 'react'
import './composants.css'

function comparer(a, b) {
  if (a == null) return 1
  if (b == null) return -1
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b), 'fr', { sensitivity: 'base' })
}

export default function DataTable({
  colonnes, lignes = [], chargement = false, tri, onTri,
  page = 1, taille, total = 0, onPage, onClicLigne, vide = 'Aucun résultat.', cleLigne = 'id',
}) {
  const [triLocal, setTriLocal] = useState({ cle: null, ordre: 'asc' })
  const [pageLocale, setPageLocale] = useState(1)
  const triActif = onTri ? tri : triLocal
  const paginationLocale = !onPage && Boolean(taille)

  const changerTri = (cle) => {
    const ordre = triActif?.cle === cle && triActif.ordre === 'asc' ? 'desc' : 'asc'
    if (onTri) onTri({ cle, ordre })
    else setTriLocal({ cle, ordre })
  }

  // Tri local uniquement si le parent ne gère pas le tri ; puis découpage si pagination locale
  const triees = useMemo(() => {
    const liste = lignes ?? []
    if (onTri || !triLocal.cle) return liste
    const col = colonnes.find((c) => c.cle === triLocal.cle)
    const valeur = col?.valeurTri ?? ((l) => l[triLocal.cle])
    const sens = triLocal.ordre === 'asc' ? 1 : -1
    return [...liste].sort((a, b) => comparer(valeur(a), valeur(b)) * sens)
  }, [lignes, triLocal, onTri, colonnes])

  const nbLignes = paginationLocale ? triees.length : total
  const nbPages = Math.max(1, Math.ceil(nbLignes / (taille || 1)))
  // la liste locale peut rétrécir (nouveau filtre) : on ne dépasse jamais la dernière page
  const pageCourante = paginationLocale ? Math.min(pageLocale, nbPages) : page
  const affichees = paginationLocale ? triees.slice((pageCourante - 1) * taille, pageCourante * taille) : triees
  const allerA = (p) => (paginationLocale ? setPageLocale(p) : onPage(p))
  const alignement = (col) => (col.align === 'droite' ? 'droite' : '')

  return (
    <div>
      <div className="dt-conteneur">
        <table className="dt">
          <thead>
            <tr>
              {colonnes.map((col) => (
                <th key={col.cle} className={`${col.triable ? 'triable' : ''} ${alignement(col)}`}
                    onClick={col.triable ? () => changerTri(col.cle) : undefined}
                    aria-sort={triActif?.cle === col.cle ? (triActif.ordre === 'asc' ? 'ascending' : 'descending') : undefined}>
                  {col.titre}
                  {triActif?.cle === col.cle && (triActif.ordre === 'asc' ? ' ▲' : ' ▼')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {!chargement && affichees.map((ligne, i) => (
              <tr key={ligne[cleLigne] ?? i} className={onClicLigne ? 'cliquable' : ''}
                  onClick={onClicLigne ? () => onClicLigne(ligne) : undefined}>
                {colonnes.map((col) => (
                  <td key={col.cle} className={alignement(col)}>{col.rendu ? col.rendu(ligne) : (ligne[col.cle] ?? '—')}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {!chargement && affichees.length === 0 && <div className="dt-vide">{vide}</div>}
        {chargement && <div className="dt-vide">Chargement…</div>}
      </div>

      {(onPage || paginationLocale) && (
        <div className="dt-pagination">
          <span>{nbLignes} résultat(s)</span>
          <div>
            <button className="btn" disabled={pageCourante <= 1} onClick={() => allerA(pageCourante - 1)}>‹ Précédent</button>
            <span>Page {pageCourante} / {nbPages}</span>
            <button className="btn" disabled={pageCourante >= nbPages} onClick={() => allerA(pageCourante + 1)}>Suivant ›</button>
          </div>
        </div>
      )}
    </div>
  )
}
