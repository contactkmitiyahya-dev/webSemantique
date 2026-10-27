// Domaines : liste (filtre type, recherche), formations du domaine dépliables,
// création / modification dans une fenêtre, suppression avec confirmation.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import ConfirmDialog from '../../components/ConfirmDialog'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import FormModal from '../../components/FormModal'
import Notification from '../../components/Notification'
import RelationSelect from '../../components/RelationSelect'
import SearchBox from '../../components/SearchBox'
import Liens from './Liens'
import {
  FILTRES_DOMAINE, TAILLE_PAGE, TYPES_DOMAINE, differences, idsModifiables, libelleType,
  liensLectureSeule, nettoyer,
} from './commun'
import './ala.css'

function versFormulaire(d) {
  return { type: d?.type ?? 'DeveloppementWeb', intitule: d?.intitule ?? '', formations: idsModifiables(d?.formations) }
}

function DomaineForm({ ouvert, ...props }) {
  // Monté seulement quand il est ouvert : son état repart de zéro à chaque ouverture
  return ouvert ? <ContenuDomaineForm {...props} /> : null
}

function ContenuDomaineForm({ domaine, onFermer, onEnregistre }) {
  const creation = !domaine
  const [form, setForm] = useState(versFormulaire(domaine))
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)

  const valider = async () => {
    setEnCours(true)
    setErreur(null)
    try {
      const r = creation
        ? await client.post('/domaines', nettoyer(form))
        : await client.put(`/domaines/${domaine.id}`, differences(versFormulaire(domaine), form))
      onEnregistre(r.data, creation)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setEnCours(false)
    }
  }

  const autres = liensLectureSeule(domaine?.formations)
  return (
    <FormModal ouvert titre={creation ? 'Nouveau domaine' : `Modifier ${domaine.intitule}`}
               onFermer={onFermer} onValider={valider} enCours={enCours} erreur={erreur}>
      <label>Type *
        <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
          {Object.entries(TYPES_DOMAINE).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </label>
      <label>Intitulé *
        <input value={form.intitule} onChange={(e) => setForm({ ...form, intitule: e.target.value })} required />
      </label>
      <div className="champ-relation">
        <span className="etiquette">Formations du domaine</span>
        <RelationSelect ressource="formations" valeurs={form.formations} placeholder="ex. Formation_Frontend"
                        onChange={(ids) => setForm({ ...form, formations: ids })} />
        {autres.length > 0 && (
          <p className="rs-aide">Aussi lié, défini par une autre partie (non modifiable ici) : {autres.map((l) => l.label).join(', ')}</p>
        )}
      </div>
    </FormModal>
  )
}

export default function DomainesListe() {
  const [q, setQ] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [ouvert, setOuvert] = useState(null)          // fiche du domaine déplié
  const [edition, setEdition] = useState(null)        // { domaine } ; domaine = null => création
  const [aSupprimer, setASupprimer] = useState(null)
  const [enCours, setEnCours] = useState(false)
  const [notif, setNotif] = useState({ message: null, type: 'succes' })

  const { data, loading, error, reload } = useApi(
    () => client.get('/domaines', { params: nettoyer({ q, type, page, taille: TAILLE_PAGE }) }).then((r) => r.data),
    [q, type, page],
  )

  // Clic sur une ligne : charge la fiche et affiche ses formations sous le tableau
  const afficher = async (ligne) => {
    try {
      const r = await client.get(`/domaines/${ligne.id}`)
      setOuvert(r.data)
    } catch (e) {
      setNotif({ message: e.message, type: 'erreur' })
    }
  }

  const supprimer = async () => {
    setEnCours(true)
    try {
      await client.delete(`/domaines/${aSupprimer.id}`)
      setNotif({ message: `Domaine « ${aSupprimer.intitule} » supprimé.`, type: 'succes' })
      if (ouvert?.id === aSupprimer.id) setOuvert(null)
      reload()
    } catch (e) {
      setNotif({ message: e.message, type: 'erreur' })
    } finally {
      setEnCours(false)
      setASupprimer(null)
    }
  }

  const colonnes = [
    { cle: 'intitule', titre: 'Domaine', triable: true },
    { cle: 'type', titre: 'Type', triable: true, rendu: (d) => libelleType(d.type) },
    { cle: 'nb_formations', titre: 'Formations', triable: true },
    {
      cle: 'actions', titre: '', rendu: (d) => (
        // stopPropagation : un clic sur un bouton ne déplie pas la ligne
        <div className="actions" onClick={(e) => e.stopPropagation()}>
          <button className="btn petit" onClick={async () => {
            const r = await client.get(`/domaines/${d.id}`).catch((e) => setNotif({ message: e.message, type: 'erreur' }))
            if (r) setEdition({ domaine: r.data })
          }}>Modifier</button>
          <button className="btn petit danger" onClick={() => setASupprimer(d)}>Supprimer</button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="entete-page">
        <h1>Domaines</h1>
        <button className="btn primaire" onClick={() => setEdition({ domaine: null })}>+ Nouveau domaine</button>
      </div>

      <FilterBar onReinitialiser={() => { setQ(''); setType(''); setPage(1) }}>
        <label>Recherche
          <SearchBox valeur={q} onChange={(v) => { setQ(v); setPage(1) }} />
        </label>
        <label>Type
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(1) }}>
            <option value="">Tous</option>
            {Object.entries(FILTRES_DOMAINE).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
      </FilterBar>

      {error && <p className="erreur">{error}</p>}
      <DataTable colonnes={colonnes} lignes={data?.donnees} chargement={loading}
                 page={page} taille={TAILLE_PAGE} total={data?.total ?? 0} onPage={setPage}
                 onClicLigne={afficher} />

      {ouvert && (
        <div className="detail-deplie">
          <div className="entete-page">
            <h2>{ouvert.intitule} <span className="badge">{libelleType(ouvert.type)}</span></h2>
            <button className="btn petit" onClick={() => setOuvert(null)}>Fermer</button>
          </div>
          <Liens titre="Formations du domaine" liens={ouvert.formations} route="formations" />
        </div>
      )}
      <p className="doux">Cliquez sur un domaine pour voir ses formations. Organismes : <Link to="/organismes">voir la liste</Link>.</p>

      <DomaineForm ouvert={!!edition} domaine={edition?.domaine ?? null} onFermer={() => setEdition(null)}
                   onEnregistre={(d, creation) => {
                     setEdition(null)
                     setNotif({ message: `Domaine « ${d.intitule} » ${creation ? 'créé' : 'modifié'}.`, type: 'succes' })
                     if (ouvert?.id === d.id) setOuvert(d)
                     reload()
                   }} />
      <ConfirmDialog ouvert={!!aSupprimer} enCours={enCours}
                     message={`Supprimer définitivement le domaine « ${aSupprimer?.intitule} » et ses liens ?`}
                     onConfirmer={supprimer} onAnnuler={() => setASupprimer(null)} />
      <Notification message={notif.message} type={notif.type} onFermer={() => setNotif({ message: null, type: 'succes' })} />
    </div>
  )
}
