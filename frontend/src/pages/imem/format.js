// Constantes et petites fonctions partagées par les pages d'Imem (composants : Affichage.jsx).
export const NIVEAUX = ['Débutant', 'Intermédiaire', 'Avancé']
export const TAILLE_PAGE = 10

// Pages des autres membres déjà intégrées : un lien n'est affiché que pour celles-ci
export const ROUTES = { Formation: 'formations', Parcours: 'parcours', Formateur: 'formateurs', Organisme: 'organismes' }

export function cout(v) {
  if (v == null) return '—'
  return v === 0 ? 'Gratuit' : `${Number(v).toLocaleString('fr-FR')} DT`
}

export function date(v) {
  if (!v) return '—'
  return new Date(v).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

// "2026-11-23T00:00:00" -> "2026-11-23" pour <input type="date">
export const versInputDate = (v) => (v ? String(v).slice(0, 10) : '')

// Libellé lisible d'un nom de classe : FormationFullStack -> Formation Full Stack
export const classe = (t) => (t ? t.replace(/([a-z])([A-Z])/g, '$1 $2') : '—')

// Retire les valeurs vides (paramètres d'URL)
export function nettoyer(objet) {
  return Object.fromEntries(Object.entries(objet).filter(([, v]) => v !== '' && v !== null && v !== undefined && v !== false))
}
