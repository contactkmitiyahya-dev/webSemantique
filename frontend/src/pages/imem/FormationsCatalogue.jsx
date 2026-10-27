// Catalogue des formations (Imem) : filtres -> paramètres d'API -> requête SPARQL (affichée en bas).
// Filtres, tri et page sont gardés dans l'URL : un lien filtré peut être partagé.
import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import Notification from '../../components/Notification'
import SearchBox from '../../components/SearchBox'
import { Niveau, Places } from './Affichage'
import { NIVEAUX, TAILLE_PAGE, classe, cout, date, nettoyer } from './format'
import './imem.css'

const FILTRES = ['q', 'type', 'niveau', 'domaine', 'cout_max', 'duree_max', 'actif', 'a_venir']

// Les clés triables correspondent au paramètre « tri » de l'API
const COLONNES = [
  { cle: 'intitule', titre: 'Intitulé', triable: true,
    rendu: (f) => <><strong>{f.intitule}</strong> {f.actif === false && <span className="pastille">inactive</span>}</> },
  { cle: 'type', titre: 'Type', rendu: (f) => classe(f.type) },
  { cle: 'niveau', titre: 'Niveau', rendu: (f) => <Niveau v={f.niveau} /> },
  { cle: 'duree', titre: 'Durée', triable: true, align: 'droite', rendu: (f) => (f.duree ? `${f.duree} h` : '—') },
  { cle: 'cout', titre: 'Coût', triable: true, align: 'droite', rendu: (f) => cout(f.cout) },
  { cle: 'debut', titre: 'Début', triable: true, rendu: (f) => date(f.dateDebut) },
  { cle: 'places', titre: 'Places restantes', triable: true,
    rendu: (f) => <Places places={f.places} restantes={f.places_restantes} /> },
]

export default function FormationsCatalogue() {
  const navigate = useNavigate()
  const location = useLocation()
  const [sp, setSp] = useSearchParams()
  const [notification, setNotification] = useState(location.state?.notification ?? null)

  const filtres = Object.fromEntries(FILTRES.map((f) => [f, sp.get(f) ?? '']))
  const page = Number(sp.get('page') || 1)
  const tri = { cle: sp.get('tri') || 'intitule', ordre: sp.get('ordre') || 'asc' }

  const { data, loading, error } = useApi(
    () => client.get('/formations', {
      params: nettoyer({ ...filtres, page, taille: TAILLE_PAGE, tri: tri.cle, ordre: tri.ordre }),
    }).then((r) => r.data),
    [sp.toString()],
  )
  const { data: options } = useApi(() => client.get('/formations/options').then((r) => r.data), [])

  // Tout changement de filtre ou de tri ramène à la page 1
  const changer = (valeurs, garderPage = false) => {
    const suivant = { ...filtres, tri: tri.cle, ordre: tri.ordre, ...(garderPage ? { page } : {}), ...valeurs }
    setSp(nettoyer(suivant))
  }
  const filtrer = (cle) => (e) => changer({ [cle]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  return (
    <div>
      <div className="entete">
        <h1>Catalogue des formations</h1>
        <Link className="btn primaire" to="/formations/nouvelle">+ Nouvelle formation</Link>
      </div>

      <FilterBar onReinitialiser={() => setSp({})}>
        <label>Recherche (intitulé)
          <SearchBox valeur={filtres.q} onChange={(q) => changer({ q })} placeholder="ex. react" />
        </label>
        <label>Type
          <select value={filtres.type} onChange={filtrer('type')}>
            <option value="">Tous</option>
            {options?.types.filter((t) => t.id !== 'Formation').map((t) => <option key={t.id} value={t.id}>{classe(t.id)}</option>)}
          </select>
        </label>
        <label>Niveau
          <select value={filtres.niveau} onChange={filtrer('niveau')}>
            <option value="">Tous</option>
            {NIVEAUX.map((n) => <option key={n}>{n}</option>)}
          </select>
        </label>
        <label>Domaine
          <select value={filtres.domaine} onChange={filtrer('domaine')}>
            <option value="">Tous</option>
            {options?.domaines.map((d) => <option key={d.id} value={d.id}>{d.label}</option>)}
          </select>
        </label>
        <label>Coût max (DT)
          <input type="number" min="0" step="50" placeholder="ex. 1000" value={filtres.cout_max} onChange={filtrer('cout_max')} />
        </label>
        <label>Durée max (h)
          <input type="number" min="1" placeholder="ex. 100" value={filtres.duree_max} onChange={filtrer('duree_max')} />
        </label>
        <label>État
          <select value={filtres.actif} onChange={filtrer('actif')}>
            <option value="">Toutes</option>
            <option value="true">Actives</option>
            <option value="false">Inactives</option>
          </select>
        </label>
        <label className="case">
          <input type="checkbox" checked={filtres.a_venir === 'true'} onChange={filtrer('a_venir')} /> À venir seulement
        </label>
      </FilterBar>

      {error && <p className="erreur">{error}</p>}
      <DataTable colonnes={COLONNES} lignes={data?.donnees} chargement={loading}
                 tri={tri} onTri={(t) => changer({ tri: t.cle, ordre: t.ordre })}
                 page={page} taille={TAILLE_PAGE} total={data?.total ?? 0} onPage={(p) => changer({ page: p }, true)}
                 onClicLigne={(f) => navigate(`/formations/${f.id}`)} vide="Aucune formation ne correspond aux filtres." />

      {data?.sparql && (
        <details className="sparql">
          <summary>Requête SPARQL envoyée à Fuseki</summary>
          <pre>{data.sparql}</pre>
        </details>
      )}
      <Notification message={notification} onFermer={() => setNotification(null)} />
    </div>
  )
}
