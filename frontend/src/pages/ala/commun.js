// Constantes et petites fonctions partagées par les pages d'Ala.

// Types acceptés par l'API (identiques aux listes des routeurs Python) avec leur libellé
export const TYPES_FORMATEUR = {
  FormateurPermanent: 'Formateur permanent',
  FormateurSenior: 'Formateur senior',
  FormateurJunior: 'Formateur junior (≤ 3 ans)',
  FormateurVacataire: 'Formateur vacataire',
  FormateurExpertIndustrie: 'Expert de l\'industrie',
  FormateurInvite: 'Formateur invité',
}

export const TYPES_PERSONNEL = {
  ResponsableDeFormation: 'Responsable de formation',
  ResponsablePedagogique: 'Responsable pédagogique',
  AgentScolarite: 'Agent de scolarité',
  GestionnaireInscription: 'Gestionnaire des inscriptions',
}
export const EST_SCOLARITE = (type) => type === 'AgentScolarite' || type === 'GestionnaireInscription'

export const TYPES_ORGANISME = {
  Universite: 'Université',
  EcoleSuperieure: 'École supérieure',
  MOOC: 'MOOC',
  AcademieEnLigne: 'Académie en ligne',
  MinistereFormation: 'Ministère (certificateur public)',
  EditeurTechnologique: 'Éditeur technologique (certificateur privé)',
}
// Filtre seulement : classes intermédiaires (sous-classes comprises côté API)
export const FILTRES_ORGANISME = {
  OrganismeDeFormation: 'Tous les organismes de formation',
  OrganismeCertificateur: 'Tous les certificateurs',
  ...TYPES_ORGANISME,
}

export const TYPES_DOMAINE = {
  DeveloppementWeb: 'Développement web',
  DeveloppementFrontend: 'Développement front-end',
  DeveloppementBackend: 'Développement back-end',
  DeveloppementFullStack: 'Développement full-stack',
  DonneesEtIA: 'Données et IA',
  AnalyseDeDonnees: 'Analyse de données',
  ApprentissageAutomatique: 'Apprentissage automatique',
  DesignInterface: 'Design d\'interface',
  UXDesign: 'Design UX',
  UIDesign: 'Design UI',
}
export const FILTRES_DOMAINE = {
  DomaineInformatique: 'Tous les domaines informatiques',
  DomaineDesign: 'Tous les domaines du design',
  ...TYPES_DOMAINE,
}

const TOUS_LES_TYPES = {
  ...TYPES_FORMATEUR, ...TYPES_PERSONNEL, ...FILTRES_ORGANISME, ...FILTRES_DOMAINE,
  ResponsableFormation: 'Responsable', ServiceScolarite: 'Scolarité',
}
export const libelleType = (type) => TOUS_LES_TYPES[type] ?? type ?? '—'

export const TAILLE_PAGE = 10

// Retire les valeurs vides (pour les paramètres d'URL et le corps d'un POST)
export function nettoyer(objet) {
  return Object.fromEntries(Object.entries(objet).filter(([, v]) => v !== '' && v !== null && v !== undefined))
}

// Identifiants des liens écrits par moi (les seuls que le formulaire peut modifier)
export const idsModifiables = (liens = []) => liens.filter((l) => l.modifiable).map((l) => l.id)
export const liensLectureSeule = (liens = []) => liens.filter((l) => !l.modifiable)

// Champs modifiés entre la fiche d'origine et le formulaire (pour un PUT partiel).
// "" devient null (= effacer la valeur côté API).
export function differences(initial, courant) {
  const modifs = {}
  for (const [cle, valeur] of Object.entries(courant)) {
    const avant = initial?.[cle]
    if (Array.isArray(valeur)) {
      const a = [...(avant ?? [])].sort().join('|')
      const b = [...valeur].sort().join('|')
      if (a !== b) modifs[cle] = valeur
    } else if ((valeur ?? '') !== (avant ?? '')) {
      modifs[cle] = valeur === '' ? null : valeur
    }
  }
  return modifs
}
