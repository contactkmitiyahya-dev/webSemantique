// Liste des organismes : filtre par type (sous-classes comprises), recherche, pagination.
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import Notification from '../../components/Notification'
import SearchBox from '../../components/SearchBox'
import OrganismeForm from './OrganismeForm'
import { FILTRES_ORGANISME, TAILLE_PAGE, libelleType, nettoyer } from './commun'
import './ala.css'

const COLONNES = [
  { cle: 'label', titre: 'Organisme', triable: true },
  { cle: 'type', titre: 'Type', triable: true, rendu: (o) => libelleType(o.type) },
  { cle: 'nb_formations', titre: 'Formations', triable: true },
  { cle: 'nb_certifications', titre: 'Certifications', triable: true },
]

export default function OrganismesListe() {
  const navigate = useNavigate()
  const location = useLocation()
  const [q, setQ] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [formOuvert, setFormOuvert] = useState(false)
  const [notification, setNotification] = useState(location.state?.notification ?? null)

  const { data, loading, error } = useApi(
    () => client.get('/organismes', { params: nettoyer({ q, type, page, taille: TAILLE_PAGE }) }).then((r) => r.data),
    [q, type, page],
  )

  return (
    <div>
      <div className="entete-page">
        <h1>Organismes</h1>
        <button className="btn primaire" onClick={() => setFormOuvert(true)}>+ Nouvel organisme</button>
      </div>

      <FilterBar onReinitialiser={() => { setQ(''); setType(''); setPage(1) }}>
        <label>Recherche
          <SearchBox valeur={q} onChange={(v) => { setQ(v); setPage(1) }} />
        </label>
        <label>Type
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(1) }}>
            <option value="">Tous</option>
            {Object.entries(FILTRES_ORGANISME).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
      </FilterBar>

      {error && <p className="erreur">{error}</p>}
      <DataTable colonnes={COLONNES} lignes={data?.donnees} chargement={loading}
                 page={page} taille={TAILLE_PAGE} total={data?.total ?? 0} onPage={setPage}
                 onClicLigne={(o) => navigate(`/organismes/${o.id}`)} />

      <OrganismeForm ouvert={formOuvert} organisme={null} onFermer={() => setFormOuvert(false)}
                     onEnregistre={(o) => navigate(`/organismes/${o.id}`, { state: { notification: `Organisme « ${o.label} » créé.` } })} />
      <Notification message={notification} onFermer={() => setNotification(null)} />
    </div>
  )
}
