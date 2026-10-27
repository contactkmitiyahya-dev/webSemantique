// Fiche d'un organisme : formations proposées et certifications délivrées (cliquables).
import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import ConfirmDialog from '../../components/ConfirmDialog'
import Notification from '../../components/Notification'
import OrganismeForm from './OrganismeForm'
import Liens from './Liens'
import { libelleType } from './commun'
import './ala.css'

export default function OrganismeFiche() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [formOuvert, setFormOuvert] = useState(false)
  const [confirmation, setConfirmation] = useState(false)
  const [enCours, setEnCours] = useState(false)
  const [notif, setNotif] = useState({ message: location.state?.notification ?? null, type: 'succes' })

  const { data: o, loading, error, reload } = useApi(
    () => client.get(`/organismes/${id}`).then((r) => r.data), [id],
  )

  const supprimer = async () => {
    setEnCours(true)
    try {
      await client.delete(`/organismes/${id}`)
      navigate('/organismes', { state: { notification: `Organisme « ${o.label} » supprimé.` } })
    } catch (e) {
      setConfirmation(false)
      setNotif({ message: e.message, type: 'erreur' })
    } finally {
      setEnCours(false)
    }
  }

  if (loading && !o) return <p>Chargement…</p>
  if (error) return <div><p className="erreur">{error}</p><Link to="/organismes">← Retour à la liste</Link></div>

  return (
    <div>
      <Link to="/organismes" className="retour">← Organismes</Link>
      <div className="entete-page">
        <div>
          <h1>{o.label}</h1>
          <span className="badge">{libelleType(o.type)}</span>
        </div>
        <div className="actions">
          <button className="btn" onClick={() => setFormOuvert(true)}>Modifier</button>
          <button className="btn danger" onClick={() => setConfirmation(true)}>Supprimer</button>
        </div>
      </div>

      <section className="carte">
        <dl className="proprietes">
          <dt>Identifiant</dt><dd><code>{o.id}</code></dd>
          <dt>Type</dt><dd>{libelleType(o.type)}</dd>
        </dl>
      </section>

      <div className="grille-relations">
        <Liens titre="Formations proposées" liens={o.formations} route="formations" />
        <Liens titre="Certifications délivrées" liens={o.certifications} route="certifications" />
      </div>

      <OrganismeForm ouvert={formOuvert} organisme={o} onFermer={() => setFormOuvert(false)}
                     onEnregistre={() => { setFormOuvert(false); setNotif({ message: 'Modifications enregistrées.', type: 'succes' }); reload() }} />
      <ConfirmDialog ouvert={confirmation} enCours={enCours}
                     message={`Supprimer définitivement « ${o.label} » ? Ses liens vers les formations et certifications seront aussi supprimés.`}
                     onConfirmer={supprimer} onAnnuler={() => setConfirmation(false)} />
      <Notification message={notif.message} type={notif.type} onFermer={() => setNotif({ message: null, type: 'succes' })} />
    </div>
  )
}
