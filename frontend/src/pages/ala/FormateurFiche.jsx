// Fiche d'un formateur : propriétés, cours / apprenants / parcours (cliquables), modification, suppression.
import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import ConfirmDialog from '../../components/ConfirmDialog'
import Notification from '../../components/Notification'
import FormateurForm from './FormateurForm'
import Liens from './Liens'
import { libelleType } from './commun'
import './ala.css'

export default function FormateurFiche() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [formOuvert, setFormOuvert] = useState(false)
  const [confirmation, setConfirmation] = useState(false)
  const [suppressionEnCours, setSuppressionEnCours] = useState(false)
  const [notification, setNotification] = useState(location.state?.notification ?? null)
  const [typeNotif, setTypeNotif] = useState('succes')

  const { data: f, loading, error, reload } = useApi(
    () => client.get(`/formateurs/${id}`).then((r) => r.data), [id],
  )

  const supprimer = async () => {
    setSuppressionEnCours(true)
    try {
      await client.delete(`/formateurs/${id}`)
      navigate('/formateurs', { state: { notification: `Formateur « ${f.nom_complet} » supprimé.` } })
    } catch (e) {
      setConfirmation(false)
      setTypeNotif('erreur')
      setNotification(e.message)
    } finally {
      setSuppressionEnCours(false)
    }
  }

  if (loading && !f) return <p>Chargement…</p>
  if (error) return <div><p className="erreur">{error}</p><Link to="/formateurs">← Retour à la liste</Link></div>

  return (
    <div>
      <Link to="/formateurs" className="retour">← Formateurs</Link>
      <div className="entete-page">
        <div>
          <h1>{f.nom_complet}</h1>
          <span className="badge">{libelleType(f.type)}</span>
        </div>
        <div className="actions">
          <button className="btn" onClick={() => setFormOuvert(true)}>Modifier</button>
          <button className="btn danger" onClick={() => setConfirmation(true)}>Supprimer</button>
        </div>
      </div>

      <section className="carte">
        <dl className="proprietes">
          <dt>Identifiant</dt><dd><code>{f.id}</code></dd>
          <dt>Libellé</dt><dd>{f.label ?? '—'}</dd>
          <dt>Email</dt><dd>{f.email ? <a href={`mailto:${f.email}`}>{f.email}</a> : '—'}</dd>
          <dt>Téléphone</dt><dd>{f.telephone ?? '—'}</dd>
          <dt>Spécialité</dt><dd>{f.specialite ?? '—'}</dd>
          <dt>Expérience</dt><dd>{f.experience != null ? `${f.experience} ans` : '—'}</dd>
        </dl>
      </section>

      <div className="grille-relations">
        <Liens titre="Cours enseignés" liens={f.cours} route="cours" />
        <Liens titre="Apprenants encadrés" liens={f.apprenants} route="apprenants" />
        <Liens titre="Parcours animés" liens={f.parcours} route="parcours" />
      </div>

      <FormateurForm ouvert={formOuvert} formateur={f} onFermer={() => setFormOuvert(false)}
                     onEnregistre={() => { setFormOuvert(false); setTypeNotif('succes'); setNotification('Modifications enregistrées.'); reload() }} />
      <ConfirmDialog ouvert={confirmation} enCours={suppressionEnCours}
                     message={`Supprimer définitivement « ${f.nom_complet} » ? Tous ses liens (cours, apprenants, parcours) seront aussi supprimés.`}
                     onConfirmer={supprimer} onAnnuler={() => setConfirmation(false)} />
      <Notification message={notification} type={typeNotif} onFermer={() => setNotification(null)} />
    </div>
  )
}
