// Formulaire de création / modification d'un parcours (Imem) : au moins un module.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import ChoixMultiple from './ChoixMultiple'
import { classe } from './format'
import './imem.css'

export default function ParcoursForm() {
  const { id } = useParams()
  const modification = Boolean(id)
  const navigate = useNavigate()
  const { data: options, error: erreurOptions } = useApi(() => client.get('/parcours/options').then((r) => r.data), [])
  const [form, setForm] = useState({ label: '', type: 'ParcoursStandard', modules: [], animateurs: [] })
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)

  useEffect(() => {
    if (!modification) return
    client.get(`/parcours/${id}`).then(({ data: d }) => setForm({
      label: d.label, type: d.types[0] ?? 'Parcours',
      modules: d.modules.map((m) => m.id), animateurs: d.animateurs.map((a) => a.id),
    })).catch((e) => setErreur(e.message))
  }, [id, modification])

  const valider = async (e) => {
    e.preventDefault()
    if (form.label.trim().length < 2) return setErreur('Le libellé est obligatoire.')
    if (!form.modules.length) return setErreur('Un parcours doit comprendre au moins un module.')
    setEnCours(true)
    setErreur(null)
    try {
      const corps = { ...form, label: form.label.trim() }
      const r = modification ? await client.put(`/parcours/${id}`, corps) : await client.post('/parcours', corps)
      navigate(`/parcours/${r.data.id}`, {
        state: { notification: modification ? 'Modifications enregistrées.' : `Parcours « ${r.data.label} » créé.` },
      })
    } catch (err) {
      setErreur(err.message)
    } finally {
      setEnCours(false)
    }
  }

  if (erreurOptions) return <p className="erreur">{erreurOptions}</p>
  if (!options) return <p>Chargement…</p>
  const retour = modification ? `/parcours/${id}` : '/parcours'

  return (
    <div>
      <Link to={retour} className="retour">← Retour</Link>
      <h1>{modification ? 'Modifier le parcours' : 'Nouveau parcours'}</h1>
      <form className="formulaire" onSubmit={valider} noValidate>
        <div className="grille-champs">
          <label className="large">Libellé *
            <input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} maxLength={200} />
          </label>
          <label>Type *
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {options.types.map((t) => <option key={t.id} value={t.id}>{classe(t.id)}</option>)}
            </select>
          </label>
        </div>
        <div className="colonnes-2">
          <ChoixMultiple titre="Modules" requis options={options.modules} valeur={form.modules}
                         onChange={(modules) => setForm({ ...form, modules })} />
          <ChoixMultiple titre="Animateurs (formateurs)" options={options.animateurs} valeur={form.animateurs}
                         onChange={(animateurs) => setForm({ ...form, animateurs })} />
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
