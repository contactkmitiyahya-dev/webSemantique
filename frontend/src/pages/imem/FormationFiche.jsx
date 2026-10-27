// Fiche d'une formation (Imem) : propriétés, modules, domaines, organismes, inscrits, places restantes.
import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import useApi from '../../api/useApi'
import ConfirmDialog from '../../components/ConfirmDialog'
import Notification from '../../components/Notification'
import { Bloc, Niveau, Places } from './Affichage'
import { ROUTES, classe, cout, date } from './format'
import './imem.css'

export default function FormationFiche() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [confirmation, setConfirmation] = useState(false)
  const [suppressionEnCours, setSuppressionEnCours] = useState(false)
  const [notification, setNotification] = useState(location.state?.notification ?? null)
  const [typeNotif, setTypeNotif] = useState('succes')

  const { data: f, loading, error } = useApi(() => client.get(`/formations/${id}`).then((r) => r.data), [id])

  const supprimer = async () => {
    setSuppressionEnCours(true)
    try {
      await client.delete(`/formations/${id}`)
      navigate('/formations', { state: { notification: `Formation « ${f.intitule} » supprimée.` } })
    } catch (e) {
      setConfirmation(false)
      setTypeNotif('erreur')
      setNotification(e.message)
    } finally {
      setSuppressionEnCours(false)
    }
  }

  if (loading && !f) return <p>Chargement…</p>
  if (error) return <div><p className="erreur">{error}</p><Link to="/formations">← Catalogue</Link></div>

  return (
    <div>
      <Link to="/formations" className="retour">← Catalogue</Link>
      <div className="entete">
        <div>
          <h1>{f.intitule}</h1>
          <p className="sous-titre">
            {f.types.map(classe).join(', ')} · <code>{f.id}</code>
            {f.estActif === false && <span className="pastille">inactive</span>}
          </p>
        </div>
        <div className="boutons">
          <Link className="btn" to={`/formations/${id}/modifier`}>Modifier</Link>
          <button className="btn danger" onClick={() => setConfirmation(true)}>Supprimer</button>
        </div>
      </div>

      <dl className="caracteristiques">
        <div><dt>Niveau</dt><dd><Niveau v={f.niveauDifficulte} /></dd></div>
        <div><dt>Durée</dt><dd>{f.dureeHeures ? `${f.dureeHeures} h` : '—'}</dd></div>
        <div><dt>Crédits ECTS</dt><dd>{f.creditsECTS ?? '—'}</dd></div>
        <div><dt>Coût</dt><dd>{cout(f.coutFormation)}</dd></div>
        <div><dt>Début</dt><dd>{date(f.dateDebut)}</dd></div>
        <div><dt>Fin</dt><dd>{date(f.dateFin)}</dd></div>
        <div><dt>Places restantes</dt><dd><Places places={f.nombrePlaces} restantes={f.placesRestantes} /></dd></div>
        <div><dt>Certification visée</dt><dd>{f.certification?.label ?? '—'}</dd></div>
      </dl>

      <div className="blocs">
        <Bloc titre="Modules" items={f.modules} />
        <Bloc titre="Domaines" items={f.domaines} />
        <Bloc titre="Proposée par" items={f.organismes} route={ROUTES.Organisme} />
        <Bloc titre="Responsables" items={f.responsables} />
        <Bloc titre="Apprenants inscrits" items={f.inscrits} vide="Aucun inscrit." />
      </div>

      <ConfirmDialog ouvert={confirmation} enCours={suppressionEnCours}
                     message={`Supprimer définitivement « ${f.intitule} » ? Les liens vers cette formation (inscriptions, organismes…) seront aussi supprimés.`}
                     onConfirmer={supprimer} onAnnuler={() => setConfirmation(false)} />
      <Notification message={notification} type={typeNotif} onFermer={() => setNotification(null)} />
    </div>
  )
}
