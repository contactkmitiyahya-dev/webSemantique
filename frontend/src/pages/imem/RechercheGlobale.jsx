// Recherche globale (Imem, intégration finale) : résultats de tous les types, regroupés par catégorie.
import { useSearchParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import FilterBar from '../../components/FilterBar'
import SearchBox from '../../components/SearchBox'
import { Bloc } from './Affichage'
import { ROUTES, classe } from './format'
import './imem.css'

export default function RechercheGlobale() {
  const [sp, setSp] = useSearchParams()
  const q = sp.get('q') ?? ''
  const { data, loading, error } = useApi(
    () => (q.length >= 2 ? client.get('/recherche', { params: { q, taille: 100 } }).then((r) => r.data) : null),
    [q],
  )

  const groupes = {}
  for (const r of data?.donnees ?? []) (groupes[r.categorie] ??= []).push(r)

  return (
    <div>
      <h1>Recherche globale</h1>
      <FilterBar>
        <SearchBox valeur={q} onChange={(v) => setSp(v ? { q: v } : {})} placeholder="Formation, module, apprenant, compétence…" />
      </FilterBar>
      {q.length < 2 && <p className="doux">Saisir au moins 2 caractères.</p>}
      {q.length >= 2 && loading && <p className="doux">Recherche…</p>}
      {error && <p className="erreur">{error}</p>}
      {q.length >= 2 && data && (
        <>
          <p className="doux">{data.total} résultat(s) pour « {q} »</p>
          <div className="blocs">
            {Object.entries(groupes).map(([categorie, items]) => (
              <Bloc key={categorie} titre={classe(categorie)} items={items} route={ROUTES[categorie]} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
