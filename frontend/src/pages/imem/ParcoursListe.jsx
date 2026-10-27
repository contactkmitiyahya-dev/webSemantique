// Liste des parcours (Imem) : recherche, filtres type / module / animateur, pagination côté serveur.
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import Notification from '../../components/Notification'
import SearchBox from '../../components/SearchBox'
import { TAILLE_PAGE, classe, nettoyer } from './format'
import './imem.css'

const FILTRES_VIDES = { q: '', type: '', module: '', animateur: '' }

const COLONNES = [
  { cle: 'label', titre: 'Parcours', rendu: (p) => <strong>{p.label}</strong> },
  { cle: 'type', titre: 'Type', rendu: (p) => classe(p.type) },
  { cle: 'nbModules', titre: 'Modules', align: 'droite' },
  { cle: 'nbApprenants', titre: 'Apprenants', align: 'droite' },
  { cle: 'animateurs', titre: 'Animé par', rendu: (p) => p.animateurs || '—' },
]

export default function ParcoursListe() {
  const navigate = useNavigate()
  const location = useLocation()
  const [filtres, setFiltres] = useState(FILTRES_VIDES)
  const [page, setPage] = useState(1)
  const [notification, setNotification] = useState(location.state?.notification ?? null)

  const { data, loading, error } = useApi(
    () => client.get('/parcours', { params: nettoyer({ ...filtres, page, taille: TAILLE_PAGE }) }).then((r) => r.data),
    [filtres, page],
  )
  const { data: options } = useApi(() => client.get('/parcours/options').then((r) => r.data), [])

  // Tout changement de filtre ramène à la page 1
  const filtrer = (cle, valeur) => { setFiltres({ ...filtres, [cle]: valeur }); setPage(1) }

  return (
    <div>
      <div className="entete">
        <h1>Parcours</h1>
        <Link className="btn primaire" to="/parcours/nouveau">+ Nouveau parcours</Link>
      </div>

      <FilterBar onReinitialiser={() => { setFiltres(FILTRES_VIDES); setPage(1) }}>
        <label>Recherche (libellé)
          <SearchBox valeur={filtres.q} onChange={(v) => filtrer('q', v)} placeholder="ex. devops" />
        </label>
        <label>Type
          <select value={filtres.type} onChange={(e) => filtrer('type', e.target.value)}>
            <option value="">Tous</option>
            {options?.types.filter((t) => t.id !== 'Parcours').map((t) => <option key={t.id} value={t.id}>{classe(t.id)}</option>)}
          </select>
        </label>
        <label>Contient le module
          <select value={filtres.module} onChange={(e) => filtrer('module', e.target.value)}>
            <option value="">Tous</option>
            {options?.modules.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </label>
        <label>Animé par
          <select value={filtres.animateur} onChange={(e) => filtrer('animateur', e.target.value)}>
            <option value="">Tous</option>
            {options?.animateurs.map((a) => <option key={a.id} value={a.id}>{a.label}</option>)}
          </select>
        </label>
      </FilterBar>

      {error && <p className="erreur">{error}</p>}
      <DataTable colonnes={COLONNES} lignes={data?.donnees} chargement={loading}
                 page={page} taille={TAILLE_PAGE} total={data?.total ?? 0} onPage={setPage}
                 onClicLigne={(p) => navigate(`/parcours/${p.id}`)} />

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
