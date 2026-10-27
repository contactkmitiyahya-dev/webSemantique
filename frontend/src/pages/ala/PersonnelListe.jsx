// Personnel administratif (responsables + scolarité) : liste, filtre type, recherche,
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
import {
  EST_SCOLARITE, TAILLE_PAGE, TYPES_PERSONNEL, differences, idsModifiables, libelleType,
  liensLectureSeule, nettoyer,
} from './commun'
import './ala.css'

function versFormulaire(p) {
  return {
    type: p?.type ?? 'ResponsableDeFormation',
    nom: p?.nom ?? '',
    prenom: p?.prenom ?? '',
    email: p?.email ?? '',
    telephone: p?.telephone ?? '',
    formations: idsModifiables(p?.formations),
  }
}

// Formulaire (création si personne = null)
function PersonnelForm({ ouvert, ...props }) {
  // Monté seulement quand il est ouvert : son état repart de zéro à chaque ouverture
  return ouvert ? <ContenuPersonnelForm {...props} /> : null
}

function ContenuPersonnelForm({ personne, onFermer, onEnregistre }) {
  const creation = !personne
  const [form, setForm] = useState(versFormulaire(personne))
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)


  const changer = (cle) => (e) => setForm({ ...form, [cle]: e.target.value })
  const scolarite = EST_SCOLARITE(form.type)
  const autres = liensLectureSeule(personne?.formations)

  const valider = async () => {
    setEnCours(true)
    setErreur(null)
    // Un agent de scolarité n'administre aucune formation (classes disjointes)
    const valeurs = scolarite ? { ...form, formations: [] } : form
    try {
      const r = creation
        ? await client.post('/responsables', nettoyer(valeurs))
        : await client.put(`/responsables/${personne.id}`, differences(versFormulaire(personne), valeurs))
      onEnregistre(r.data, creation)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setEnCours(false)
    }
  }

  return (
    <FormModal ouvert titre={creation ? 'Nouveau membre du personnel' : `Modifier ${personne.nom_complet}`}
               onFermer={onFermer} onValider={valider} enCours={enCours} erreur={erreur}>
      <div className="grille-2">
        <label>Type *
          <select value={form.type} onChange={changer('type')}>
            {Object.entries(TYPES_PERSONNEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <span />
        <label>Nom *<input value={form.nom} onChange={changer('nom')} required /></label>
        <label>Prénom<input value={form.prenom} onChange={changer('prenom')} /></label>
        <label>Email<input type="email" value={form.email} onChange={changer('email')} /></label>
        <label>Téléphone<input value={form.telephone} onChange={changer('telephone')} /></label>
      </div>
      <div className="champ-relation">
        <span className="etiquette">Formations administrées</span>
        {scolarite ? (
          <p className="rs-aide">Un agent de scolarité n'administre pas de formation (classes disjointes dans l'ontologie).</p>
        ) : (
          <RelationSelect ressource="formations" valeurs={form.formations} placeholder="ex. Formation_Backend"
                          onChange={(ids) => setForm({ ...form, formations: ids })} />
        )}
        {autres.length > 0 && (
          <p className="rs-aide">Aussi lié, défini par une autre partie (non modifiable ici) : {autres.map((l) => l.label).join(', ')}</p>
        )}
      </div>
    </FormModal>
  )
}

export default function PersonnelListe() {
  const [q, setQ] = useState('')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [edition, setEdition] = useState(null)       // { personne } ou null ; personne = null => création
  const [aSupprimer, setASupprimer] = useState(null)
  const [enCours, setEnCours] = useState(false)
  const [notif, setNotif] = useState({ message: null, type: 'succes' })

  const { data, loading, error, reload } = useApi(
    () => client.get('/responsables', { params: nettoyer({ q, type, page, taille: TAILLE_PAGE }) }).then((r) => r.data),
    [q, type, page],
  )

  // La modification a besoin de la fiche complète (formations avec « modifiable »)
  const ouvrirModification = async (ligne) => {
    try {
      const r = await client.get(`/responsables/${ligne.id}`)
      setEdition({ personne: r.data })
    } catch (e) {
      setNotif({ message: e.message, type: 'erreur' })
    }
  }

  const supprimer = async () => {
    setEnCours(true)
    try {
      await client.delete(`/responsables/${aSupprimer.id}`)
      setNotif({ message: `« ${aSupprimer.nom_complet} » supprimé.`, type: 'succes' })
      reload()
    } catch (e) {
      setNotif({ message: e.message, type: 'erreur' })
    } finally {
      setEnCours(false)
      setASupprimer(null)
    }
  }

  const colonnes = [
    { cle: 'nom_complet', titre: 'Nom', triable: true },
    { cle: 'type', titre: 'Type', triable: true, rendu: (p) => libelleType(p.type) },
    { cle: 'categorie', titre: 'Catégorie', triable: true, rendu: (p) => libelleType(p.categorie) },
    { cle: 'email', titre: 'Email' },
    { cle: 'nb_formations', titre: 'Formations', triable: true },
    {
      cle: 'actions', titre: '', rendu: (p) => (
        <div className="actions">
          <button className="btn petit" onClick={() => ouvrirModification(p)}>Modifier</button>
          <button className="btn petit danger" onClick={() => setASupprimer(p)}>Supprimer</button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="entete-page">
        <h1>Personnel</h1>
        <button className="btn primaire" onClick={() => setEdition({ personne: null })}>+ Nouveau</button>
      </div>

      <FilterBar onReinitialiser={() => { setQ(''); setType(''); setPage(1) }}>
        <label>Recherche (nom, prénom)
          <SearchBox valeur={q} onChange={(v) => { setQ(v); setPage(1) }} />
        </label>
        <label>Type
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(1) }}>
            <option value="">Tous</option>
            {Object.entries(TYPES_PERSONNEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
      </FilterBar>

      {error && <p className="erreur">{error}</p>}
      <DataTable colonnes={colonnes} lignes={data?.donnees} chargement={loading}
                 page={page} taille={TAILLE_PAGE} total={data?.total ?? 0} onPage={setPage} />
      <p className="doux">Les formations administrées sont visibles dans le formulaire « Modifier ». Voir aussi les <Link to="/formateurs">formateurs</Link>.</p>

      <PersonnelForm ouvert={!!edition} personne={edition?.personne ?? null} onFermer={() => setEdition(null)}
                     onEnregistre={(p, creation) => {
                       setEdition(null)
                       setNotif({ message: `« ${p.nom_complet} » ${creation ? 'créé' : 'modifié'}.`, type: 'succes' })
                       reload()
                     }} />
      <ConfirmDialog ouvert={!!aSupprimer} enCours={enCours}
                     message={`Supprimer définitivement « ${aSupprimer?.nom_complet} » et tous ses liens ?`}
                     onConfirmer={supprimer} onAnnuler={() => setASupprimer(null)} />
      <Notification message={notif.message} type={notif.type} onFermer={() => setNotif({ message: null, type: 'succes' })} />
    </div>
  )
}
