// Liste des formateurs : filtres (type, spécialité, expérience), recherche, tri et pagination côté serveur.
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import Notification from '../../components/Notification'
import SearchBox from '../../components/SearchBox'
import FormateurForm from './FormateurForm'
import { TAILLE_PAGE, TYPES_FORMATEUR, libelleType, nettoyer } from './commun'
import './ala.css'

const FILTRES_VIDES = { q: '', type: '', specialite: '', experience_min: '' }

// Les clés triables correspondent au paramètre « tri » de l'API
const COLONNES = [
  { cle: 'nom', titre: 'Nom', triable: true, rendu: (f) => f.nom_complet },
  { cle: 'type', titre: 'Type', triable: true, rendu: (f) => libelleType(f.type) },
  { cle: 'specialite', titre: 'Spécialité' },
  { cle: 'experience', titre: 'Expérience', triable: true, rendu: (f) => (f.experience != null ? `${f.experience} ans` : '—') },
  { cle: 'nb_cours', titre: 'Cours', triable: true },
]

export default function FormateursListe() {
  const navigate = useNavigate()
  const location = useLocation()
  const [filtres, setFiltres] = useState(FILTRES_VIDES)
  const [page, setPage] = useState(1)
  const [tri, setTri] = useState({ cle: 'nom', ordre: 'asc' })
  const [formOuvert, setFormOuvert] = useState(false)
  const [notification, setNotification] = useState(location.state?.notification ?? null)

  const { data, loading, error } = useApi(
    () => client.get('/formateurs', {
      params: nettoyer({ ...filtres, page, taille: TAILLE_PAGE, tri: tri.cle, ordre: tri.ordre }),
    }).then((r) => r.data),
    [filtres, page, tri],
  )

  // Tout changement de filtre ramène à la page 1
  const filtrer = (cle, valeur) => { setFiltres({ ...filtres, [cle]: valeur }); setPage(1) }

  return (
    <div>
      <div className="entete-page">
        <h1>Formateurs</h1>
        <button className="btn primaire" onClick={() => setFormOuvert(true)}>+ Nouveau formateur</button>
      </div>

      <FilterBar onReinitialiser={() => { setFiltres(FILTRES_VIDES); setPage(1) }}>
        <label>Recherche (nom, prénom)
          <SearchBox valeur={filtres.q} onChange={(v) => filtrer('q', v)} />
        </label>
        <label>Type
          <select value={filtres.type} onChange={(e) => filtrer('type', e.target.value)}>
            <option value="">Tous</option>
            {Object.entries(TYPES_FORMATEUR).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>Spécialité contient
          <SearchBox valeur={filtres.specialite} onChange={(v) => filtrer('specialite', v)} placeholder="ex. devops" />
        </label>
        <label>Expérience min.
          <input type="number" min="0" style={{ width: 90 }} value={filtres.experience_min}
                 onChange={(e) => filtrer('experience_min', e.target.value)} />
        </label>
      </FilterBar>

      {error && <p className="erreur">{error}</p>}
      <DataTable colonnes={COLONNES} lignes={data?.donnees} chargement={loading}
                 tri={tri} onTri={(t) => { setTri(t); setPage(1) }}
                 page={page} taille={TAILLE_PAGE} total={data?.total ?? 0} onPage={setPage}
                 onClicLigne={(f) => navigate(`/formateurs/${f.id}`)} />

      <FormateurForm ouvert={formOuvert} formateur={null} onFermer={() => setFormOuvert(false)}
                     onEnregistre={(f) => navigate(`/formateurs/${f.id}`, { state: { notification: `Formateur « ${f.nom_complet} » créé.` } })} />
      <Notification message={notification} onFermer={() => setNotification(null)} />
    </div>
  )
}
