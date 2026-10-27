// Formulaire de création / modification d'un organisme (fenêtre modale).
import { useState } from 'react'
import client from '../../api/client'
import FormModal from '../../components/FormModal'
import RelationSelect from '../../components/RelationSelect'
import { TYPES_ORGANISME, differences, idsModifiables, liensLectureSeule, nettoyer } from './commun'

const RELATIONS = [
  { cle: 'formations', titre: 'Formations proposées', ressource: 'formations', exemple: 'ex. Formation_FullStack' },
  { cle: 'certifications', titre: 'Certifications délivrées', ressource: 'certifications', exemple: 'ex. Certificat_Frontend' },
]

function versFormulaire(o) {
  return {
    type: o?.type ?? 'Universite',
    label: o?.label ?? '',
    formations: idsModifiables(o?.formations),
    certifications: idsModifiables(o?.certifications),
  }
}

export default function OrganismeForm({ ouvert, ...props }) {
  // Monté seulement quand il est ouvert : son état repart de zéro à chaque ouverture
  return ouvert ? <ContenuOrganismeForm {...props} /> : null
}

function ContenuOrganismeForm({ organisme, onFermer, onEnregistre }) {
  const creation = !organisme
  const [form, setForm] = useState(versFormulaire(organisme))
  const [erreur, setErreur] = useState(null)
  const [enCours, setEnCours] = useState(false)

  const valider = async () => {
    setEnCours(true)
    setErreur(null)
    try {
      const r = creation
        ? await client.post('/organismes', nettoyer(form))
        : await client.put(`/organismes/${organisme.id}`, differences(versFormulaire(organisme), form))
      onEnregistre(r.data)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setEnCours(false)
    }
  }

  return (
    <FormModal ouvert titre={creation ? 'Nouvel organisme' : `Modifier ${organisme.label}`}
               onFermer={onFermer} onValider={valider} enCours={enCours} erreur={erreur}>
      <label>Type *
        <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
          {Object.entries(TYPES_ORGANISME).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </label>
      <label>Nom (libellé) *
        <input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} required />
      </label>
      {RELATIONS.map(({ cle, titre, ressource, exemple }) => {
        const autres = liensLectureSeule(organisme?.[cle])
        return (
          <div key={cle} className="champ-relation">
            <span className="etiquette">{titre}</span>
            <RelationSelect ressource={ressource} valeurs={form[cle]} placeholder={exemple}
                            onChange={(ids) => setForm({ ...form, [cle]: ids })} />
            {autres.length > 0 && (
              <p className="rs-aide">Aussi lié, défini par une autre partie (non modifiable ici) : {autres.map((l) => l.label).join(', ')}</p>
            )}
          </div>
        )
      })}
    </FormModal>
  )
}
