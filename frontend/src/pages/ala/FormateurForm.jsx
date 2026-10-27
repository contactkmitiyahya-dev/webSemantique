// Formulaire de création / modification d'un formateur (fenêtre modale).
// Création : POST de tous les champs remplis. Modification : PUT des SEULS champs changés.
// Relations : seuls les liens écrits par Ala (modifiable: true) sont éditables ;
// les liens définis par une autre partie sont affichés en lecture seule.
import { useState } from 'react'
import client from '../../api/client'
import FormModal from '../../components/FormModal'
import RelationSelect from '../../components/RelationSelect'
import { TYPES_FORMATEUR, differences, idsModifiables, liensLectureSeule, nettoyer } from './commun'

const RELATIONS = [
  { cle: 'cours', titre: 'Cours enseignés', ressource: 'cours', exemple: 'ex. Cours_React' },
  { cle: 'apprenants', titre: 'Apprenants encadrés', ressource: 'apprenants', exemple: 'ex. Omar' },
  { cle: 'parcours', titre: 'Parcours animés', ressource: 'parcours', exemple: 'ex. Parcours_Backend' },
]

// Valeurs du formulaire à partir d'une fiche (ou vides pour une création)
function versFormulaire(f) {
  return {
    type: f?.type ?? 'FormateurPermanent',
    nom: f?.nom ?? '',
    prenom: f?.prenom ?? '',
    email: f?.email ?? '',
    telephone: f?.telephone ?? '',
    specialite: f?.specialite ?? '',
    experience: f?.experience ?? '',
    label: f?.label ?? '',
    cours: idsModifiables(f?.cours),
    apprenants: idsModifiables(f?.apprenants),
    parcours: idsModifiables(f?.parcours),
  }
}

export default function FormateurForm({ ouvert, ...props }) {
  // Monté seulement quand il est ouvert : son état repart de zéro à chaque ouverture
  return ouvert ? <ContenuFormateurForm {...props} /> : null
}

function ContenuFormateurForm({ formateur, onFermer, onEnregistre }) {
  const creation = !formateur
  const [form, setForm] = useState(versFormulaire(formateur))
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)


  const changer = (cle) => (e) => setForm({ ...form, [cle]: e.target.value })

  const valider = async () => {
    setEnCours(true)
    setErreur(null)
    const valeurs = { ...form, experience: form.experience === '' ? '' : Number(form.experience) }
    try {
      const reponse = creation
        ? await client.post('/formateurs', nettoyer(valeurs))
        : await client.put(`/formateurs/${formateur.id}`, differences(versFormulaire(formateur), valeurs))
      onEnregistre(reponse.data)
    } catch (e) {
      setErreur(e.message) // message lisible fourni par client.js (detail du back)
    } finally {
      setEnCours(false)
    }
  }

  return (
    <FormModal ouvert titre={creation ? 'Nouveau formateur' : `Modifier ${formateur.nom_complet}`}
               onFermer={onFermer} onValider={valider} enCours={enCours} erreur={erreur}>
      <div className="grille-2">
        <label>Type *
          <select value={form.type} onChange={changer('type')} required>
            {Object.entries(TYPES_FORMATEUR).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>Expérience (années)
          <input type="number" min="0" step="1" value={form.experience} onChange={changer('experience')} />
        </label>
        <label>Nom *<input value={form.nom} onChange={changer('nom')} required /></label>
        <label>Prénom<input value={form.prenom} onChange={changer('prenom')} /></label>
        <label>Email<input type="email" value={form.email} onChange={changer('email')} /></label>
        <label>Téléphone<input value={form.telephone} onChange={changer('telephone')} /></label>
        <label>Spécialité<input value={form.specialite} onChange={changer('specialite')} /></label>
        <label>Libellé affiché<input value={form.label} onChange={changer('label')}
                                     placeholder={creation ? 'Par défaut : prénom + nom' : ''} /></label>
      </div>

      {RELATIONS.map(({ cle, titre, ressource, exemple }) => {
        const autres = liensLectureSeule(formateur?.[cle])
        return (
          <div key={cle} className="champ-relation">
            <span className="etiquette">{titre}</span>
            <RelationSelect ressource={ressource} valeurs={form[cle]} placeholder={exemple}
                            onChange={(ids) => setForm({ ...form, [cle]: ids })} />
            {autres.length > 0 && (
              <p className="rs-aide">
                Aussi lié, défini par une autre partie (non modifiable ici) : {autres.map((l) => l.label).join(', ')}
              </p>
            )}
          </div>
        )
      })}
    </FormModal>
  )
}
