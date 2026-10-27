// Formulaire de création / modification d'une formation (Imem), sur sa propre page.
// Mêmes contrôles que l'API : au moins un module et un domaine, fin après début, coût >= 0.
// PUT = remplacement complet : le formulaire renvoie toujours tous les champs.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import ChoixMultiple from './ChoixMultiple'
import { NIVEAUX, classe, versInputDate } from './format'
import './imem.css'

const VIDE = {
  intitule: '', type: 'FormationCourte', dureeHeures: '', niveauDifficulte: '', creditsECTS: '',
  coutFormation: '', dateDebut: '', dateFin: '', nombrePlaces: '', estActif: true,
  modules: [], domaines: [], organismes: [], responsables: [], certification: null,
}
const ids = (liste) => (liste ?? []).map((x) => x.id)
const nombre = (v) => (v === '' || v == null ? null : Number(v))

// Valeurs du formulaire à partir d'une fiche de l'API
function versFormulaire(d) {
  return {
    intitule: d.intitule ?? '', type: d.types[0] ?? 'Formation', dureeHeures: d.dureeHeures ?? '',
    niveauDifficulte: d.niveauDifficulte ?? '', creditsECTS: d.creditsECTS ?? '', coutFormation: d.coutFormation ?? '',
    dateDebut: versInputDate(d.dateDebut), dateFin: versInputDate(d.dateFin), nombrePlaces: d.nombrePlaces ?? '',
    estActif: d.estActif !== false, modules: ids(d.modules), domaines: ids(d.domaines),
    organismes: ids(d.organismes), responsables: ids(d.responsables), certification: d.certification?.id ?? null,
  }
}

export default function FormationForm() {
  const { id } = useParams()
  const modification = Boolean(id)
  const navigate = useNavigate()
  const { data: options, error: erreurOptions } = useApi(() => client.get('/formations/options').then((r) => r.data), [])
  const [form, setForm] = useState(VIDE)
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)

  useEffect(() => {
    if (!modification) return
    client.get(`/formations/${id}`).then((r) => setForm(versFormulaire(r.data))).catch((e) => setErreur(e.message))
  }, [id, modification])

  const changer = (cle) => (e) => setForm({ ...form, [cle]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const choisir = (cle) => (valeur) => setForm({ ...form, [cle]: valeur })

  function verifier() {
    if (form.intitule.trim().length < 2) return "L'intitulé est obligatoire."
    if (!form.modules.length) return 'Choisir au moins un module.'
    if (!form.domaines.length) return 'Choisir au moins un domaine.'
    if (form.coutFormation !== '' && Number(form.coutFormation) < 0) return 'Le coût doit être positif ou nul.'
    if (form.dateDebut && form.dateFin && form.dateFin <= form.dateDebut) return 'La date de fin doit être après la date de début.'
    return null
  }

  const valider = async (e) => {
    e.preventDefault() // pas de rechargement de page
    const message = verifier()
    if (message) return setErreur(message)
    const corps = {
      ...form, intitule: form.intitule.trim(), niveauDifficulte: form.niveauDifficulte || null,
      dureeHeures: nombre(form.dureeHeures), creditsECTS: nombre(form.creditsECTS),
      coutFormation: nombre(form.coutFormation), nombrePlaces: nombre(form.nombrePlaces),
      dateDebut: form.dateDebut ? `${form.dateDebut}T00:00:00` : null,
      dateFin: form.dateFin ? `${form.dateFin}T00:00:00` : null,
    }
    setEnCours(true)
    setErreur(null)
    try {
      const r = modification ? await client.put(`/formations/${id}`, corps) : await client.post('/formations', corps)
      navigate(`/formations/${r.data.id}`, {
        state: { notification: modification ? 'Modifications enregistrées.' : `Formation « ${r.data.intitule} » créée.` },
      })
    } catch (err) {
      setErreur(err.message) // message lisible fourni par client.js (detail du back)
    } finally {
      setEnCours(false)
    }
  }

  if (erreurOptions) return <p className="erreur">{erreurOptions}</p>
  if (!options) return <p>Chargement…</p>
  const retour = modification ? `/formations/${id}` : '/formations'

  return (
    <div>
      <Link to={retour} className="retour">← Retour</Link>
      <h1>{modification ? 'Modifier la formation' : 'Nouvelle formation'}</h1>
      <form className="formulaire" onSubmit={valider} noValidate>
        <div className="grille-champs">
          <label className="large">Intitulé *
            <input value={form.intitule} onChange={changer('intitule')} maxLength={200} />
          </label>
          <label>Type *
            <select value={form.type} onChange={changer('type')}>
              {options.types.map((t) => <option key={t.id} value={t.id}>{classe(t.id)}</option>)}
            </select>
          </label>
          <label>Niveau
            <select value={form.niveauDifficulte} onChange={changer('niveauDifficulte')}>
              <option value="">—</option>
              {NIVEAUX.map((n) => <option key={n}>{n}</option>)}
            </select>
          </label>
          <label>Durée (heures)<input type="number" min="1" value={form.dureeHeures} onChange={changer('dureeHeures')} /></label>
          <label>Crédits ECTS<input type="number" min="0" value={form.creditsECTS} onChange={changer('creditsECTS')} /></label>
          <label>Coût (DT, 0 = gratuit)
            <input type="number" min="0" step="10" value={form.coutFormation} onChange={changer('coutFormation')} />
          </label>
          <label>Nombre de places<input type="number" min="0" value={form.nombrePlaces} onChange={changer('nombrePlaces')} /></label>
          <label>Date de début<input type="date" value={form.dateDebut} onChange={changer('dateDebut')} /></label>
          <label>Date de fin
            <input type="date" value={form.dateFin} min={form.dateDebut || undefined} onChange={changer('dateFin')} />
          </label>
          <label className="case">
            <input type="checkbox" checked={form.estActif} onChange={changer('estActif')} /> Formation active
          </label>
        </div>

        <div className="colonnes-2">
          <ChoixMultiple titre="Modules" requis options={options.modules} valeur={form.modules} onChange={choisir('modules')} />
          <ChoixMultiple titre="Domaines" requis options={options.domaines} valeur={form.domaines} onChange={choisir('domaines')} />
          <ChoixMultiple titre="Proposée par" options={options.organismes} valeur={form.organismes} onChange={choisir('organismes')} />
          <ChoixMultiple titre="Responsables" options={options.responsables} valeur={form.responsables} onChange={choisir('responsables')} />
          <ChoixMultiple titre="Certification visée (au plus une)" unique options={options.certification}
                         valeur={form.certification} onChange={choisir('certification')} />
        </div>

        {erreur && <p className="erreur">{erreur}</p>}
        <div className="boutons">
          <Link className="btn" to={retour}>Annuler</Link>
          <button type="submit" className="btn primaire" disabled={enCours}>{enCours ? 'Enregistrement…' : 'Enregistrer'}</button>
        </div>
      </form>
    </div>
  )
}
