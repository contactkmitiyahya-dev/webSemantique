// Fiche d'un parcours (Imem) : modules ordonnés par prérequis (aPourPrerequis+), animateurs, apprenants.
import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import ConfirmDialog from '../../components/ConfirmDialog'
import Notification from '../../components/Notification'
import { Bloc } from './Affichage'
import { ROUTES, classe } from './format'
import './imem.css'

export default function ParcoursFiche() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [confirmation, setConfirmation] = useState(false)
  const [suppressionEnCours, setSuppressionEnCours] = useState(false)
  const [notification, setNotification] = useState(location.state?.notification ?? null)
  const [typeNotif, setTypeNotif] = useState('succes')

  const { data: p, loading, error } = useApi(() => client.get(`/parcours/${id}`).then((r) => r.data), [id])

  const supprimer = async () => {
    setSuppressionEnCours(true)
    try {
      await client.delete(`/parcours/${id}`)
      navigate('/parcours', { state: { notification: `Parcours « ${p.label} » supprimé.` } })
    } catch (e) {
      setConfirmation(false)
      setTypeNotif('erreur')
      setNotification(e.message)
    } finally {
      setSuppressionEnCours(false)
    }
  }

  if (loading && !p) return <p>Chargement…</p>
  if (error) return <div><p className="erreur">{error}</p><Link to="/parcours">← Parcours</Link></div>

  return (
    <div>
      <Link to="/parcours" className="retour">← Parcours</Link>
      <div className="entete">
        <div>
          <h1>{p.label}</h1>
          <p className="sous-titre">{p.types.map(classe).join(', ')} · <code>{p.id}</code></p>
        </div>
        <div className="boutons">
          <Link className="btn" to={`/parcours/${id}/modifier`}>Modifier</Link>
          <button className="btn danger" onClick={() => setConfirmation(true)}>Supprimer</button>
        </div>
      </div>

      <section className="bloc">
        <h3>Étapes du parcours <span className="doux">(ordonnées par nombre de prérequis)</span></h3>
        <ol className="etapes">
          {p.modules.map((m) => (
            <li key={m.id}>
              <strong>{m.label}</strong>
              <span className="doux"> — {m.nbPrerequis ? `${m.nbPrerequis} prérequis` : 'aucun prérequis'}</span>
            </li>
          ))}
        </ol>
      </section>
      <div className="blocs">
        <Bloc titre="Animé par" items={p.animateurs} route={ROUTES.Formateur} vide="Aucun animateur." />
        <Bloc titre="Apprenants qui le suivent" items={p.apprenants} vide="Aucun apprenant." />
      </div>

      <ConfirmDialog ouvert={confirmation} enCours={suppressionEnCours}
                     message={`Supprimer définitivement « ${p.label} » ? Les apprenants qui le suivent n'y seront plus rattachés.`}
                     onConfirmer={supprimer} onAnnuler={() => setConfirmation(false)} />
      <Notification message={notification} type={typeNotif} onFermer={() => setNotification(null)} />
    </div>
  )
}
